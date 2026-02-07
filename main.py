"""
Veto Budget Agent - Dedalus MCP Server

Entry point for Dedalus Labs MCP deployment.
Provides budget management tools for AI agents.
"""
import os
import asyncio
import json
from typing import Optional

from dedalus_mcp import MCPServer, tool
from dedalus_mcp.server import TransportSecuritySettings


# ══════════════════════════════════════════════════════════════════════════════
# LOCAL TOOLS (no database, pure logic - always available)
# ══════════════════════════════════════════════════════════════════════════════

@tool(description="Returns a list of popular budget methods with descriptions")
def get_budget_methods() -> str:
    """Returns a list of popular budget methods."""
    methods = [
        {"name": "50/30/20 Rule", "description": "50% needs, 30% wants, 20% savings"},
        {"name": "Zero-Based", "description": "Assign every dollar a purpose"},
        {"name": "Envelope System", "description": "Physical/virtual spending envelopes"},
        {"name": "Pay Yourself First", "description": "Save first, spend what's left"},
        {"name": "80/20 Rule", "description": "Save 20%, spend 80%"},
    ]
    return json.dumps(methods, indent=2)


@tool(description="Check if a purchase is within budget")
def check_budget_for_purchase(
    budget_limit: float,
    amount_spent: float,
    purchase_amount: float,
    category: str = "General"
) -> str:
    """Check if a purchase is within budget."""
    remaining = budget_limit - amount_spent
    after_purchase = remaining - purchase_amount
    
    result = {
        "category": category,
        "budget_limit": budget_limit,
        "remaining_before": remaining,
        "purchase_amount": purchase_amount,
        "remaining_after": after_purchase,
    }
    
    if purchase_amount > remaining:
        result["recommendation"] = "DENY"
        result["reason"] = f"Would exceed budget by ${abs(after_purchase):.2f}"
    elif after_purchase < (budget_limit * 0.1):
        result["recommendation"] = "CAUTION"
        result["reason"] = f"Would leave only ${after_purchase:.2f} remaining"
    else:
        result["recommendation"] = "APPROVE"
        result["reason"] = f"Within budget. ${after_purchase:.2f} remaining"
    
    return json.dumps(result, indent=2)


@tool(description="Suggest budget allocations based on income and method")
def suggest_budget_allocation(monthly_income: float, method: str = "50/30/20") -> str:
    """Suggest budget allocations based on income."""
    if method == "50/30/20":
        allocations = {
            "needs": monthly_income * 0.50,
            "wants": monthly_income * 0.30,
            "savings": monthly_income * 0.20,
        }
    elif method == "80/20":
        allocations = {
            "spending": monthly_income * 0.80,
            "savings": monthly_income * 0.20,
        }
    else:
        return json.dumps({"error": f"Unknown method: {method}"})
    
    return json.dumps({
        "monthly_income": monthly_income,
        "method": method,
        "allocations": allocations
    }, indent=2)


@tool(description="Calculate a 0-100 financial health score")
def get_budget_health_score(
    total_income: float,
    total_expenses: float,
    categories_over_budget: int = 0,
    has_emergency_fund: bool = False
) -> str:
    """Calculate a financial health score."""
    score = 50
    
    if total_income > 0:
        savings_rate = (total_income - total_expenses) / total_income
        if savings_rate >= 0.20:
            score += 30
        elif savings_rate >= 0.10:
            score += 15
        elif savings_rate < 0:
            score -= 20
    
    score -= min(categories_over_budget * 5, 15)
    if has_emergency_fund:
        score += 15
    
    score = max(0, min(100, score))
    
    if score >= 80:
        grade, message = "A", "Excellent!"
    elif score >= 60:
        grade, message = "B", "Good with room for improvement"
    elif score >= 40:
        grade, message = "C", "Fair - review your budget"
    else:
        grade, message = "D", "Needs attention"
    
    return json.dumps({"score": score, "grade": grade, "message": message}, indent=2)


@tool(description="Project end-of-month spending based on current pace")
def project_monthly_spending(
    current_day_of_month: int,
    days_in_month: int,
    amount_spent_so_far: float,
    budget_limit: float
) -> str:
    """Project end-of-month spending based on current pace."""
    if current_day_of_month <= 0:
        return json.dumps({"error": "current_day_of_month must be positive"})
    
    daily_rate = amount_spent_so_far / current_day_of_month
    projected_total = daily_rate * days_in_month
    difference = budget_limit - projected_total
    
    result = {
        "projected_total": round(projected_total, 2),
        "budget_limit": budget_limit,
        "status": "ON_TRACK" if difference >= 0 else "OVER_BUDGET",
        "difference": round(abs(difference), 2),
    }
    
    return json.dumps(result, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# SERVER INITIALIZATION
# ══════════════════════════════════════════════════════════════════════════════

all_tools = [
    get_budget_methods,
    check_budget_for_purchase,
    suggest_budget_allocation,
    get_budget_health_score,
    project_monthly_spending,
]


def create_server() -> MCPServer:
    """Create MCP server with proper HTTP configuration."""
    as_url = os.getenv("DEDALUS_AS_URL", "https://as.dedaluslabs.ai")
    return MCPServer(
        name="veto-budget",
        http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
        streamable_http_stateless=True,
        authorization_server=as_url,
    )


async def main() -> None:
    """Start MCP server."""
    server = create_server()
    server.collect(*all_tools)
    port = int(os.getenv("PORT", "8080"))
    await server.serve(host="0.0.0.0", port=port)


if __name__ == "__main__":
    asyncio.run(main())
