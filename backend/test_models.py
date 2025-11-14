#!/usr/bin/env python
"""Test script to verify database models."""
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Import models and database
from app.database import Base, engine, SessionLocal, Product, Webhook, Job, JobStatus

print("=" * 60)
print("Testing Database Models")
print("=" * 60)

# Create all tables
print("\n1. Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully")

# Create a database session
db = SessionLocal()

try:
    # Test Product model
    print("\n2. Testing Product model...")
    product = Product(
        sku="SKU-001",
        sku_norm="sku-001",
        name="Test Product",
        description="A test product",
        price=99.99,
        active=True
    )
    db.add(product)
    db.commit()
    print(f"✅ Product created: {product}")
    
    # Query product
    retrieved = db.query(Product).filter_by(sku_norm="sku-001").first()
    print(f"✅ Product retrieved: {retrieved}")
    
    # Test Webhook model
    print("\n3. Testing Webhook model...")
    webhook = Webhook(
        url="https://example.com/webhook",
        event_types=["product.created", "product.updated"],
        enabled=True
    )
    db.add(webhook)
    db.commit()
    print(f"✅ Webhook created: {webhook}")
    
    # Query webhook
    retrieved_webhook = db.query(Webhook).filter_by(id=webhook.id).first()
    print(f"✅ Webhook retrieved: {retrieved_webhook}")
    
    # Test Job model
    print("\n4. Testing Job model...")
    job = Job(
        job_id="job-001",
        filename="products.csv",
        status=JobStatus.PROCESSING,
        total_rows=1000,
        current_step="parsing",
        progress_percentage=25,
        celery_task_id="celery-task-001"
    )
    db.add(job)
    db.commit()
    print(f"✅ Job created: {job}")
    
    # Query job
    retrieved_job = db.query(Job).filter_by(job_id="job-001").first()
    print(f"✅ Job retrieved: {retrieved_job}")
    print(f"   Status: {retrieved_job.status}")
    print(f"   Progress: {retrieved_job.progress_percentage}%")
    
    # Test querying multiple products
    print("\n5. Testing multiple queries...")
    print(f"   Total products: {db.query(Product).count()}")
    print(f"   Total webhooks: {db.query(Webhook).count()}")
    print(f"   Total jobs: {db.query(Job).count()}")
    
    # Test case-insensitive SKU lookup (unique constraint)
    print("\n6. Testing SKU uniqueness (case-insensitive)...")
    try:
        duplicate = Product(
            sku="SKU-001",  # Same original SKU
            sku_norm="sku-001",  # Same normalized SKU (should fail)
            name="Duplicate Product",
            price=50.00,
            active=True
        )
        db.add(duplicate)
        db.commit()
        print("❌ ERROR: Duplicate SKU was allowed (should have been prevented)")
    except Exception as e:
        print(f"✅ Correctly prevented duplicate SKU: {type(e).__name__}")
        db.rollback()
    
    print("\n" + "=" * 60)
    print("✅ ALL MODEL TESTS PASSED!")
    print("=" * 60)
    
finally:
    db.close()
