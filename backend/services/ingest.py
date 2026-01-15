"""Document ingestion service."""

import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.document import Document, DocumentStatus
from models.chunk import Chunk
from core.storage import storage_service
from core.config import settings

logger = logging.getLogger(__name__)


async def extract_text(file_bytes: bytes, content_type: str) -> str:
    """
    Extract text from file bytes based on content type.
    
    Args:
        file_bytes: File content as bytes
        content_type: MIME type of the file
        
    Returns:
        Extracted text content
    """
    content_type_lower = content_type.lower()
    
    if content_type_lower in ["text/plain", "text/markdown"]:
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Try with error handling
            return file_bytes.decode('utf-8', errors='replace')
    
    elif content_type_lower == "application/pdf":
        # Stub: PDF extraction not implemented
        logger.warning("PDF extraction not implemented, returning placeholder")
        return "[PDF extraction not implemented]"
    
    elif "wordprocessingml" in content_type_lower or content_type_lower.endswith("msword"):
        # Stub: DOCX extraction not implemented
        logger.warning("DOCX extraction not implemented, returning placeholder")
        return "[DOCX extraction not implemented]"
    
    else:
        # Fallback: try to decode as text
        try:
            return file_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to extract text from {content_type}: {str(e)}")
            return ""


async def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Chunk text using sliding window approach.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text or chunk_size <= 0:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
        
        # Move start position forward by (chunk_size - overlap)
        start += chunk_size - overlap
        
        # Prevent infinite loop if overlap >= chunk_size
        if overlap >= chunk_size:
            break
    
    return chunks


async def ingest_document(document_id: str, db: AsyncSession) -> None:
    """
    Ingest a document: download, extract text, chunk, and store chunks.
    
    Args:
        document_id: UUID of the document to ingest
        db: Database session
    """
    try:
        # Load document from database
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        # Update status to processing
        document.status = DocumentStatus.PROCESSING
        await db.commit()
        
        # Download file from storage
        logger.info(f"Downloading document {document_id} from storage")
        file_bytes = await storage_service.download_file(document.s3_key)
        
        # Extract text
        logger.info(f"Extracting text from document {document_id}")
        text = await extract_text(file_bytes, document.content_type)
        
        if not text or text.strip() == "":
            raise ValueError("No text content extracted from document")
        
        # Chunk text
        logger.info(f"Chunking text for document {document_id}")
        text_chunks = await chunk_text(
            text,
            settings.CHUNK_SIZE,
            settings.CHUNK_OVERLAP
        )
        
        if not text_chunks:
            raise ValueError("No chunks created from document text")
        
        # Create chunk records
        logger.info(f"Creating {len(text_chunks)} chunks for document {document_id}")
        chunk_objects = []
        for idx, chunk_content in enumerate(text_chunks):
            chunk = Chunk(
                document_id=document_id,
                content=chunk_content,
                chunk_index=idx,
                token_count=len(chunk_content.split())  # Simple word count as token estimate
            )
            chunk_objects.append(chunk)
        
        db.add_all(chunk_objects)
        
        # Update document status to completed
        document.status = DocumentStatus.COMPLETED
        await db.commit()
        
        logger.info(f"Successfully ingested document {document_id} with {len(text_chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Failed to ingest document {document_id}: {str(e)}", exc_info=True)
        
        # Update document status to failed
        try:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            if document:
                document.status = DocumentStatus.FAILED
                # Store error message in metadata
                if not document.metadata_json:
                    document.metadata_json = {}
                document.metadata_json['error'] = str(e)
                await db.commit()
        except Exception as commit_error:
            logger.error(f"Failed to update document status: {str(commit_error)}")
        
        raise
