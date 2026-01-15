"""Chunk model for document text chunks."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from db.database import Base


class Chunk(Base):
    """Chunk model representing text chunks from documents."""
    
    __tablename__ = "chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=True)
    embedding = Column(Text, nullable=True)  # JSON string for now, Vector type for future
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_document_chunk', 'document_id', 'chunk_index'),
    )
    
    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
