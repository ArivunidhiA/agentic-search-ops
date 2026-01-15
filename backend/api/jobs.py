"""Jobs API endpoints for agentic workflows."""

import logging
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from db.database import get_db
from models.job import Job, JobStatus, JobType, JobEvent, JobEventType, JobState
from core.config import settings
from core.security import validate_job_config
from services.agent import run_agent_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix=settings.API_V1_PREFIX, tags=["jobs"])


class JobCreateRequest(BaseModel):
    """Request model for creating a job."""
    job_type: str = Field(..., description="Job type: ingestion, search, synthesis, refresh")
    config: dict = Field(default_factory=dict, description="Job configuration parameters")


class JobResponse(BaseModel):
    """Response model for job."""
    id: str
    job_type: str
    status: str
    config: dict
    result: dict
    error_message: Optional[str]
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    retry_count: int
    max_retries: int


class JobListResponse(BaseModel):
    """Response model for job list."""
    jobs: List[dict]
    total: int
    skip: int
    limit: int


class JobDetailResponse(BaseModel):
    """Response model for job details."""
    id: str
    job_type: str
    status: str
    config: dict
    result: dict
    error_message: Optional[str]
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    retry_count: int
    max_retries: int
    latest_checkpoint: Optional[dict]
    event_count: int


class JobControlRequest(BaseModel):
    """Request model for job control."""
    action: str = Field(..., description="Action: pause, resume, or stop")


class JobControlResponse(BaseModel):
    """Response model for job control."""
    job_id: str
    status: str
    message: str


class CheckpointRequest(BaseModel):
    """Request model for creating a checkpoint."""
    state_data: dict = Field(..., description="Checkpoint state data")
    step_name: str = Field(..., min_length=1, max_length=100, description="Step name")


class CheckpointResponse(BaseModel):
    """Response model for checkpoint."""
    checkpoint_id: str
    timestamp: str


class JobEventResponse(BaseModel):
    """Response model for job event."""
    id: str
    event_type: str
    event_data: dict
    timestamp: str


class JobEventListResponse(BaseModel):
    """Response model for job event list."""
    events: List[JobEventResponse]
    total: int
    skip: int
    limit: int


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job.
    
    Validates job_type and config, then creates Job record.
    """
    try:
        # Validate job type
        try:
            job_type_enum = JobType(request.job_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job type: {request.job_type}. Must be one of: {[t.value for t in JobType]}"
            )
        
        # Validate and sanitize config
        sanitized_config = validate_job_config(
            request.config,
            settings.MAX_JOB_RUNTIME_MINUTES,
            settings.MAX_JOB_COST_USD
        )
        
        # Create job
        job = Job(
            job_type=job_type_enum,
            status=JobStatus.PENDING,
            config=sanitized_config,
            result={}
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        # Trigger async job execution (fire and forget)
        # Create new session for background task
        from db.database import AsyncSessionLocal
        async def background_job():
            async with AsyncSessionLocal() as bg_db:
                await run_agent_job(job.id, bg_db)
        asyncio.create_task(background_job())
        
        return JobResponse(
            id=job.id,
            job_type=job.job_type.value,
            status=job.status.value,
            config=job.config,
            result=job.result,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            retry_count=job.retry_count,
            max_retries=job.max_retries
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List jobs with pagination.
    
    Query params:
    - skip: Number of jobs to skip
    - limit: Maximum number of jobs to return (1-100)
    - status: Filter by status (pending, running, paused, completed, failed)
    """
    try:
        # Build query
        query = select(Job)
        
        if status_filter:
            try:
                status_enum = JobStatus(status_filter.lower())
                query = query.where(Job.status == status_enum)
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
        query = query.order_by(Job.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        # Format response
        job_list = [
            {
                "id": job.id,
                "job_type": job.job_type.value,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ]
        
        return JobListResponse(
            jobs=job_list,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get job details by ID.
    
    Includes latest checkpoint and event count.
    """
    try:
        result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get latest checkpoint
        checkpoint_result = await db.execute(
            select(JobState)
            .where(JobState.job_id == job_id)
            .order_by(JobState.checkpoint_timestamp.desc())
            .limit(1)
        )
        latest_checkpoint = checkpoint_result.scalar_one_or_none()
        
        # Get event count
        event_count_result = await db.execute(
            select(func.count(JobEvent.id)).where(JobEvent.job_id == job_id)
        )
        event_count = event_count_result.scalar() or 0
        
        return JobDetailResponse(
            id=job.id,
            job_type=job.job_type.value,
            status=job.status.value,
            config=job.config,
            result=job.result,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            retry_count=job.retry_count,
            max_retries=job.max_retries,
            latest_checkpoint={
                "id": latest_checkpoint.id,
                "step_name": latest_checkpoint.step_name,
                "state_data": latest_checkpoint.state_data,
                "checkpoint_timestamp": latest_checkpoint.checkpoint_timestamp.isoformat()
            } if latest_checkpoint else None,
            event_count=event_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
        )


@router.get("/jobs/{job_id}/events", response_model=JobEventListResponse)
async def get_job_events(
    job_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job events with pagination.
    
    Returns events ordered by timestamp (descending).
    """
    try:
        # Verify job exists
        job_result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        if not job_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get total count
        count_result = await db.execute(
            select(func.count(JobEvent.id)).where(JobEvent.job_id == job_id)
        )
        total = count_result.scalar() or 0
        
        # Get paginated events
        events_result = await db.execute(
            select(JobEvent)
            .where(JobEvent.job_id == job_id)
            .order_by(JobEvent.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        events = events_result.scalars().all()
        
        # Format response
        event_list = [
            JobEventResponse(
                id=event.id,
                event_type=event.event_type.value,
                event_data=event.event_data,
                timestamp=event.timestamp.isoformat()
            )
            for event in events
        ]
        
        return JobEventListResponse(
            events=event_list,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get events for job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job events"
        )


@router.post("/jobs/{job_id}/control", response_model=JobControlResponse)
async def control_job(
    job_id: str,
    request: JobControlRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Control job execution (pause, resume, stop).
    
    Updates job status and creates corresponding event.
    """
    try:
        result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        action = request.action.lower()
        
        if action == "pause":
            if job.status != JobStatus.RUNNING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot pause job with status: {job.status.value}"
                )
            job.status = JobStatus.PAUSED
            event_type = JobEventType.PAUSE
            message = "Job paused"
            
        elif action == "resume":
            if job.status != JobStatus.PAUSED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot resume job with status: {job.status.value}"
                )
            job.status = JobStatus.RUNNING
            event_type = JobEventType.RESUME
            message = "Job resumed"
            # Trigger job execution again
            from db.database import AsyncSessionLocal
            async def background_job():
                async with AsyncSessionLocal() as bg_db:
                    await run_agent_job(job_id, bg_db)
            asyncio.create_task(background_job())
            
        elif action == "stop":
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot stop job with status: {job.status.value}"
                )
            job.status = JobStatus.FAILED
            job.error_message = "Job stopped by operator"
            event_type = JobEventType.ERROR
            message = "Job stopped"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}. Must be one of: pause, resume, stop"
            )
        
        # Create event
        event = JobEvent(
            job_id=job_id,
            event_type=event_type,
            event_data={"action": action}
        )
        db.add(event)
        await db.commit()
        
        return JobControlResponse(
            job_id=job_id,
            status=job.status.value,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to control job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to control job"
        )


@router.post("/jobs/{job_id}/checkpoint", response_model=CheckpointResponse)
async def create_checkpoint(
    job_id: str,
    request: CheckpointRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a checkpoint for a job.
    
    Saves state data and creates checkpoint event.
    """
    try:
        # Verify job exists
        job_result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Create checkpoint
        checkpoint = JobState(
            job_id=job_id,
            state_data=request.state_data,
            step_name=request.step_name
        )
        db.add(checkpoint)
        
        # Create checkpoint event
        event = JobEvent(
            job_id=job_id,
            event_type=JobEventType.CHECKPOINT,
            event_data={"step_name": request.step_name}
        )
        db.add(event)
        await db.commit()
        await db.refresh(checkpoint)
        
        return CheckpointResponse(
            checkpoint_id=checkpoint.id,
            timestamp=checkpoint.checkpoint_timestamp.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkpoint for job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkpoint"
        )
