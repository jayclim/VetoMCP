from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from auth import get_current_user
from database import get_session
from models import (
    BudgetCategoryCreate,
    BudgetCategoryPublic,
    DashboardSummary,
    User,
)
from services import budget_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("/categories", response_model=BudgetCategoryPublic)
def create_category(
    body: BudgetCategoryCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return budget_service.create_category(session, user.id, body)


@router.get("/categories", response_model=List[BudgetCategoryPublic])
def list_categories(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return budget_service.get_categories(session, user.id)


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return budget_service.get_dashboard_summary(session, user.id)
