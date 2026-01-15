"""Upload API endpoints."""

import logging
import asyncio
from uuid import uuid4
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from db.database import get_db
from models.document import Document, DocumentStatus
from core.storage import storage_service
from core.config import settings
from core.security import (
    validate_filename,
    validate_file_size,
    validate_content_type
)
from services.ingest import ingest_document
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix=settings.API_V1_PREFIX, tags=["upload"])


class DocumentResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    filename: str
    status: str
    upload_timestamp: str
    file_size: int


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[dict]
    total: int
    skip: int
    limit: int


class DocumentDetailResponse(BaseModel):
    """Response model for document details."""
    id: str
    filename: str
    s3_key: str
    upload_timestamp: str
    file_size: int
    content_type: str
    status: str
    metadata: dict
    chunk_count: int
    download_url: Optional[str] = None


class DeleteResponse(BaseModel):
    """Response model for document deletion."""
    deleted: bool
    document_id: str


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document file.
    
    Validates filename, size, and content type.
    Uploads to storage and creates Document record.
    Triggers async ingestion task.
    Rate limit: 10 uploads per minute per IP (enforced by middleware).
    """
    # Rate limiting is handled by SlowAPIMiddleware with default limit
    # For production, configure per-endpoint limits in middleware config
    try:
        # Validate filename
        safe_filename = validate_filename(file.filename or "unnamed")
        
        # Read file to get size
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        validate_file_size(file_size, settings.MAX_UPLOAD_SIZE)
        
        # Validate content type
        content_type = file.content_type or "application/octet-stream"
        validate_content_type(content_type, settings.ALLOWED_CONTENT_TYPES)
        
        # Reset file pointer
        await file.seek(0)
        
        # Generate document ID and S3 key
        document_id = str(uuid4())
        s3_key = f"documents/{document_id}/{safe_filename}"
        
        # Upload to storage
        logger.info(f"Uploading file {safe_filename} to storage as {s3_key}")
        await storage_service.upload_file(file, s3_key)
        
        # Create document record
        document = Document(
            id=document_id,
            filename=safe_filename,
            s3_key=s3_key,
            file_size=file_size,
            content_type=content_type,
            status=DocumentStatus.PENDING,
            metadata_json={}
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Trigger async ingestion (fire and forget)
        # Create new session for background task
        from db.database import AsyncSessionLocal
        async def background_ingest():
            async with AsyncSessionLocal() as bg_db:
                await ingest_document(document_id, bg_db)
        asyncio.create_task(background_ingest())
        
        return DocumentResponse(
            document_id=document.id,
            filename=document.filename,
            status=document.status.value,
            upload_timestamp=document.upload_timestamp.isoformat(),
            file_size=document.file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List documents with pagination.
    
    Query params:
    - skip: Number of documents to skip
    - limit: Maximum number of documents to return (1-100)
    - status: Filter by status (pending, processing, completed, failed)
    """
    try:
        # Build query
        query = select(Document)
        
        if status_filter:
            try:
                status_enum = DocumentStatus(status_filter.lower())
                query = query.where(Document.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(Document.upload_timestamp.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Format response
        document_list = [
            {
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status.value,
                "upload_timestamp": doc.upload_timestamp.isoformat() if doc.upload_timestamp else None,
                "file_size": doc.file_size
            }
            for doc in documents
        ]
        
        return DocumentListResponse(
            documents=document_list,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get document details by ID.
    
    Includes presigned download URL if status is completed.
    """
    try:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get chunk count
        from models.chunk import Chunk
        chunk_count_result = await db.execute(
            select(func.count(Chunk.id)).where(Chunk.document_id == document_id)
        )
        chunk_count = chunk_count_result.scalar() or 0
        
        # Generate presigned URL if document is completed
        download_url = None
        if document.status == DocumentStatus.COMPLETED:
            download_url = await storage_service.get_presigned_url(document.s3_key, expiry_hours=1)
        
        return DocumentDetailResponse(
            id=document.id,
            filename=document.filename,
            s3_key=document.s3_key,
            upload_timestamp=document.upload_timestamp.isoformat() if document.upload_timestamp else "",
            file_size=document.file_size,
            content_type=document.content_type,
            status=document.status.value,
            metadata=document.metadata_json or {},
            chunk_count=chunk_count,
            download_url=download_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and all its chunks.
    
    Deletes from storage and database (cascade).
    """
    try:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete from storage
        await storage_service.delete_file(document.s3_key)
        
        # Delete from database (cascade will delete chunks)
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Deleted document {document_id}")
        
        return DeleteResponse(
            deleted=True,
            document_id=document_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )
