"""Job endpoints to list and inspect import jobs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    query = db.query(Job).order_by(Job.created_at.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.get("/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
