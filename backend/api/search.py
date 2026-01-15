"""Search API endpoints."""

import logging
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db.database import get_db
from core.config import settings
from services.search import search_chunks, semantic_search_chunks
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix=settings.API_V1_PREFIX, tags=["search"])


class SearchRequest(BaseModel):
    """Request model for keyword search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to filter by")


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to filter by")


class SearchResult(BaseModel):
    """Search result item."""
    chunk_id: str
    document_id: str
    content: str
    highlighted_content: str
    score: Union[int, float]  # int for keyword search, float for semantic
    chunk_index: int
    document_metadata: dict


class SearchResponse(BaseModel):
    """Response model for search."""
    results: List[SearchResult]
    query: str
    total_results: int
    search_type: str = "keyword"


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    results: List[SearchResult]
    query: str
    total_results: int
    search_type: str = "semantic"
    embeddings_enabled: bool


@router.post("/search", response_model=SearchResponse)
async def search(
    request: Request,
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search through document chunks using keyword matching.
    
    Performs text search across all chunks (or filtered by document_ids).
    Returns results with relevance scores and highlighted matches.
    Rate limit: 30 requests per minute per IP (enforced by middleware).
    """
    try:
        results = await search_chunks(
            query=search_request.query,
            limit=search_request.limit,
            document_ids=search_request.document_ids,
            db=db
        )
        
        # Convert to response models
        search_results = [
            SearchResult(**result)
            for result in results
        ]
        
        return SearchResponse(
            results=search_results,
            query=search_request.query,
            total_results=len(search_results),
            search_type="keyword"
        )
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.post("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    request: Request,
    search_request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search through document chunks using semantic similarity.
    
    Uses vector embeddings and cosine similarity to find semantically
    similar content, even if exact keywords don't match.
    
    Requires ENABLE_EMBEDDINGS=true in configuration.
    Falls back to keyword search if embeddings are disabled.
    
    Rate limit: 30 requests per minute per IP (enforced by middleware).
    """
    try:
        results = await semantic_search_chunks(
            query=search_request.query,
            limit=search_request.limit,
            document_ids=search_request.document_ids,
            db=db
        )
        
        # Convert to response models
        search_results = [
            SearchResult(**result)
            for result in results
        ]
        
        return SemanticSearchResponse(
            results=search_results,
            query=search_request.query,
            total_results=len(search_results),
            search_type="semantic" if settings.ENABLE_EMBEDDINGS else "keyword",
            embeddings_enabled=settings.ENABLE_EMBEDDINGS
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Semantic search operation failed"
        )


@router.get("/search/status")
async def search_status():
    """
    Get search capabilities status.
    
    Returns information about available search features and their configuration.
    """
    return {
        "keyword_search": True,
        "semantic_search_enabled": settings.ENABLE_EMBEDDINGS,
        "embedding_model": settings.EMBEDDING_MODEL if settings.ENABLE_EMBEDDINGS else None,
        "similarity_threshold": settings.EMBEDDING_SIMILARITY_THRESHOLD if settings.ENABLE_EMBEDDINGS else None,
        "pdf_extraction_enabled": settings.ENABLE_PDF_EXTRACTION,
        "docx_extraction_enabled": settings.ENABLE_DOCX_EXTRACTION
    }
