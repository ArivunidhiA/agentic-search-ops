"""Search API endpoints."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db.database import get_db
from core.config import settings
from services.search import search_chunks
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix=settings.API_V1_PREFIX, tags=["search"])


class SearchRequest(BaseModel):
    """Request model for search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to filter by")


class SearchResult(BaseModel):
    """Search result item."""
    chunk_id: str
    document_id: str
    content: str
    highlighted_content: str
    score: int
    chunk_index: int
    document_metadata: dict


class SearchResponse(BaseModel):
    """Response model for search."""
    results: List[SearchResult]
    query: str
    total_results: int


@router.post("/search", response_model=SearchResponse)
async def search(
    request: Request,
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Search through document chunks.
    
    Performs text search across all chunks (or filtered by document_ids).
    Returns results with relevance scores and highlighted matches.
    Rate limit: 30 requests per minute per IP (enforced by middleware).
    """
    # Rate limiting is handled by SlowAPIMiddleware with default limit
    # For production, configure per-endpoint limits in middleware config
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
            total_results=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )
