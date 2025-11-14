#!/usr/bin/env python3
import sys
sys.path.insert(0, 'c:\\Users\\Admin\\Desktop\\Project\\interview-projects\\product-importer\\product-importer\\backend')

from app.database import SessionLocal
from app.models import Job, Product

session = SessionLocal()
jobs = session.query(Job).all()
products = session.query(Product).all()

print("\n=== Database State ===")
print(f"Jobs: {len(jobs)}")
for job in jobs:
    print(f"  - {job.job_id}: {job.status} ({job.progress_percentage}%, {job.created_rows} created, {job.updated_rows} updated)")

print(f"\nProducts: {len(products)}")
for p in products:
    print(f"  - {p.sku}: {p.name}")

session.close()
