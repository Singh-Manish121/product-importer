"""Tests for upload endpoint."""
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Job
import io
import os

client = TestClient(app)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

print("Testing uploads endpoint")

sample_csv = "sku,name,description,price,active\nTEST-1,Test Product,Sample,9.99,True\n"
files = {"file": ("sample.csv", sample_csv, "text/csv")}
resp = client.post("/uploads", files=files)
assert resp.status_code == 201, f"Expected 201, got {resp.status_code} - {resp.text}"
body = resp.json()
assert "job_id" in body
print(f"Created job: {body['job_id']} status={body.get('status')}")

# Verify job exists in DB
db = SessionLocal()
job = db.query(Job).filter(Job.job_id == body["job_id"]).first()
assert job is not None, "Job should be present in DB"
print(f"Job in DB: id={job.id}, filename={job.filename}")
# File should exist
assert os.path.exists(job.filename), "Uploaded file was not saved"
print("Upload file saved and job created - PASS")

# Cleanup
try:
    os.remove(job.filename)
except Exception:
    pass

db.delete(job)
db.commit()
db.close()
print("ALL upload tests passed")
