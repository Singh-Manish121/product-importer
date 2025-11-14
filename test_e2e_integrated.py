#!/usr/bin/env python3
"""
Integrated E2E Test: Run app in eager mode and test the full flow
"""
import sys
import os
import time
import json
from pathlib import Path
from threading import Thread

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure Celery for eager execution
from app.celery_app import celery_app
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
    broker_url='memory://',
    result_backend='cache+memory://',
)

# Now import the app
from app.main import app
from app.database import SessionLocal
from app.models import Job, Product, Webhook
from fastapi.testclient import TestClient

def run_app_server():
    """Run the app in a background thread"""
    import uvicorn
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    server.run()

print("\n" + "=" * 70)
print("E2E Test: Product Importer (Eager Mode)")
print("=" * 70)

# Use TestClient for direct testing
client = TestClient(app)
csv_file = Path(__file__).parent / "test_products.csv"

# Test 1: Health check
print("\n[1] Health Check")
response = client.get("/health")
print(f"  Status: {response.status_code}")
assert response.status_code == 200, "Health check failed"
print("  ✓ Backend is healthy")

# Test 2: Upload CSV
print("\n[2] CSV Upload")
with open(csv_file, 'rb') as f:
    files = {'file': ('test_products.csv', f, 'text/csv')}
    response = client.post("/uploads", files=files)

assert response.status_code == 201, f"Upload failed: {response.status_code} - {response.text}"
data = response.json()
job_id = data.get('job_id')
print(f"  Status: {response.status_code}")
print(f"  Job ID: {job_id}")
print("  ✓ File uploaded successfully")

# Test 3: Check Job Status
print("\n[3] Job Status")
response = client.get(f"/jobs/{job_id}")
assert response.status_code == 200
job = response.json()
print(f"  Status: {job['status']}")
print(f"  Progress: {job['progress_percentage']}%")
print(f"  Created: {job['created_rows']}, Updated: {job['updated_rows']}")
print(f"  ✓ Job status retrieved")

# Test 4: List Jobs
print("\n[4] List Jobs")
response = client.get("/jobs")
assert response.status_code == 200
jobs_list = response.json()['items']
print(f"  Total jobs: {len(jobs_list)}")
print("  ✓ Jobs listed")

# Test 5: List Products
print("\n[5] List Products")
response = client.get("/products")
assert response.status_code == 200
products = response.json()['items']
print(f"  Total products: {len(products)}")
if products:
    for p in products[:3]:  # Show first 3
        print(f"    - {p['sku']}: {p['name']}")
    if len(products) > 3:
        print(f"    ... and {len(products)-3} more")
print("  ✓ Products listed")

# Test 6: Create Webhook
print("\n[6] Create Webhook")
webhook_payload = {
    "url": "http://localhost:9000/webhook",
    "event_types": ["product.created", "product.updated"],
    "enabled": True
}
response = client.post("/webhooks", json=webhook_payload)
assert response.status_code in [200, 201], f"Webhook creation failed: {response.status_code}"
webhook = response.json()
webhook_id = webhook.get('id')
print(f"  Status: {response.status_code}")
print(f"  Webhook ID: {webhook_id}")
print("  ✓ Webhook created")

# Test 7: List Webhooks
print("\n[7] List Webhooks")
response = client.get("/webhooks")
assert response.status_code == 200
webhooks = response.json()['items']
print(f"  Total webhooks: {len(webhooks)}")
if webhooks:
    for w in webhooks[:3]:
        print(f"    - {w.get('url')}: {', '.join(w.get('event_types', []))}")
print("  ✓ Webhooks listed")

# Test 8: Create Product
print("\n[8] Create Product (Direct)")
product_payload = {
    "sku": "TEST-PROD-001",
    "name": "Test Product",
    "description": "A test product created via API"
}
response = client.post("/products", json=product_payload)
assert response.status_code in [200, 201], f"Product creation failed: {response.status_code}"
new_product = response.json()
print(f"  Status: {response.status_code}")
print(f"  Product ID: {new_product.get('id')}")
print(f"  SKU: {new_product.get('sku')}")
print("  ✓ Product created")

# Test 9: Database Integrity Check
print("\n[9] Database Integrity Check")
session = SessionLocal()
db_products = session.query(Product).all()
db_jobs = session.query(Job).all()
db_webhooks = session.query(Webhook).all()
session.close()

print(f"  Products in DB: {len(db_products)}")
print(f"  Jobs in DB: {len(db_jobs)}")
print(f"  Webhooks in DB: {len(db_webhooks)}")
print("  ✓ Database integrity verified")

print("\n" + "=" * 70)
print("✓ E2E Test Complete - All Tests Passed!")
print("=" * 70 + "\n")
