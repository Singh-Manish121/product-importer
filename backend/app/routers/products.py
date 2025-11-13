"""Product CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional
from decimal import Decimal

from app.database import get_db
from app.models import Product
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
)
from app.tasks import schedule_webhook_event

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    sku: Optional[str] = Query(None, description="Filter by SKU (partial match)"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    description: Optional[str] = Query(None, description="Filter by description (partial match)"),
    db: Session = Depends(get_db),
):
    """
    List products with pagination and filtering.
    
    **Query Parameters:**
    - `limit`: Number of items per page (default: 10, max: 100)
    - `offset`: Number of items to skip (default: 0)
    - `sku`: Filter by SKU (partial match, case-insensitive)
    - `name`: Filter by name (partial match, case-insensitive)
    - `description`: Filter by description (partial match, case-insensitive)
    """
    # Build filter query
    query = db.query(Product)
    
    filters = []
    if sku:
        filters.append(Product.sku.ilike(f"%{sku}%"))
    if name:
        filters.append(Product.name.ilike(f"%{name}%"))
    # No active filter; model does not include `active` anymore
    if description:
        filters.append(Product.description.ilike(f"%{description}%"))
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    products = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": products,
    }


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
):
    """Create a new product.

    Request body fields:
    - `sku`, `name` required; `description` optional.
    """
    # Check if SKU already exists (case-insensitive)
    sku_norm = product.sku.lower().strip()
    existing = db.query(Product).filter(Product.sku_norm == sku_norm).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Product with SKU '{product.sku}' already exists (ID: {existing.id})"
        )
    
    # Create new product
    db_product = Product(
        sku=product.sku.strip(),
        sku_norm=sku_norm,
        name=product.name.strip(),
        description=product.description.strip() if product.description else None,
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    # Schedule webhook event for creation
    try:
        schedule_webhook_event("product.created", {
            "id": db_product.id,
            "sku": db_product.sku,
            "name": db_product.name,
            "description": db_product.description,
        })
    except Exception:
        pass
    
    return db_product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a product by ID.
    
    **Path Parameters:**
    - `product_id`: ID of the product to retrieve
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a product by ID.
    
    **Path Parameters:**
    - `product_id`: ID of the product to update
    
    **Request Body (all optional):**
    - `name`: Product name
    - `description`: Product description
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Update fields if provided
    if product.name is not None:
        db_product.name = product.name.strip()
    if product.description is not None:
        db_product.description = product.description.strip() if product.description else None
    # price/active removed from model
    
    db.commit()
    db.refresh(db_product)
    # Schedule webhook event for update
    try:
        schedule_webhook_event("product.updated", {
            "id": db_product.id,
            "sku": db_product.sku,
            "name": db_product.name,
            "description": db_product.description,
        })
    except Exception:
        pass
    
    return db_product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a product by ID.
    
    **Path Parameters:**
    - `product_id`: ID of the product to delete
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    
    if not db_product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    # capture info for webhook before deletion
    product_payload = {
        "id": db_product.id,
        "sku": db_product.sku,
        "name": db_product.name,
        "description": db_product.description,
    }
    db.delete(db_product)
    db.commit()
    # Schedule webhook for deletion
    try:
        schedule_webhook_event("product.deleted", product_payload)
    except Exception:
        pass
    
    return None
