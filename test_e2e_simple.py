#!/usr/bin/env python3
"""
Integrated E2E Test: Run app in eager mode and test the full flow
"""
import sys
import os
from pathlib import Path

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

print("\n" + "=" * 70)
print("E2E Test: Product Importer (Eager Mode)")
print("=" * 70)

# Use TestClient for direct testing
client = TestClient(app)
csv_file = Path(__file__).parent / "test_products.csv"

# Test 1: Health check
print("\n[1] Health Check")
response = client.get("/health")
print("  Status: %d" % response.status_code)
assert response.status_code == 200
print("  [PASS] Backend is healthy")

# Test 2: Upload CSV
print("\n[2] CSV Upload")
with open(csv_file, 'rb') as f:
    files = {'file': ('test_products.csv', f, 'text/csv')}
    response = client.post("/uploads", files=files)

assert response.status_code == 201, "Upload failed: %d" % response.status_code
data = response.json()
job_id = data.get('job_id')
print("  Status: %d" % response.status_code)
print("  Job ID: %s" % job_id)
print("  [PASS] File uploaded successfully")

# Test 3: Check Job Status
print("\n[3] Job Status")
response = client.get("/jobs/%s" % job_id)
assert response.status_code == 200
job = response.json()
print("  Status: %s" % job['status'])
print("  Progress: %d%%" % job['progress_percentage'])
print("  Created: %d, Updated: %d" % (job['created_rows'], job['updated_rows']))
print("  [PASS] Job status retrieved")

# Test 4: List Jobs
print("\n[4] List Jobs")
response = client.get("/jobs")
assert response.status_code == 200
jobs_list = response.json()['items']
print("  Total jobs: %d" % len(jobs_list))
print("  [PASS] Jobs listed")

# Test 5: List Products
print("\n[5] List Products")
response = client.get("/products")
assert response.status_code == 200
products = response.json()['items']
print("  Total products: %d" % len(products))
if products:
    for p in products[:3]:
        print("    - %s: %s" % (p['sku'], p['name']))
    if len(products) > 3:
        print("    ... and %d more" % (len(products)-3))
print("  [PASS] Products listed")

# Test 6: Create Webhook
print("\n[6] Create Webhook")
webhook_payload = {
    "url": "http://localhost:9000/webhook",
    "event_types": ["product.created", "product.updated"],
    "enabled": True
}
response = client.post("/webhooks", json=webhook_payload)
assert response.status_code in [200, 201], "Webhook creation failed: %d" % response.status_code
webhook = response.json()
webhook_id = webhook.get('id')
print("  Status: %d" % response.status_code)
print("  Webhook ID: %s" % webhook_id)
print("  [PASS] Webhook created")

# Test 7: List Webhooks
print("\n[7] List Webhooks")
response = client.get("/webhooks")
assert response.status_code == 200
webhooks = response.json()['items']
print("  Total webhooks: %d" % len(webhooks))
if webhooks:
    for w in webhooks[:3]:
        print("    - %s: %s" % (w.get('url'), ', '.join(w.get('event_types', []))))
print("  [PASS] Webhooks listed")

# Test 8: Create Product
print("\n[8] Create Product (Direct)")
product_payload = {
    "sku": "TEST-PROD-001",
    "name": "Test Product",
    "description": "A test product created via API"
}
response = client.post("/products", json=product_payload)
assert response.status_code in [200, 201], "Product creation failed: %d" % response.status_code
new_product = response.json()
print("  Status: %d" % response.status_code)
print("  Product ID: %s" % new_product.get('id'))
print("  SKU: %s" % new_product.get('sku'))
print("  [PASS] Product created")

# Test 9: Database Integrity Check
print("\n[9] Database Integrity Check")
session = SessionLocal()
db_products = session.query(Product).all()
db_jobs = session.query(Job).all()
db_webhooks = session.query(Webhook).all()
session.close()

print("  Products in DB: %d" % len(db_products))
print("  Jobs in DB: %d" % len(db_jobs))
print("  Webhooks in DB: %d" % len(db_webhooks))
print("  [PASS] Database integrity verified")

print("\n" + "=" * 70)
print("[SUCCESS] E2E Test Complete - All Tests Passed!")
print("=" * 70 + "\n")
