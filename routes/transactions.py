from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from auth import get_current_user
from database import get_session
from models import (
    TransactionCreate,
    TransactionPublic,
    TransactionType,
    User,
)
from services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionPublic)
def create_transaction(
    body: TransactionCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return transaction_service.add_transaction(session, user.id, body)


@router.get("", response_model=List[TransactionPublic])
def list_transactions(
    category: Optional[str] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return transaction_service.get_transactions(
        session, user.id, category, transaction_type, start_date, end_date
    )


@router.delete("/{transaction_id}")
def remove_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    deleted = transaction_service.delete_transaction(session, user.id, transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"ok": True}
