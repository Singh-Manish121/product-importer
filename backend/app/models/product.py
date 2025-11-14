"""Product model for CSV import.

Now constrained to exactly the required fields: sku, name, description.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime
from app.database import Base


class Product(Base):
    """Product model for storing product information.

    Fields:
    - id: primary key
    - sku: original SKU (preserved case)
    - sku_norm: lowercase normalized SKU for uniqueness checks
    - name: product name
    - description: product description
    - created_at/updated_at timestamps
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(255), nullable=False)
    sku_norm = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # sku_norm is unique; don't create a duplicate index (unique=True already creates one)

    def __repr__(self):
        return f"<Product(id={self.id}, sku={self.sku}, name={self.name})>"
