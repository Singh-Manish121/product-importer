"""File upload endpoints for CSV imports."""
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi import status
from uuid import uuid4
from app.config import get_settings
from app.database import get_db
from sqlalchemy.orm import Session
from app.models import Job, JobStatus
from datetime import datetime
from pathlib import Path
from app.celery_app import celery_app

router = APIRouter(prefix="/uploads", tags=["uploads"])

settings = get_settings()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", status_code=201)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV file and create an import job.

    - Saves the uploaded file under `backend/uploads/` directory.
    - Creates a Job row with status PENDING and returns job_id.
    - If Celery is available and a worker is running, it will attempt to enqueue a background task. If not, the job will remain pending.
    """
    # Basic validation
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    # Save file in streaming mode and enforce max size
    file_id = uuid4().hex
    safe_name = f"{file_id}_{os.path.basename(file.filename)}"
    dest_path = UPLOAD_DIR / safe_name

    total_bytes = 0
    try:
        with open(dest_path, "wb") as dest:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size:
                    dest.close()
                    dest_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="Uploaded file is too large")
                dest.write(chunk)
    finally:
        await file.close()

    # Create Job record
    job_uuid = str(uuid4())
    db_job = Job(
        job_id=job_uuid,
        status=JobStatus.PENDING,
        filename=str(dest_path),
        total_rows=0,
        processed_rows=0,
        created_rows=0,
        updated_rows=0,
        failed_rows=0,
        current_step=None,
        progress_percentage=0,
        started_at=None,
        completed_at=None,
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    # Try to enqueue Celery task (best-effort)
    celery_task_id = None
    try:
        # Use a best-effort send_task; actual task implementation will be added in Task 6
        async_result = celery_app.send_task("app.tasks.import_csv", args=[db_job.job_id, str(dest_path)])
        celery_task_id = getattr(async_result, "id", None)
        if celery_task_id:
            db_job.celery_task_id = celery_task_id
            db.commit()
    except Exception:
        # If Celery broker not available, leave job pending and return success
        pass

    return {"job_id": db_job.job_id, "status": db_job.status, "celery_task_id": db_job.celery_task_id}
