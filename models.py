from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


def _generate_id() -> str:
    return uuid4().hex


def _camel_alias(field_name: str) -> str:
    parts = field_name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


class CamelModel(SQLModel):
    model_config = ConfigDict(
        alias_generator=_camel_alias,
        populate_by_name=True,
    )


# ── Table Models (DB) ─────────────────────────────────────────────


class User(SQLModel, table=True):
    id: str = Field(default_factory=_generate_id, primary_key=True)
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=_generate_id, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    amount: float
    description: str
    category: str = Field(default="Uncategorized")
    transaction_type: TransactionType = Field(default=TransactionType.expense)
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BudgetCategory(SQLModel, table=True):
    id: str = Field(default_factory=_generate_id, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    name: str
    monthly_limit: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RuleType(str, Enum):
    percentage_allocation = "percentage_allocation"  # e.g., 50/30/20
    category_limit = "category_limit"               # max spend per category
    savings_goal = "savings_goal"                   # save X per month
    spending_alert = "spending_alert"               # alert when threshold hit


class BudgetRule(SQLModel, table=True):
    id: str = Field(default_factory=_generate_id, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    rule_type: RuleType
    name: str  # e.g., "50/30/20 Rule", "Groceries Alert"
    config: str  # JSON string with rule-specific configuration
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Public Models (Pydantic schemas for API) ──────────────────────


class TransactionCreate(CamelModel):
    amount: float
    description: str
    category: str = "Uncategorized"
    transaction_type: TransactionType = TransactionType.expense
    date: Optional[datetime] = None


class TransactionPublic(CamelModel):
    id: str
    amount: float
    description: str
    category: str
    transaction_type: TransactionType
    date: datetime
    created_at: datetime


class BudgetCategoryCreate(CamelModel):
    name: str
    monthly_limit: float


class BudgetCategoryPublic(CamelModel):
    id: str
    name: str
    monthly_limit: float
    created_at: datetime


class CategorySummary(CamelModel):
    category: str
    total_spent: float
    budget_limit: Optional[float] = None
    remaining: Optional[float] = None


class DashboardSummary(CamelModel):
    total_income: float
    total_expenses: float
    net: float
    categories: List[CategorySummary]


class UserPublic(CamelModel):
    id: str
    username: str
    created_at: datetime


class BudgetRuleCreate(CamelModel):
    rule_type: RuleType
    name: str
    config: str  # JSON string


class BudgetRulePublic(CamelModel):
    id: str
    rule_type: RuleType
    name: str
    config: str
    is_active: bool
    created_at: datetime
