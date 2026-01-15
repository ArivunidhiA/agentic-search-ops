"""Job, JobState, and JobEvent models for agentic workflows."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
import enum

from db.database import Base


class JobType(str, enum.Enum):
    """Job type enumeration."""
    INGESTION = "ingestion"
    SEARCH = "search"
    SUMMARIZATION = "summarization"
    DEEP_SEARCH = "deep_search"
    SYNTHESIS = "synthesis"
    REFRESH = "refresh"


class JobStatus(str, enum.Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class JobEventType(str, enum.Enum):
    """Job event type enumeration."""
    START = "start"
    CHECKPOINT = "checkpoint"
    ERROR = "error"
    RETRY = "retry"
    COMPLETE = "complete"
    PAUSE = "pause"
    RESUME = "resume"


class Job(Base):
    """Job model for agentic workflow execution."""
    
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    config = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Relationships
    states = relationship("JobState", back_populates="job", cascade="all, delete-orphan", order_by="JobState.checkpoint_timestamp.desc()")
    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan", order_by="JobEvent.timestamp.desc()")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_status_type', 'status', 'job_type'),
        Index('idx_job_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"


class JobState(Base):
    """JobState model for checkpointing job progress."""
    
    __tablename__ = "job_states"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    state_data = Column(JSON, nullable=False)
    checkpoint_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    
    # Relationships
    job = relationship("Job", back_populates="states")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_state_timestamp', 'job_id', 'checkpoint_timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<JobState(id={self.id}, job_id={self.job_id}, step={self.step_name})>"


class JobEvent(Base):
    """JobEvent model for job event logging."""
    
    __tablename__ = "job_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(SQLEnum(JobEventType), nullable=False, index=True)
    event_data = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    job = relationship("Job", back_populates="events")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_event_timestamp', 'job_id', 'timestamp'),
        Index('idx_job_event_type', 'job_id', 'event_type'),
    )
    
    def __repr__(self) -> str:
        return f"<JobEvent(id={self.id}, job_id={self.job_id}, type={self.event_type})>"
