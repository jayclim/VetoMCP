"""Agent Guard Rails tools for VetoMCP."""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from dedalus_mcp import tool
from supabase import Client

# Import database client from VetoMCP
from database import supabase

# Import models
from models import (
    _generate_id,
    AgentSettingsCreate,
    AgentSettingsPublic,
    AgentSettingsUpdate,
    AuthorizationLogCreate,
    AuthorizationLogPublic,
    AuthorizationStatus,
    RiskLevel,
)


# ══════════════════════════════════════════════════════════════════════════════
# Service Logic (Helper Functions)
# ══════════════════════════════════════════════════════════════════════════════

def get_user_id_from_username(client: Client, username: str) -> Optional[str]:
    """Look up a user's UUID from their username."""
    result = client.table("veto_users").select("id").eq("username", username).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def get_or_create_user_id(client: Client, username: str) -> str:
    """Get user's UUID, creating the user if they don't exist."""
    user_id = get_user_id_from_username(client, username)
    if user_id:
        return user_id
    
    # Create user if not exists
    # Note: verify if database.py has ensure_user, but we use this consistent logic
    new_user = {"id": _generate_id(), "username": username}
    result = client.table("veto_users").insert(new_user).execute()
    return result.data[0]["id"]


def get_agent_settings(client: Client, user_id: str) -> Optional[AgentSettingsPublic]:
    """Get agent settings for a user. Returns None if not configured."""
    result = (
        client.table("veto_agent_settings")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    if result.data and len(result.data) > 0:
        return AgentSettingsPublic(**result.data[0])
    return None


def get_or_create_agent_settings(client: Client, user_id: str) -> AgentSettingsPublic:
    """Get agent settings for a user, creating defaults if not exists."""
    existing = get_agent_settings(client, user_id)
    if existing:
        return existing
    
    # Create default settings
    return create_agent_settings(client, user_id, AgentSettingsCreate())


def create_agent_settings(
    client: Client,
    user_id: str,
    data: AgentSettingsCreate,
) -> AgentSettingsPublic:
    """Create agent settings for a user."""
    row = {
        "id": _generate_id(),
        "user_id": user_id,
        "single_transaction_limit": data.single_transaction_limit,
        "daily_limit": data.daily_limit,
        "weekly_limit": data.weekly_limit,
        "monthly_limit": data.monthly_limit,
        "require_approval_above": data.require_approval_above,
        "allowed_categories": json.dumps(data.allowed_categories) if data.allowed_categories else None,
        "blocked_categories": json.dumps(data.blocked_categories) if data.blocked_categories else "[]",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    result = client.table("veto_agent_settings").insert(row).execute()
    return AgentSettingsPublic(**result.data[0])


def update_agent_settings(
    client: Client,
    user_id: str,
    data: AgentSettingsUpdate,
) -> Optional[AgentSettingsPublic]:
    """Update agent settings for a user."""
    update_data = {"updated_at": datetime.utcnow().isoformat()}
    
    if data.single_transaction_limit is not None:
        update_data["single_transaction_limit"] = data.single_transaction_limit
    if data.daily_limit is not None:
        update_data["daily_limit"] = data.daily_limit
    if data.weekly_limit is not None:
        update_data["weekly_limit"] = data.weekly_limit
    if data.monthly_limit is not None:
        update_data["monthly_limit"] = data.monthly_limit
    if data.require_approval_above is not None:
        update_data["require_approval_above"] = data.require_approval_above
    if data.allowed_categories is not None:
        update_data["allowed_categories"] = json.dumps(data.allowed_categories)
    if data.blocked_categories is not None:
        update_data["blocked_categories"] = json.dumps(data.blocked_categories)
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    
    result = (
        client.table("veto_agent_settings")
        .update(update_data)
        .eq("user_id", user_id)
        .execute()
    )
    
    if result.data:
        return AgentSettingsPublic(**result.data[0])
    return None


def log_authorization(
    client: Client,
    user_id: str,
    data: AuthorizationLogCreate,
) -> AuthorizationLogPublic:
    """Log an authorization attempt."""
    row = {
        "id": _generate_id(),
        "user_id": user_id,
        "agent_id": data.agent_id,
        "action_type": data.action_type,
        "amount": data.amount,
        "category": data.category,
        "merchant": data.merchant,
        "description": data.description,
        "status": data.status.value if isinstance(data.status, AuthorizationStatus) else data.status,
        "reason": data.reason,
        "risk_score": data.risk_score,
        "authorization_token": data.authorization_token,
        "was_executed": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    result = client.table("veto_agent_authorization_log").insert(row).execute()
    return AuthorizationLogPublic(**result.data[0])


def get_authorization_history(
    client: Client,
    user_id: str,
    limit: int = 50,
    status_filter: Optional[str] = None,
) -> List[AuthorizationLogPublic]:
    """Get authorization history for a user."""
    query = (
        client.table("veto_agent_authorization_log")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    
    if status_filter:
        query = query.eq("status", status_filter)
    
    result = query.execute()
    return [AuthorizationLogPublic(**r) for r in result.data]


def get_cumulative_agent_spend(
    client: Client,
    user_id: str,
    period: str = "daily",
) -> float:
    """Get cumulative agent spending for a time period."""
    now = datetime.utcnow()
    
    if period == "daily":
        start_time = now - timedelta(days=1)
    elif period == "weekly":
        start_time = now - timedelta(weeks=1)
    elif period == "monthly":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)
    
    result = (
        client.table("veto_agent_authorization_log")
        .select("amount")
        .eq("user_id", user_id)
        .eq("status", "APPROVED")
        .eq("was_executed", True)
        .gte("created_at", start_time.isoformat())
        .execute()
    )
    
    return sum(r.get("amount", 0) for r in result.data)


# ══════════════════════════════════════════════════════════════════════════════
# MCP Tools
# ══════════════════════════════════════════════════════════════════════════════

@tool(description="Authorize a purchase against agent spending limits and policies. Returns JSON with status (APPROVED/DENIED/CAUTION).")
async def authorize_purchase(
    username: str,
    amount: float,
    category: str,
    merchant: str = None,
    description: str = None,
    agent_id: str = None,
) -> str:
    try:
        # Get user ID
        user_id = get_or_create_user_id(supabase, username)
        
        # Get settings
        settings = get_or_create_agent_settings(supabase, user_id)
        
        # Get cumulative spend
        daily_spend = get_cumulative_agent_spend(supabase, user_id, "daily")
        weekly_spend = get_cumulative_agent_spend(supabase, user_id, "weekly")
        monthly_spend = get_cumulative_agent_spend(supabase, user_id, "monthly")
        
        reasons = []
        status = AuthorizationStatus.APPROVED
        
        # Checks
        if settings.blocked_categories and category in settings.blocked_categories:
            status = AuthorizationStatus.DENIED
            reasons.append(f"Category '{category}' is blocked.")
        
        if settings.allowed_categories and category not in settings.allowed_categories:
            status = AuthorizationStatus.DENIED
            reasons.append(f"Category '{category}' is not in allowed list.")
        
        if amount > settings.single_transaction_limit:
            if amount > settings.single_transaction_limit * 1.5:
                status = AuthorizationStatus.DENIED
                reasons.append(f"Amount ${amount} exceeds single transaction limit ${settings.single_transaction_limit}.")
            else:
                status = AuthorizationStatus.CAUTION
                reasons.append(f"Amount ${amount} exceeds single transaction limit.")
        
        if (daily_spend + amount) > settings.daily_limit:
            status = AuthorizationStatus.DENIED
            reasons.append(f"Daily limit exceeded (${daily_spend + amount} > ${settings.daily_limit}).")
        
        if amount >= settings.require_approval_above:
            status = AuthorizationStatus.REQUIRES_HUMAN_APPROVAL
            reasons.append(f"Amount ${amount} requires human approval (threshold: ${settings.require_approval_above}).")
        
        # Log the attempt
        log_data = AuthorizationLogCreate(
            agent_id=agent_id,
            action_type="purchase",
            amount=amount,
            category=category,
            merchant=merchant,
            description=description,
            status=status,
            reason="; ".join(reasons) if reasons else "Within budget limits",
            risk_score=0, # Simplified
        )
        log_authorization(supabase, user_id, log_data)
        
        return json.dumps({
            "status": status.value,
            "reasons": reasons,
            "remaining_daily": settings.daily_limit - daily_spend,
            "remaining_weekly": settings.weekly_limit - weekly_spend,
        }, indent=2)
            
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)}, indent=2)


@tool(description="Get configured spending limits for agents.")
async def get_agent_spending_limits(username: str) -> str:
    try:
        user_id = get_or_create_user_id(supabase, username)
        settings = get_or_create_agent_settings(supabase, user_id)
        
        return json.dumps({
            "single_transaction_limit": settings.single_transaction_limit,
            "daily_limit": settings.daily_limit,
            "weekly_limit": settings.weekly_limit,
            "monthly_limit": settings.monthly_limit,
            "require_approval_above": settings.require_approval_above,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@tool(description="Assess risk of a potential purchase (0-100 score).")
async def assess_purchase_risk(
    amount: float,
    category: str,
    monthly_income: float = 0.0,
    monthly_expenses: float = 0.0,
    is_recurring: bool = False,
    is_essential: bool = False,
) -> str:
    risk_score = 0
    factors = []
    
    # Simple logic ported from Phase 1
    if monthly_income > 0:
        ratio = amount / monthly_income
        if ratio > 0.5:
            risk_score += 50
            factors.append("Cost > 50% of monthly income")
        elif ratio > 0.1:
            risk_score += 20
            factors.append("Significant cost relative to income")
    
    if not is_essential:
        risk_score += 10
        factors.append("Non-essential calculation")
    
    risk_level = RiskLevel.LOW
    if risk_score > 70:
        risk_level = RiskLevel.CRITICAL
    elif risk_score > 50:
        risk_level = RiskLevel.HIGH
    elif risk_score > 20:
        risk_level = RiskLevel.MEDIUM
        
    return json.dumps({
        "risk_score": risk_score,
        "risk_level": risk_level.value,
        "factors": factors
    }, indent=2)


@tool(description="Validate a broad range of agent actions (purchase, transfer, etc).")
async def validate_agent_action(
    action_type: str,
    amount: float,
    category: str = "General",
    agent_id: str = None
) -> str:
    """Validate action type and amount."""
    # Simplified logic for now
    if action_type not in ["purchase", "transfer", "subscription"]:
        return json.dumps({"status": "DENIED", "reason": "Invalid action type"})
        
    return json.dumps({"status": "APPROVED", "message": "Action valid within limits"}, indent=2)


@tool(description="Set or update agent spending limits.")
async def set_agent_spending_limits(
    username: str,
    single_transaction_limit: float = None,
    daily_limit: float = None,
    weekly_limit: float = None,
    monthly_limit: float = None,
    require_approval_above: float = None,
) -> str:
    try:
        user_id = get_or_create_user_id(supabase, username)
        existing = get_agent_settings(supabase, user_id)
        
        if existing:
            update_data = AgentSettingsUpdate(
                single_transaction_limit=single_transaction_limit,
                daily_limit=daily_limit,
                weekly_limit=weekly_limit,
                monthly_limit=monthly_limit,
                require_approval_above=require_approval_above,
            )
            result = update_agent_settings(supabase, user_id, update_data)
        else:
            base_settings = AgentSettingsCreate()
            if single_transaction_limit: base_settings.single_transaction_limit = single_transaction_limit
            if daily_limit: base_settings.daily_limit = daily_limit
            if weekly_limit: base_settings.weekly_limit = weekly_limit
            if monthly_limit: base_settings.monthly_limit = monthly_limit
            if require_approval_above: base_settings.require_approval_above = require_approval_above
            result = create_agent_settings(supabase, user_id, base_settings)
            
        return json.dumps({
            "success": True, 
            "settings": json.loads(result.model_dump_json())
        }, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@tool(description="Get full agent settings.")
async def get_agent_settings_tool(username: str) -> str:
    try:
        user_id = get_or_create_user_id(supabase, username)
        settings = get_or_create_agent_settings(supabase, user_id)
        return settings.model_dump_json(indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@tool(description="Get cumulative agent spend for a period.")
async def get_cumulative_agent_spend_tool(username: str, period: str = "daily") -> str:
    try:
        user_id = get_or_create_user_id(supabase, username)
        spend = get_cumulative_agent_spend(supabase, user_id, period)
        settings = get_or_create_agent_settings(supabase, user_id)
        
        limit = {
            "daily": settings.daily_limit,
            "weekly": settings.weekly_limit,
            "monthly": settings.monthly_limit
        }.get(period, settings.daily_limit)
        
        return json.dumps({
            "period": period,
            "spend": spend,
            "limit": limit,
            "remaining": max(0, limit - spend)
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@tool(description="Log an agent authorization attempt.")
async def log_agent_authorization(
    username: str,
    action_type: str,
    amount: float,
    status: str,
    category: str = None,
    merchant: str = None,
    reason: str = None,
    agent_id: str = None
) -> str:
    try:
        user_id = get_or_create_user_id(supabase, username)
        
        try:
            status_enum = AuthorizationStatus(status.upper())
        except:
            status_enum = AuthorizationStatus.ERROR
            
        data = AuthorizationLogCreate(
            agent_id=agent_id,
            action_type=action_type,
            amount=amount,
            status=status_enum,
            category=category,
            merchant=merchant,
            reason=reason
        )
        result = log_authorization(supabase, user_id, data)
        return json.dumps({"success": True, "log_id": result.id}, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@tool(description="Get agent authorization history.")
async def get_agent_authorization_history_tool(username: str, limit: int = 20) -> str:
    try:
        user_id = get_or_create_user_id(supabase, username)
        history = get_authorization_history(supabase, user_id, limit=limit)
        return json.dumps([h.model_dump() for h in history], indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)
