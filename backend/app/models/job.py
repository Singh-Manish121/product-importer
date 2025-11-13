"""Job model for tracking CSV import jobs."""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func, Enum
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base


class JobStatus(str, PyEnum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    """Job model for tracking CSV import tasks."""
    
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True)  # UUID for external reference
    status = Column(String(20), default=JobStatus.PENDING, nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    created_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)  # Current processing step: "parsing", "validating", "importing"
    progress_percentage = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    errors = Column(JSON, default=list, nullable=True)  # List of row errors
    celery_task_id = Column(String(100), nullable=True, index=True)  # Celery task ID for tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Job(id={self.id}, job_id={self.job_id}, status={self.status}, progress={self.progress_percentage}%)>"
