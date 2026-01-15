"""Document model for the Knowledge Base."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from db.database import Base


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """Document model representing uploaded files."""
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    filename = Column(String(255), nullable=False, index=True)
    s3_key = Column(String(512), nullable=False, unique=True, index=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False, index=True)
    metadata_json = Column("metadata", JSON, default=dict)  # Renamed to avoid SQLAlchemy reserved name
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
