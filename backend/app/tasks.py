"""CSV import Celery task for bulk product processing."""
import csv
from pathlib import Path
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Product, Job, JobStatus, Webhook
import time
import httpx
from datetime import datetime
import json
import redis
from app.config import get_settings

settings = get_settings()

# Redis connection for progress pub/sub
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
except Exception:
    redis_client = None


def publish_progress(job_id: str, step: str, processed: int, created: int, updated: int, failed: int, total: int, percentage: int, errors: list = None):
    """Publish progress event to Redis pub/sub channel."""
    if not redis_client:
        return
    
    channel = f"job:{job_id}:progress"
    message = {
        "job_id": job_id,
        "current_step": step,
        "processed_rows": processed,
        "created_rows": created,
        "updated_rows": updated,
        "failed_rows": failed,
        "total_rows": total,
        "progress_percentage": percentage,
        "errors": errors or [],
    }
    
    try:
        redis_client.publish(channel, json.dumps(message))
    except Exception:
        pass


@celery_app.task(bind=True, name="app.tasks.deliver_webhook", max_retries=5)
def deliver_webhook(self, webhook_id: int, event_type: str, payload: dict):
    """Deliver a single webhook payload and record result on the Webhook row.

    Retries on network errors or 5xx responses with exponential backoff.
    """
    db = SessionLocal()
    try:
        wh = db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not wh or not wh.enabled:
            return {"skipped": True}

        url = wh.url
        headers = {"Content-Type": "application/json"}
        start = time.time()
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(url, json={"event": event_type, "data": payload}, headers=headers)
        except Exception as exc:
            # Retry on network errors
            wh.last_error = str(exc)
            wh.last_response_status = None
            wh.last_triggered_at = datetime.utcnow()
            db.commit()
            # exponential backoff
            retries = getattr(self.request, "retries", 0)
            countdown = min(60, 2 ** retries)
            raise self.retry(exc=exc, countdown=countdown)

        elapsed_ms = int((time.time() - start) * 1000)
        wh.last_triggered_at = datetime.utcnow()
        wh.last_response_time_ms = elapsed_ms
        wh.last_response_status = resp.status_code
        wh.last_error = None if 200 <= resp.status_code < 300 else resp.text[:2000]
        db.commit()

        # If server error, retry
        if 500 <= resp.status_code < 600:
            retries = getattr(self.request, "retries", 0)
            countdown = min(60, 2 ** retries)
            raise self.retry(exc=Exception(f"Server error {resp.status_code}"), countdown=countdown)

        return {"status": resp.status_code}
    finally:
        db.close()


def schedule_webhook_event(event_type: str, payload: dict):
    """Find enabled webhooks interested in this event and enqueue delivery tasks."""
    db = SessionLocal()
    try:
        webhooks = db.query(Webhook).filter(Webhook.enabled == True).all()
        for wh in webhooks:
            events = wh.event_types or []
            if event_type in events:
                try:
                    celery_app.send_task("app.tasks.deliver_webhook", args=[wh.id, event_type, payload])
                except Exception:
                    # best-effort, don't block processing on webhook enqueue failure
                    pass
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.import_csv")
def import_csv(self, job_id: str, filepath: str):
    """
    Celery task to import CSV file and create/update products.
    
    Args:
        job_id: UUID of the Job record
        filepath: Full path to the CSV file
    """
    db = SessionLocal()
    
    try:
        # Get job record
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}
        
        # Update job: started processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        job.celery_task_id = self.request.id
        db.commit()
        
        # Read CSV file
        filepath_obj = Path(filepath)
        if not filepath_obj.exists():
            job.status = JobStatus.FAILED
            job.error_message = f"File not found: {filepath}"
            db.commit()
            return {"error": f"File not found: {filepath}"}
        
        # Parse CSV and collect rows
        rows = []
        publish_progress(job_id, "parsing", 0, 0, 0, 0, 0, 0)
        
        try:
            with open(filepath_obj, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ValueError("CSV has no header")
                
                # Expect: sku, name, description (at minimum)
                required_fields = {"sku", "name"}
                if not required_fields.issubset(set(reader.fieldnames or [])):
                    raise ValueError(f"CSV must have columns: {required_fields}")
                
                for row_num, row in enumerate(reader, start=2):  # start=2 to skip header
                    rows.append((row_num, row))
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = f"CSV parsing error: {str(e)}"
            db.commit()
            db.close()
            return {"error": str(e)}
        
        total_rows = len(rows)
        job.total_rows = total_rows
        db.commit()
        
        # Process rows in batches
        created_count = 0
        updated_count = 0
        failed_count = 0
        error_list = []
        batch_size = settings.csv_chunk_size  # 10,000
        session_skus = {}  # Track SKUs added in current session batch (for duplicate detection)
        
        publish_progress(job_id, "validating", 0, 0, 0, 0, total_rows, 0)
        
        for idx, (row_num, row) in enumerate(rows):
            try:
                sku = row.get("sku", "").strip()
                name = row.get("name", "").strip()
                description = row.get("description", "").strip() or None
                
                # Validation
                if not sku or not name:
                    failed_count += 1
                    error_list.append({
                        "row": row_num,
                        "error": "Missing sku or name"
                    })
                    continue
                
                # Check if product exists (by sku_norm)
                sku_norm = sku.lower()
                
                # Check session batch first, then database
                if sku_norm in session_skus:
                    # Update the product added in this batch
                    product = session_skus[sku_norm]
                    product.name = name
                    product.description = description
                    product.updated_at = datetime.utcnow()
                    updated_count += 1
                    # schedule webhook for update
                    try:
                        schedule_webhook_event("product.updated", {
                            "sku": product.sku,
                            "name": product.name,
                            "description": product.description,
                        })
                    except Exception:
                        pass
                    continue
                
                existing = db.query(Product).filter(Product.sku_norm == sku_norm).first()
                
                
                if existing:
                    # Update
                    existing.name = name
                    existing.description = description
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                    # schedule webhook for update
                    try:
                        schedule_webhook_event("product.updated", {
                            "id": existing.id,
                            "sku": existing.sku,
                            "name": existing.name,
                            "description": existing.description,
                        })
                    except Exception:
                        pass
                else:
                    # Create
                    new_product = Product(
                        sku=sku,
                        sku_norm=sku_norm,
                        name=name,
                        description=description,
                    )
                    db.add(new_product)
                    session_skus[sku_norm] = new_product  # Track for duplicate detection in batch
                    created_count += 1
                    # schedule webhook for creation
                    try:
                        schedule_webhook_event("product.created", {
                            "sku": new_product.sku,
                            "name": new_product.name,
                            "description": new_product.description,
                        })
                    except Exception:
                        pass
                
                # Batch commit every N rows
                if (idx + 1) % batch_size == 0:
                    db.commit()
                    session_skus.clear()  # Reset session batch tracker
                    processed = idx + 1
                    percentage = int((processed / total_rows) * 100)
                    job.processed_rows = processed
                    job.created_rows = created_count
                    job.updated_rows = updated_count
                    job.failed_rows = failed_count
                    job.progress_percentage = percentage
                    job.current_step = "importing"
                    db.commit()
                    
                    publish_progress(
                        job_id,
                        "importing",
                        processed,
                        created_count,
                        updated_count,
                        failed_count,
                        total_rows,
                        percentage,
                        error_list[-10:] if len(error_list) > 10 else error_list
                    )
            
            except Exception as e:
                failed_count += 1
                error_list.append({
                    "row": row_num,
                    "error": str(e),
                    "sku": row.get("sku", "")
                })
        
        # Final commit for remaining rows
        db.commit()
        
        # Mark job as completed
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.processed_rows = total_rows
        job.created_rows = created_count
        job.updated_rows = updated_count
        job.failed_rows = failed_count
        job.progress_percentage = 100
        job.current_step = "completed"
        job.errors = error_list
        db.commit()
        
        # Final progress update
        publish_progress(
            job_id,
            "completed",
            total_rows,
            created_count,
            updated_count,
            failed_count,
            total_rows,
            100,
            error_list
        )
        
        return {
            "job_id": job_id,
            "total": total_rows,
            "created": created_count,
            "updated": updated_count,
            "failed": failed_count,
        }
    
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = f"Unexpected error: {str(e)}"
        job.completed_at = datetime.utcnow()
        db.commit()
        return {"error": str(e)}
    
    finally:
        db.close()
