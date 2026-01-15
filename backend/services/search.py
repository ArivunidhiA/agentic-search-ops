"""Search service for querying document chunks."""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from models.chunk import Chunk
from models.document import Document
from core.security import sanitize_search_query
from core.config import settings

logger = logging.getLogger(__name__)


async def search_chunks(
    query: str,
    limit: int,
    document_ids: Optional[List[str]],
    db: AsyncSession
) -> List[dict]:
    """
    Search through document chunks using keyword matching.
    
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


async def semantic_search_chunks(
    query: str,
    limit: int,
    document_ids: Optional[List[str]],
    db: AsyncSession
) -> List[dict]:
    """
    Search through document chunks using semantic similarity.
    
    Uses vector embeddings and cosine similarity to find
    semantically similar content, even if exact keywords don't match.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        document_ids: Optional list of document IDs to filter by
        db: Database session
        
    Returns:
        List of dictionaries with chunk, document, and similarity score
    """
    if not settings.ENABLE_EMBEDDINGS:
        logger.warning("Semantic search requested but embeddings are disabled")
        # Fall back to keyword search
        return await search_chunks(query, limit, document_ids, db)
    
    try:
        from services.embeddings import embedding_service
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query)
        
        if query_embedding is None:
            logger.warning("Failed to generate query embedding, falling back to keyword search")
            return await search_chunks(query, limit, document_ids, db)
        
        # Build query to get chunks with embeddings
        base_query = select(
            Chunk,
            Document
        ).join(
            Document, Chunk.document_id == Document.id
        ).where(
            Chunk.embedding.isnot(None)
        )
        
        # Filter by document_ids if provided
        if document_ids:
            base_query = base_query.where(Document.id.in_(document_ids))
        
        # Execute query to get all chunks with embeddings
        result = await db.execute(base_query)
        rows = result.all()
        
        if not rows:
            logger.warning("No chunks with embeddings found, falling back to keyword search")
            return await search_chunks(query, limit, document_ids, db)
        
        # Calculate similarity scores
        scored_results = []
        for chunk, document in rows:
            chunk_embedding = embedding_service.json_to_embedding(chunk.embedding)
            
            if chunk_embedding is None:
                continue
            
            # Calculate cosine similarity
            similarity = embedding_service.cosine_similarity(
                query_embedding,
                chunk_embedding
            )
            
            # Filter by threshold
            if similarity >= settings.EMBEDDING_SIMILARITY_THRESHOLD:
                scored_results.append({
                    "chunk": chunk,
                    "document": document,
                    "similarity": similarity
                })
        
        # Sort by similarity (descending) and limit
        scored_results.sort(key=lambda x: x["similarity"], reverse=True)
        scored_results = scored_results[:limit]
        
        # Format results
        results = []
        for item in scored_results:
            chunk = item["chunk"]
            document = item["document"]
            similarity = item["similarity"]
            
            results.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "highlighted_content": chunk.content,  # No keyword highlighting for semantic
                "score": round(similarity, 4),
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
        
        logger.info(f"Semantic search '{query}' returned {len(results)} results")
        return results
        
    except ImportError:
        logger.error("Embedding service not available, falling back to keyword search")
        return await search_chunks(query, limit, document_ids, db)
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        # Fall back to keyword search on error
        return await search_chunks(query, limit, document_ids, db)
