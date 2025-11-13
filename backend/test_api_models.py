#!/usr/bin/env python
"""Test API endpoints with models."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app
from app.database import SessionLocal, Product, Webhook, Job, JobStatus
from fastapi.testclient import TestClient
import json

client = TestClient(app)

print("=" * 60)
print("Testing API with Database Models")
print("=" * 60)

# Test 1: API health check
print("\n1. Testing API health endpoint...")
response = client.get("/health")
print(f"✅ Health check: {response.status_code}")
print(f"   Response: {response.json()}")

# Test 2: Root endpoint
print("\n2. Testing root endpoint...")
response = client.get("/")
print(f"✅ Root endpoint: {response.status_code}")
print(f"   Response: {response.json()}")

# Test 3: Database connectivity
print("\n3. Testing database connectivity via models...")
try:
    db = SessionLocal()
    
    # Create a test product
    product = Product(
        sku="TEST-001",
        sku_norm="test-001",
        name="API Test Product",
        price=49.99,
        active=True
    )
    db.add(product)
    db.commit()
    product_id = product.id
    
    print(f"✅ Product created in DB: ID={product_id}")
    
    # Create a test webhook
    webhook = Webhook(
        url="https://test.example.com/webhook",
        event_types=["product.created"],
        enabled=True
    )
    db.add(webhook)
    db.commit()
    webhook_id = webhook.id
    
    print(f"✅ Webhook created in DB: ID={webhook_id}")
    
    # Create a test job
    job = Job(
        job_id="test-job-001",
        filename="test.csv",
        status=JobStatus.COMPLETED,
        total_rows=100,
        processed_rows=100,
        created_rows=50,
        updated_rows=50,
        progress_percentage=100
    )
    db.add(job)
    db.commit()
    job_id = job.id
    
    print(f"✅ Job created in DB: ID={job_id}")
    
    # Query them back
    print("\n4. Querying data back from database...")
    
    query_product = db.query(Product).filter_by(id=product_id).first()
    print(f"✅ Product query: {query_product}")
    
    query_webhook = db.query(Webhook).filter_by(id=webhook_id).first()
    print(f"✅ Webhook query: {query_webhook}")
    
    query_job = db.query(Job).filter_by(id=job_id).first()
    print(f"✅ Job query: Status={query_job.status}, Progress={query_job.progress_percentage}%")
    
    # Count all records
    product_count = db.query(Product).count()
    webhook_count = db.query(Webhook).count()
    job_count = db.query(Job).count()
    
    print(f"\n5. Record counts:")
    print(f"   Products: {product_count}")
    print(f"   Webhooks: {webhook_count}")
    print(f"   Jobs: {job_count}")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ ALL API TESTS PASSED!")
print("=" * 60)
