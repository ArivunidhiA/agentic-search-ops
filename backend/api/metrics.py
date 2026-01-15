"""Metrics API endpoints."""

import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from db.database import get_db
from models.document import Document
from models.chunk import Chunk
from models.job import Job, JobStatus, JobEvent
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix=settings.API_V1_PREFIX, tags=["metrics"])


class SystemHealth(str):
    """System health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"


class MetricsResponse(BaseModel):
    """Response model for system metrics."""
    total_documents: int
    total_chunks: int
    jobs_by_status: dict
    storage_used_bytes: int
    recent_activity: List[dict]
    system_health: str


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get system metrics.
    
    Returns:
    - Total documents count
    - Total chunks count
    - Jobs by status
    - Storage used (bytes)
    - Recent activity (last 10 events)
    - System health status
    """
    try:
        # Get document count
        doc_count_result = await db.execute(
            select(func.count(Document.id))
        )
        total_documents = doc_count_result.scalar() or 0
        
        # Get chunk count
        chunk_count_result = await db.execute(
            select(func.count(Chunk.id))
        )
        total_chunks = chunk_count_result.scalar() or 0
        
        # Get jobs by status
        jobs_by_status = {}
        for status_enum in JobStatus:
            count_result = await db.execute(
                select(func.count(Job.id)).where(Job.status == status_enum)
            )
            jobs_by_status[status_enum.value] = count_result.scalar() or 0
        
        # Calculate storage used (approximate)
        # For local storage, sum file sizes from documents
        # For S3, this would require listing objects (expensive), so we approximate
        storage_used = 0
        if not settings.S3_BUCKET_NAME:
            # Local storage: sum document file sizes
            size_result = await db.execute(
                select(func.sum(Document.file_size))
            )
            storage_used = size_result.scalar() or 0
        else:
            # S3: approximate from document sizes (not exact due to chunking overhead)
            size_result = await db.execute(
                select(func.sum(Document.file_size))
            )
            storage_used = size_result.scalar() or 0
        
        # Get recent activity (last 10 events)
        recent_activity = []
        try:
            recent_events_result = await db.execute(
                select(JobEvent)
                .order_by(JobEvent.timestamp.desc())
                .limit(10)
            )
            recent_events = recent_events_result.scalars().all()
            
            recent_activity = [
                {
                    "id": str(event.id),
                    "job_id": str(event.job_id),
                    "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                    "timestamp": event.timestamp.isoformat() if event.timestamp else datetime.utcnow().isoformat()
                }
                for event in recent_events
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch recent events: {str(e)}")
            recent_activity = []
        
        # Determine system health
        # Healthy: no failed jobs in recent activity, storage accessible
        # Degraded: failed jobs or storage issues
        system_health = SystemHealth.HEALTHY
        failed_jobs_count = jobs_by_status.get(JobStatus.FAILED.value, 0)
        if failed_jobs_count > 10:  # Threshold for degraded
            system_health = SystemHealth.DEGRADED
        
        return MetricsResponse(
            total_documents=total_documents,
            total_chunks=total_chunks,
            jobs_by_status=jobs_by_status,
            storage_used_bytes=storage_used,
            recent_activity=recent_activity,
            system_health=system_health
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )
