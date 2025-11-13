"""Product model for CSV import."""
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, Index, func
from datetime import datetime
from app.database import Base


class Product(Base):
    """Product model for storing product information."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(255), nullable=False, unique=False)  # Original SKU
    sku_norm = Column(String(255), nullable=False, unique=True, index=True)  # Normalized (lowercase) SKU
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)  # Price in dollars
    active = Column(Boolean, default=True, index=True)  # Active/Inactive status
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Index for filtering by multiple columns
    __table_args__ = (
        Index('ix_products_sku_norm_active', 'sku_norm', 'active'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku={self.sku}, name={self.name}, active={self.active})>"
