"""Transaction business logic — MCP-ready standalone functions."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from models import (
    Transaction,
    TransactionCreate,
    TransactionPublic,
    TransactionType,
)


def add_transaction(
    session: Session,
    user_id: str,
    data: TransactionCreate,
) -> TransactionPublic:
    """Create a new transaction for a user."""
    tx = Transaction(
        user_id=user_id,
        amount=data.amount,
        description=data.description,
        category=data.category,
        transaction_type=data.transaction_type,
        date=data.date or datetime.utcnow(),
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return TransactionPublic.model_validate(tx)


def delete_transaction(
    session: Session,
    user_id: str,
    transaction_id: str,
) -> bool:
    """Delete a transaction owned by the user. Returns True if deleted."""
    tx = session.exec(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
    ).first()
    if not tx:
        return False
    session.delete(tx)
    session.commit()
    return True


def get_transactions(
    session: Session,
    user_id: str,
    category: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[TransactionPublic]:
    """Retrieve transactions for a user with optional filters."""
    stmt = select(Transaction).where(Transaction.user_id == user_id)

    if category:
        stmt = stmt.where(Transaction.category == category)
    if transaction_type:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    if start_date:
        stmt = stmt.where(Transaction.date >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.date <= end_date)

    stmt = stmt.order_by(Transaction.date.desc())  # type: ignore[union-attr]
    rows = session.exec(stmt).all()
    return [TransactionPublic.model_validate(r) for r in rows]
