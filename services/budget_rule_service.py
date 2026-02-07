"""Budget rule business logic — MCP-ready standalone functions."""
from __future__ import annotations

import json
from typing import List, Optional

from sqlmodel import Session, select

from models import (
    BudgetRule,
    BudgetRuleCreate,
    BudgetRulePublic,
    RuleType,
    Transaction,
    TransactionType,
)


def create_rule(
    session: Session,
    user_id: str,
    data: BudgetRuleCreate,
) -> BudgetRulePublic:
    """Create a new budget rule for a user."""
    rule = BudgetRule(
        user_id=user_id,
        rule_type=data.rule_type,
        name=data.name,
        config=data.config,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return BudgetRulePublic.model_validate(rule)


def get_rules(
    session: Session,
    user_id: str,
    active_only: bool = True,
) -> list[BudgetRulePublic]:
    """List all budget rules for a user."""
    stmt = select(BudgetRule).where(BudgetRule.user_id == user_id)
    if active_only:
        stmt = stmt.where(BudgetRule.is_active == True)
    rows = session.exec(stmt).all()
    return [BudgetRulePublic.model_validate(r) for r in rows]


def delete_rule(
    session: Session,
    user_id: str,
    rule_id: str,
) -> bool:
    """Delete a budget rule. Returns True if deleted."""
    rule = session.exec(
        select(BudgetRule).where(
            BudgetRule.id == rule_id,
            BudgetRule.user_id == user_id,
        )
    ).first()
    if not rule:
        return False
    session.delete(rule)
    session.commit()
    return True


def check_rule_compliance(
    session: Session,
    user_id: str,
) -> dict:
    """
    Check if the user is following their active budget rules.
    Returns a dict with compliance status for each rule.
    """
    rules = session.exec(
        select(BudgetRule).where(
            BudgetRule.user_id == user_id,
            BudgetRule.is_active == True,
        )
    ).all()

    if not rules:
        return {"status": "no_rules", "message": "No active budget rules found."}

    # Get transactions for analysis
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

    results = []
    for rule in rules:
        config = json.loads(rule.config) if rule.config else {}
        compliance = {"rule_name": rule.name, "rule_type": rule.rule_type.value}

        if rule.rule_type == RuleType.percentage_allocation:
            # e.g., config = {"needs": 50, "wants": 30, "savings": 20}
            # This is more of a guideline check
            if total_income > 0:
                savings_rate = ((total_income - total_expenses) / total_income) * 100
                target_savings = config.get("savings", 20)
                compliance["target_savings_pct"] = target_savings
                compliance["actual_savings_pct"] = round(savings_rate, 1)
                compliance["compliant"] = savings_rate >= target_savings
            else:
                compliance["compliant"] = None
                compliance["message"] = "No income recorded yet."

        elif rule.rule_type == RuleType.category_limit:
            # e.g., config = {"category": "Food", "limit": 500}
            category = config.get("category", "")
            limit = config.get("limit", 0)
            spent = expense_by_cat.get(category, 0)
            compliance["category"] = category
            compliance["limit"] = limit
            compliance["spent"] = spent
            compliance["compliant"] = spent <= limit

        elif rule.rule_type == RuleType.savings_goal:
            # e.g., config = {"goal": 1000}
            goal = config.get("goal", 0)
            saved = total_income - total_expenses
            compliance["goal"] = goal
            compliance["saved"] = saved
            compliance["compliant"] = saved >= goal

        elif rule.rule_type == RuleType.spending_alert:
            # e.g., config = {"category": "Entertainment", "threshold": 200}
            category = config.get("category", "")
            threshold = config.get("threshold", 0)
            spent = expense_by_cat.get(category, 0)
            compliance["category"] = category
            compliance["threshold"] = threshold
            compliance["spent"] = spent
            compliance["alert_triggered"] = spent >= threshold
            compliance["compliant"] = spent < threshold

        results.append(compliance)

    return {"status": "checked", "rules": results}
