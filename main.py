"""
Veto Budget Agent - Dedalus MCP Server

This is the entry point for Dedalus Labs MCP deployment.
The server provides budget management tools for AI agents.
"""
import os
import asyncio
from dedalus_mcp import MCPServer, tool
from dedalus_mcp.server import TransportSecuritySettings
from sqlmodel import Session

from database import engine
from models import (
    TransactionType,
    TransactionCreate,
    BudgetCategoryCreate,
    RuleType,
    BudgetRuleCreate,
)
from services import transaction_service, budget_service, budget_rule_service
import json
from typing import Optional
from datetime import datetime


def get_session():
    return Session(engine)


# ══════════════════════════════════════════════════════════════════════════════
# SERVER TOOLS (require database access)
# ══════════════════════════════════════════════════════════════════════════════

@tool(description="Record a new financial transaction (expense or income)")
def add_transaction(
    amount: float,
    description: str,
    category: str,
    transaction_type: str,
    username: str = "default_user",
    date: Optional[str] = None,
) -> str:
    """Record a new financial transaction."""
    try:
        try:
            type_enum = TransactionType(transaction_type.lower())
        except ValueError:
            return f"Error: Invalid transaction type '{transaction_type}'. Must be 'expense' or 'income'."

        parsed_date = None
        if date:
            parsed_date = datetime.fromisoformat(date)

        with get_session() as session:
            tx_data = TransactionCreate(
                amount=amount,
                description=description,
                category=category,
                transaction_type=type_enum,
                date=parsed_date
            )
            result = transaction_service.add_transaction(session, username, tx_data)
            return f"Transaction added: {result.description} ({result.amount}) - ID: {result.id}"
    except Exception as e:
        return f"Error adding transaction: {str(e)}"


@tool(description="Delete a transaction by its ID")
def delete_transaction(transaction_id: str, username: str = "default_user") -> str:
    """Delete a transaction by its ID."""
    try:
        with get_session() as session:
            success = transaction_service.delete_transaction(session, username, transaction_id)
            if success:
                return f"Transaction {transaction_id} deleted successfully."
            else:
                return f"Transaction {transaction_id} not found or access denied."
    except Exception as e:
        return f"Error deleting transaction: {str(e)}"


@tool(description="List recent transactions with optional filtering")
def get_transactions(
    username: str = "default_user",
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    limit: int = 10
) -> str:
    """List recent transactions with optional filtering."""
    try:
        type_enum = None
        if transaction_type:
            try:
                type_enum = TransactionType(transaction_type.lower())
            except ValueError:
                return f"Error: Invalid transaction type '{transaction_type}'."

        with get_session() as session:
            txs = transaction_service.get_transactions(
                session, 
                username, 
                category=category, 
                transaction_type=type_enum
            )
            
            if not txs:
                return "No transactions found."
            
            txs = txs[:limit]
            
            output = [f"Found {len(txs)} transactions:"]
            for tx in txs:
                date_str = tx.date.strftime("%Y-%m-%d") if tx.date else "N/A"
                output.append(f"- [{date_str}] {tx.description}: ${tx.amount} ({tx.category}) [{tx.transaction_type.value}] ID: {tx.id}")
            
            return "\n".join(output)
    except Exception as e:
        return f"Error fetching transactions: {str(e)}"


@tool(description="Create a new budget category with a monthly spending limit")
def create_budget_category(
    name: str,
    monthly_limit: float,
    username: str = "default_user"
) -> str:
    """Create a new budget category with a monthly spending limit."""
    try:
        with get_session() as session:
            cat_data = BudgetCategoryCreate(name=name, monthly_limit=monthly_limit)
            result = budget_service.create_category(session, username, cat_data)
            return f"Category '{result.name}' created with limit ${result.monthly_limit}."
    except Exception as e:
        return f"Error creating category: {str(e)}"


@tool(description="List all budget categories and their limits")
def get_budget_categories(username: str = "default_user") -> str:
    """List all budget categories and their limits."""
    try:
        with get_session() as session:
            cats = budget_service.get_categories(session, username)
            if not cats:
                return "No categories set."
            
            output = ["Budget Categories:"]
            for c in cats:
                output.append(f"- {c.name}: ${c.monthly_limit}/month")
            return "\n".join(output)
    except Exception as e:
        return f"Error fetching categories: {str(e)}"


@tool(description="Get a financial dashboard summary including income, expenses, and category breakdowns")
def get_dashboard_summary(username: str = "default_user") -> str:
    """Get a financial dashboard summary."""
    try:
        with get_session() as session:
            summary = budget_service.get_dashboard_summary(session, username)
            
            lines = [
                "**Dashboard Summary**",
                f"Total Income: ${summary.total_income:.2f}",
                f"Total Expenses: ${summary.total_expenses:.2f}",
                f"Net: ${summary.net:.2f}",
                "",
                "**Category Breakdown:**"
            ]
            
            for cat in summary.categories:
                limit_str = f" / ${cat.budget_limit}" if cat.budget_limit else ""
                remaining_str = f" (Remaining: ${cat.remaining:.2f})" if cat.remaining is not None else ""
                lines.append(f"- {cat.category}: ${cat.total_spent:.2f}{limit_str}{remaining_str}")
                
            return "\n".join(lines)
    except Exception as e:
        return f"Error fetching dashboard: {str(e)}"


@tool(description="Create a new budget rule for automated budget management")
def create_budget_rule(
    rule_type: str,
    name: str,
    config: str,
    username: str = "default_user"
) -> str:
    """Create a new budget rule."""
    try:
        try:
            type_enum = RuleType(rule_type.lower())
        except ValueError:
            valid = ", ".join([r.value for r in RuleType])
            return f"Error: Invalid rule type '{rule_type}'. Must be one of: {valid}"

        try:
            json.loads(config)
        except json.JSONDecodeError:
            return "Error: config must be a valid JSON string."

        with get_session() as session:
            rule_data = BudgetRuleCreate(
                rule_type=type_enum,
                name=name,
                config=config
            )
            result = budget_rule_service.create_rule(session, username, rule_data)
            return f"Budget rule '{result.name}' created successfully (ID: {result.id})."
    except Exception as e:
        return f"Error creating budget rule: {str(e)}"


@tool(description="List all active budget rules for a user")
def get_budget_rules(username: str = "default_user") -> str:
    """List all active budget rules for a user."""
    try:
        with get_session() as session:
            rules = budget_rule_service.get_rules(session, username)
            if not rules:
                return "No budget rules set."
            
            output = ["Active Budget Rules:"]
            for r in rules:
                output.append(f"- [{r.rule_type.value}] {r.name} (ID: {r.id})")
                output.append(f"  Config: {r.config}")
            return "\n".join(output)
    except Exception as e:
        return f"Error fetching budget rules: {str(e)}"


@tool(description="Delete a budget rule by its ID")
def delete_budget_rule(rule_id: str, username: str = "default_user") -> str:
    """Delete a budget rule by its ID."""
    try:
        with get_session() as session:
            success = budget_rule_service.delete_rule(session, username, rule_id)
            if success:
                return f"Budget rule {rule_id} deleted successfully."
            else:
                return f"Budget rule {rule_id} not found or access denied."
    except Exception as e:
        return f"Error deleting budget rule: {str(e)}"


@tool(description="Check if the user is following their active budget rules")
def check_rule_compliance(username: str = "default_user") -> str:
    """Check if the user is following their active budget rules."""
    try:
        with get_session() as session:
            result = budget_rule_service.check_rule_compliance(session, username)
            
            if result.get("status") == "no_rules":
                return result.get("message", "No active budget rules found.")
            
            lines = ["**Budget Rule Compliance Report**", ""]
            for rule in result.get("rules", []):
                status = "✅ Compliant" if rule.get("compliant") else "❌ Not Compliant"
                if rule.get("compliant") is None:
                    status = "⚠️ Cannot determine"
                lines.append(f"**{rule.get('rule_name')}** ({rule.get('rule_type')}): {status}")
                lines.append("")
            
            return "\n".join(lines)
    except Exception as e:
        return f"Error checking compliance: {str(e)}"


@tool(description="Get AI-friendly spending insights and patterns")
def get_spending_insights(username: str = "default_user") -> str:
    """Get AI-friendly spending insights and patterns."""
    try:
        with get_session() as session:
            summary = budget_service.get_dashboard_summary(session, username)
            
            insights = []
            
            if summary.total_income > 0:
                savings_rate = ((summary.total_income - summary.total_expenses) / summary.total_income) * 100
                if savings_rate >= 20:
                    insights.append(f"✅ Great savings rate of {savings_rate:.1f}%!")
                elif savings_rate >= 10:
                    insights.append(f"⚠️ Savings rate is {savings_rate:.1f}%.")
                else:
                    insights.append(f"❌ Low savings rate ({savings_rate:.1f}%).")
            else:
                insights.append("ℹ️ No income recorded yet.")
            
            if not insights:
                return "No spending data available yet."
            
            return "**Spending Insights**\n" + "\n".join(insights)
    except Exception as e:
        return f"Error generating insights: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# LOCAL TOOLS (no database, pure logic)
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
    """Suggest budget allocations."""
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
    
    return json.dumps({"monthly_income": monthly_income, "method": method, "allocations": allocations}, indent=2)


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
    """Project end-of-month spending."""
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

# All tools to collect
all_tools = [
    add_transaction,
    delete_transaction,
    get_transactions,
    create_budget_category,
    get_budget_categories,
    get_dashboard_summary,
    create_budget_rule,
    get_budget_rules,
    delete_budget_rule,
    check_rule_compliance,
    get_spending_insights,
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
    await server.serve(port=8080)


if __name__ == "__main__":
    asyncio.run(main())
