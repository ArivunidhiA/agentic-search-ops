"""Search service for querying document chunks."""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from models.chunk import Chunk
from models.document import Document
from core.security import sanitize_search_query

logger = logging.getLogger(__name__)


async def search_chunks(
    query: str,
    limit: int,
    document_ids: Optional[List[str]],
    db: AsyncSession
) -> List[dict]:
    """
    Search through document chunks.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        document_ids: Optional list of document IDs to filter by
        db: Database session
        
    Returns:
        List of dictionaries with chunk, document, and score information
    """
    # Sanitize query
    sanitized_query = sanitize_search_query(query)
    
    if not sanitized_query:
        return []
    
    # Build query
    # Simple case-insensitive text search
    search_term = f"%{sanitized_query.lower()}%"
    query_lower = sanitized_query.lower()
    
    # Base query: join chunks with documents
    # Calculate score as number of occurrences (simplified)
    base_query = select(
        Chunk,
        Document
    ).join(
        Document, Chunk.document_id == Document.id
    ).where(
        func.lower(Chunk.content).like(search_term)
    )
    
    # Filter by document_ids if provided
    if document_ids:
        base_query = base_query.where(Document.id.in_(document_ids))
    
    # Order by content length (simpler heuristic for now)
    # In production, this would use proper text ranking
    base_query = base_query.order_by(
        func.length(Chunk.content).desc()
    ).limit(limit)
    
    # Execute query
    result = await db.execute(base_query)
    rows = result.all()
    
    # Format results
    results = []
    for chunk, document in rows:
        # Calculate actual score (number of occurrences)
        content_lower = chunk.content.lower()
        query_lower = sanitized_query.lower()
        occurrence_count = content_lower.count(query_lower)
        
        # Highlight matched terms (simple: wrap in ** for markdown)
        highlighted_content = chunk.content
        if query_lower in content_lower:
            # Simple highlighting: wrap query term
            highlighted_content = chunk.content.replace(
                query_lower,
                f"**{query_lower}**"
            )
        
        results.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "content": chunk.content,
            "highlighted_content": highlighted_content,
            "score": occurrence_count,
            "chunk_index": chunk.chunk_index,
            "document_metadata": {
                "id": document.id,
                "filename": document.filename,
                "status": document.status.value,
                "upload_timestamp": document.upload_timestamp.isoformat() if document.upload_timestamp else None,
                "file_size": document.file_size,
                "content_type": document.content_type
            }
        })
    
    logger.info(f"Search query '{sanitized_query}' returned {len(results)} results")
    return results
