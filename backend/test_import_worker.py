"""Test CSV import worker (Celery task)."""
import csv
from pathlib import Path
import tempfile
from app.database import Base, engine, SessionLocal
from app.models import Job, JobStatus, Product
from app.tasks import import_csv
import uuid

# Setup: Create tables
Base.metadata.create_all(bind=engine)

print("=" * 80)
print("Testing CSV Import Worker")
print("=" * 80)

# Create a temporary CSV file with test data
test_csv_path = Path(tempfile.gettempdir()) / f"test_products_{uuid.uuid4().hex}.csv"

print("\n1. Creating test CSV file...")
with open(test_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["sku", "name", "description"])
    writer.writeheader()
    writer.writerow({"sku": "PROD-001", "name": "Product 1", "description": "First product"})
    writer.writerow({"sku": "PROD-002", "name": "Product 2", "description": "Second product"})
    writer.writerow({"sku": "prod-001", "name": "Product 1 Updated", "description": "Updated via case-insensitive match"})
    writer.writerow({"sku": "", "name": "Invalid Product", "description": "Missing SKU"})
    writer.writerow({"sku": "PROD-003", "name": "", "description": "Missing Name"})
    writer.writerow({"sku": "PROD-004", "name": "Product 4", "description": None})

print("[PASS] Test CSV created with 6 rows (2 valid new, 1 duplicate, 1 no sku, 1 no name, 1 no desc)")

# Create a Job record
print("\n2. Creating Job record...")
db = SessionLocal()
job_uuid = str(uuid.uuid4())
job = Job(
    job_id=job_uuid,
    status=JobStatus.PENDING,
    filename=str(test_csv_path),
    total_rows=0,
    processed_rows=0,
    created_rows=0,
    updated_rows=0,
    failed_rows=0,
)
db.add(job)
db.commit()
print(f"[PASS] Job created with ID: {job_uuid}")

# Run the task (directly call the task function, not through Celery worker)
print("\n3. Running import_csv task (synchronous)...")
result = import_csv(
    job_id=job_uuid,
    filepath=str(test_csv_path)
)

print(f"[PASS] Task completed with result: {result}")

# Verify results in database
print("\n4. Verifying results in database...")
db = SessionLocal()
job = db.query(Job).filter(Job.job_id == job_uuid).first()
print(f"Job status: {job.status}")
print(f"Processed rows: {job.processed_rows}")
print(f"Created rows: {job.created_rows}")
print(f"Updated rows: {job.updated_rows}")
print(f"Failed rows: {job.failed_rows}")
print(f"Progress: {job.progress_percentage}%")

assert job.status == JobStatus.COMPLETED, "Job should be completed"
assert job.processed_rows == 6, f"Expected 6 processed rows, got {job.processed_rows}"
assert job.created_rows == 3, f"Expected 3 created (PROD-001, PROD-002, PROD-004), got {job.created_rows}"
assert job.updated_rows == 1, f"Expected 1 updated (prod-001 -> PROD-001), got {job.updated_rows}"
assert job.failed_rows == 2, f"Expected 2 failed (missing sku/name), got {job.failed_rows}"
assert job.progress_percentage == 100, "Progress should be 100%"
print("[PASS] Job stats correct")

# Verify products created
print("\n5. Verifying products in database...")
products = db.query(Product).all()
print(f"Total products: {len(products)}")
for p in products:
    print(f"  - {p.id}: {p.sku} - {p.name}")

assert len(products) == 3, f"Expected 3 products, got {len(products)}"

# Verify PROD-001 was updated (not duplicated)
prod_001 = db.query(Product).filter(Product.sku_norm == "prod-001").first()
assert prod_001 is not None, "PROD-001 should exist"
assert prod_001.name == "Product 1 Updated", "PROD-001 should be updated to latest name"
print("[PASS] Deduplication (case-insensitive SKU update) works correctly")

# Verify errors recorded
print("\n6. Verifying error tracking...")
print(f"Errors recorded: {len(job.errors)}")
for err in job.errors:
    print(f"  - Row {err['row']}: {err['error']}")

assert len(job.errors) >= 2, "Should have at least 2 errors recorded"
print("[PASS] Error tracking works")

# Cleanup
test_csv_path.unlink(missing_ok=True)
db.query(Product).delete()
db.query(Job).delete()
db.commit()
db.close()

print("\n" + "=" * 80)
print("[SUCCESS] ALL CSV IMPORT WORKER TESTS PASSED!")
print("=" * 80)
