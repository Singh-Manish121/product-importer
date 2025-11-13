"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    sku: str = Field(..., min_length=1, max_length=255, description="Product SKU")
    name: str = Field(..., min_length=1, max_length=500, description="Product name")
    description: Optional[str] = Field(None, description="Product description")

    class Config:
        json_schema_extra = {
            "example": {
                "sku": "PROD-001",
                "name": "Widget A",
                "description": "High-quality widget",
            }
        }


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Widget A Updated",
                "description": "Improved description",
            }
        }


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    sku: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "sku": "PROD-001",
                "name": "Widget A",
                "description": "High-quality widget",
                "created_at": "2025-11-13T20:51:03.123456",
                "updated_at": "2025-11-13T20:51:03.123456",
            }
        }


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class FilterParams(BaseModel):
    """Schema for filter parameters."""
    sku: Optional[str] = Field(None, description="Filter by SKU (partial match)")
    name: Optional[str] = Field(None, description="Filter by name (partial match)")
    description: Optional[str] = Field(None, description="Filter by description (partial match)")


class ProductListResponse(BaseModel):
    """Schema for product list response."""
    total: int = Field(..., description="Total number of products matching filters")
    limit: int = Field(..., description="Limit used in query")
    offset: int = Field(..., description="Offset used in query")
    items: List[ProductResponse] = Field(..., description="List of products")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "limit": 10,
                "offset": 0,
                "items": [
                    {
                        "id": 1,
                        "sku": "PROD-001",
                        "name": "Widget A",
                        "description": "High-quality widget",
                        "created_at": "2025-11-13T20:51:03.123456",
                        "updated_at": "2025-11-13T20:51:03.123456",
                    }
                ],
            }
        }
