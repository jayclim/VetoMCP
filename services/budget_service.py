"""Budget business logic — MCP-ready standalone functions."""
from __future__ import annotations

from typing import Dict, List

from sqlmodel import Session, select, func

from models import (
    BudgetCategory,
    BudgetCategoryCreate,
    BudgetCategoryPublic,
    CategorySummary,
    DashboardSummary,
    Transaction,
    TransactionType,
)


def create_category(
    session: Session,
    user_id: str,
    data: BudgetCategoryCreate,
) -> BudgetCategoryPublic:
    """Create a budget category for a user."""
    cat = BudgetCategory(
        user_id=user_id,
        name=data.name,
        monthly_limit=data.monthly_limit,
    )
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return BudgetCategoryPublic.model_validate(cat)


def get_categories(
    session: Session,
    user_id: str,
) -> list[BudgetCategoryPublic]:
    """List all budget categories for a user."""
    rows = session.exec(
        select(BudgetCategory).where(BudgetCategory.user_id == user_id)
    ).all()
    return [BudgetCategoryPublic.model_validate(r) for r in rows]


def get_dashboard_summary(
    session: Session,
    user_id: str,
) -> DashboardSummary:
    """Build a dashboard summary: totals + per-category breakdown."""
    transactions = session.exec(
        select(Transaction).where(Transaction.user_id == user_id)
    ).all()

    total_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.income)
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == TransactionType.expense)

    # Per-category spending
    expense_by_cat: dict[str, float] = {}
    for t in transactions:
        if t.transaction_type == TransactionType.expense:
            expense_by_cat[t.category] = expense_by_cat.get(t.category, 0) + t.amount

    # Budget limits lookup
    budgets = session.exec(
        select(BudgetCategory).where(BudgetCategory.user_id == user_id)
    ).all()
    limit_map = {b.name: b.monthly_limit for b in budgets}

    categories: list[CategorySummary] = []
    all_cats = set(expense_by_cat.keys()) | set(limit_map.keys())
    for cat in sorted(all_cats):
        spent = expense_by_cat.get(cat, 0)
        limit = limit_map.get(cat)
        categories.append(
            CategorySummary(
                category=cat,
                total_spent=spent,
                budget_limit=limit,
                remaining=limit - spent if limit is not None else None,
            )
        )

    return DashboardSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net=total_income - total_expenses,
        categories=categories,
    )
