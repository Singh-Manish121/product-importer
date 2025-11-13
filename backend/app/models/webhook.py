"""Webhook model for managing webhooks."""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, func
from datetime import datetime
from app.database import Base


class Webhook(Base):
    """Webhook model for storing webhook configurations."""
    
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)  # Webhook URL
    event_types = Column(JSON, default=list, nullable=False)  # List of event types: ['product.created', 'product.updated', 'product.deleted']
    enabled = Column(Boolean, default=True, index=True)
    last_triggered_at = Column(DateTime, nullable=True)
    last_response_status = Column(Integer, nullable=True)  # HTTP status code from last delivery
    last_response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    last_error = Column(Text, nullable=True)  # Last error message
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Webhook(id={self.id}, url={self.url}, enabled={self.enabled}, events={self.event_types})>"
