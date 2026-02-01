"""
ConversionJob model for tracking PDF to EPUB conversions
"""
from sqlalchemy import Column, String, Integer, Enum, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
import uuid

from app.models.base import Base, TimestampMixin


class JobStatus(str, enum.Enum):
    """Enum for job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConversionJob(Base, TimestampMixin):
    """ConversionJob model"""
    
    __tablename__ = "conversion_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User relationship (optional for MVP, required in Phase 2)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="conversion_jobs")
    
    # File information
    file_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    
    # Job status
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    
    # Processing parameters
    start_page = Column(Integer, nullable=True)
    max_pages = Column(Integer, nullable=True)
    languages = Column(String(100), default="English", nullable=False)
    batch_multiplier = Column(Integer, default=2, nullable=False)
    
    # Output information
    epub_filename = Column(String(255), nullable=True)
    epub_size = Column(Integer, nullable=True)  # in bytes
    
    # Processing details
    pages_processed = Column(Integer, default=0, nullable=False)
    processing_time = Column(Integer, nullable=True)  # in seconds
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Metadata (using job_metadata to avoid SQLAlchemy reserved name)
    job_metadata = Column(JSONB, nullable=True)  # Store extracted metadata from PDF
    
    # Send to Kindle
    sent_to_kindle = Column(Boolean, default=False, nullable=False)
    kindle_email = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<ConversionJob {self.id} ({self.status})>"
