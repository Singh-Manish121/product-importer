"""Webhook CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.webhook import Webhook
from app.schemas import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Webhook).order_by(Webhook.id)
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(payload: WebhookCreate, db: Session = Depends(get_db)):
    db_wh = Webhook(
        url=payload.url.strip(),
        event_types=payload.event_types,
        enabled=payload.enabled,
    )
    db.add(db_wh)
    db.commit()
    db.refresh(db_wh)
    return db_wh


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    wh = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return wh


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(webhook_id: int, payload: WebhookUpdate, db: Session = Depends(get_db)):
    wh = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    if payload.url is not None:
        wh.url = payload.url.strip()
    if payload.event_types is not None:
        wh.event_types = payload.event_types
    if payload.enabled is not None:
        wh.enabled = payload.enabled
    db.commit()
    db.refresh(wh)
    return wh


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    wh = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(wh)
    db.commit()
    return None
