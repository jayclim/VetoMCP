from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, field_validator


def _generate_id() -> str:
    return uuid4().hex


def _camel_alias(field_name: str) -> str:
    parts = field_name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_camel_alias,
        populate_by_name=True,
        from_attributes=True,
    )


class AuthorizationStatus(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    CAUTION = "CAUTION"
    REQUIRES_HUMAN_APPROVAL = "REQUIRES_HUMAN_APPROVAL"
    ERROR = "ERROR"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentSettingsCreate(CamelModel):
    single_transaction_limit: float = 50.0
    daily_limit: float = 100.0
    weekly_limit: float = 500.0
    monthly_limit: float = 2000.0
    require_approval_above: float = 100.0
    allowed_categories: Optional[List[str]] = None
    blocked_categories: Optional[List[str]] = None
    is_active: bool = True


class AgentSettingsUpdate(CamelModel):
    single_transaction_limit: Optional[float] = None
    daily_limit: Optional[float] = None
    weekly_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    require_approval_above: Optional[float] = None
    allowed_categories: Optional[List[str]] = None
    blocked_categories: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AgentSettingsPublic(CamelModel):
    id: str
    single_transaction_limit: float
    daily_limit: float
    weekly_limit: float
    monthly_limit: float
    require_approval_above: float
    allowed_categories: Optional[List[str]] = None
    blocked_categories: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @field_validator('allowed_categories', 'blocked_categories', mode='before')
    @classmethod
    def parse_json_field(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v


class AuthorizationLogCreate(CamelModel):
    agent_id: Optional[str] = None
    action_type: str  # purchase, transfer, subscription
    amount: float
    category: Optional[str] = None
    merchant: Optional[str] = None
    description: Optional[str] = None
    status: AuthorizationStatus
    reason: Optional[str] = None
    risk_score: Optional[int] = None
    authorization_token: Optional[str] = None


class AuthorizationLogPublic(CamelModel):
    id: str
    user_id: str
    agent_id: Optional[str] = None
    action_type: str
    amount: float
    category: Optional[str] = None
    merchant: Optional[str] = None
    description: Optional[str] = None
    status: str
    reason: Optional[str] = None
    risk_score: Optional[int] = None
    authorization_token: Optional[str] = None
    was_executed: bool
    created_at: datetime
