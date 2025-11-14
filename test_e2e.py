#!/usr/bin/env python3
"""
E2E Test: Product Importer from Upload to Database
Tests: CSV upload -> Job creation -> Product listing -> Webhooks
"""
import requests
import time
import json
from pathlib import Path

API_BASE = "http://localhost:8000"
CSV_FILE = Path(__file__).parent / "test_products.csv"

def test_upload_csv():
    """Test CSV upload and Job creation"""
    print("\n=== Testing CSV Upload ===")
    with open(CSV_FILE, 'rb') as f:
        files = {'file': ('test_products.csv', f, 'text/csv')}
        response = requests.post(f"{API_BASE}/uploads", files=files)
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 200:
        job_id = data.get('job_id')
        print(f"✓ Upload successful, job_id: {job_id}")
        return job_id
    else:
        print("✗ Upload failed")
        return None

def test_job_status(job_id):
    """Poll job status until completion"""
    print(f"\n=== Monitoring Job {job_id} ===")
    max_polls = 30
    for i in range(max_polls):
        response = requests.get(f"{API_BASE}/jobs/{job_id}")
        data = response.json()
        
        status = data.get('status')
        progress = data.get('progress_percentage', 0)
        processed = data.get('rows_processed', 0)
        created = data.get('rows_created', 0)
        
        print(f"[Poll {i+1}] Status: {status}, Progress: {progress}%, Processed: {processed}, Created: {created}")
        
        if status in ['COMPLETED', 'FAILED']:
            print(f"✓ Job {status}")
            if data.get('errors'):
                print(f"  Errors: {data['errors']}")
            return data
        
        time.sleep(1)
    
    print("✗ Job did not complete within timeout")
    return None

def test_list_jobs():
    """Test listing all jobs"""
    print(f"\n=== Listing All Jobs ===")
    response = requests.get(f"{API_BASE}/jobs")
    data = response.json()
    
    jobs = data.get('jobs', [])
    print(f"Found {len(jobs)} job(s)")
    for job in jobs:
        print(f"  - {job.get('job_id')}: {job.get('status')} ({job.get('progress_percentage')}%)")
    
    return jobs

def test_list_products():
    """Test listing products"""
    print(f"\n=== Listing Products ===")
    response = requests.get(f"{API_BASE}/products")
    data = response.json()
    
    products = data.get('products', [])
    print(f"Found {len(products)} product(s)")
    for product in products:
        print(f"  - SKU: {product.get('sku')}, Name: {product.get('name')}")
    
    return products

def test_create_webhook():
    """Test webhook registration"""
    print(f"\n=== Creating Webhook ===")
    payload = {
        "url": "http://localhost:9000/webhook",
        "event_types": ["product.created", "product.updated"],
        "enabled": True
    }
    response = requests.post(f"{API_BASE}/webhooks", json=payload)
    
    if response.status_code in [200, 201]:
        data = response.json()
        webhook_id = data.get('id')
        print(f"✓ Webhook created, id: {webhook_id}")
        return webhook_id
    else:
        print(f"✗ Webhook creation failed: {response.status_code}")
        return None

def test_list_webhooks():
    """Test listing webhooks"""
    print(f"\n=== Listing Webhooks ===")
    response = requests.get(f"{API_BASE}/webhooks")
    data = response.json()
    
    webhooks = data.get('webhooks', [])
    print(f"Found {len(webhooks)} webhook(s)")
    for webhook in webhooks:
        print(f"  - ID: {webhook.get('id')}, URL: {webhook.get('url')}, Enabled: {webhook.get('enabled')}")
    
    return webhooks

def main():
    print("=" * 60)
    print("E2E Test: Product Importer System")
    print("=" * 60)
    
    # Test 1: Upload CSV
    job_id = test_upload_csv()
    if not job_id:
        print("\n✗ E2E test failed at upload stage")
        return
    
    # Test 2: Monitor job
    job_data = test_job_status(job_id)
    if not job_data:
        print("\n✗ E2E test failed at job monitoring stage")
        return
    
    # Test 3: List jobs
    test_list_jobs()
    
    # Test 4: List products
    products = test_list_products()
    if not products:
        print("✗ No products found after import")
    else:
        print(f"✓ {len(products)} product(s) found in database")
    
    # Test 5: Create webhook
    webhook_id = test_create_webhook()
    
    # Test 6: List webhooks
    test_list_webhooks()
    
    print("\n" + "=" * 60)
    print("E2E Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
