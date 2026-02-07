import json
from typing import Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP, Context
from sqlmodel import Session, create_engine, select

from database import engine
from models import (
    TransactionType,
    TransactionCreate,
    BudgetCategoryCreate,
    RuleType,
    BudgetRuleCreate,
)
from services import transaction_service, budget_service, budget_rule_service

# Initialize FastMCP server
mcp = FastMCP("Veto Budget Agent")

def get_session():
    return Session(engine)

# ══════════════════════════════════════════════════════════════════════════════
# SERVER TOOLS (require database access)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def add_transaction(
    amount: float,
    description: str,
    category: str,
    transaction_type: str,
    username: str = "default_user",
    date: Optional[datetime] = None,
) -> str:
    """
    Record a new financial transaction (expense or income).
    
    Args:
        amount: The monetary value of the transaction.
        description: A brief description of what the transaction was for.
        category: The budget category (e.g., "Food", "Transport").
        transaction_type: Either "expense" or "income".
        username: The user's identifier (defaults to "default_user").
        date: Optional date of the transaction (defaults to now).
    """
    try:
        try:
            type_enum = TransactionType(transaction_type.lower())
        except ValueError:
            return f"Error: Invalid transaction type '{transaction_type}'. Must be 'expense' or 'income'."

        with get_session() as session:
            tx_data = TransactionCreate(
                amount=amount,
                description=description,
                category=category,
                transaction_type=type_enum,
                date=date
            )
            result = transaction_service.add_transaction(session, username, tx_data)
            return f"Transaction added: {result.description} ({result.amount}) - ID: {result.id}"
    except Exception as e:
        return f"Error adding transaction: {str(e)}"

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
def get_dashboard_summary(username: str = "default_user") -> str:
    """Get a financial dashboard summary including income, expenses, and category breakdowns."""
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

# ── Budget Rules Server Tools ────────────────────────────────────────────────

@mcp.tool()
def create_budget_rule(
    rule_type: str,
    name: str,
    config: str,
    username: str = "default_user"
) -> str:
    """
    Create a new budget rule.
    
    Args:
        rule_type: One of "percentage_allocation", "category_limit", "savings_goal", "spending_alert"
        name: A friendly name for the rule (e.g., "50/30/20 Rule")
        config: JSON string with rule configuration. Examples:
            - percentage_allocation: {"needs": 50, "wants": 30, "savings": 20}
            - category_limit: {"category": "Food", "limit": 500}
            - savings_goal: {"goal": 1000}
            - spending_alert: {"category": "Entertainment", "threshold": 200}
        username: The user's identifier.
    """
    try:
        try:
            type_enum = RuleType(rule_type.lower())
        except ValueError:
            valid = ", ".join([r.value for r in RuleType])
            return f"Error: Invalid rule type '{rule_type}'. Must be one of: {valid}"

        # Validate JSON
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

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
def check_rule_compliance(username: str = "default_user") -> str:
    """
    Check if the user is following their active budget rules.
    Returns compliance status for each rule.
    """
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
                
                # Add details based on rule type
                if rule.get("rule_type") == "percentage_allocation":
                    lines.append(f"  Target savings: {rule.get('target_savings_pct')}% | Actual: {rule.get('actual_savings_pct')}%")
                elif rule.get("rule_type") == "category_limit":
                    lines.append(f"  {rule.get('category')}: ${rule.get('spent')} / ${rule.get('limit')}")
                elif rule.get("rule_type") == "savings_goal":
                    lines.append(f"  Saved: ${rule.get('saved')} / Goal: ${rule.get('goal')}")
                elif rule.get("rule_type") == "spending_alert":
                    alert = "🔔 ALERT TRIGGERED" if rule.get("alert_triggered") else "No alert"
                    lines.append(f"  {rule.get('category')}: ${rule.get('spent')} (threshold: ${rule.get('threshold')}) - {alert}")
                lines.append("")
            
            return "\n".join(lines)
    except Exception as e:
        return f"Error checking compliance: {str(e)}"

@mcp.tool()
def get_spending_insights(username: str = "default_user") -> str:
    """
    Get AI-friendly spending insights and patterns.
    Useful for providing proactive budget advice.
    """
    try:
        with get_session() as session:
            summary = budget_service.get_dashboard_summary(session, username)
            
            insights = []
            
            # Overall health
            if summary.total_income > 0:
                savings_rate = ((summary.total_income - summary.total_expenses) / summary.total_income) * 100
                if savings_rate >= 20:
                    insights.append(f"✅ Great savings rate of {savings_rate:.1f}%!")
                elif savings_rate >= 10:
                    insights.append(f"⚠️ Savings rate is {savings_rate:.1f}%. Consider increasing to 20%.")
                elif savings_rate > 0:
                    insights.append(f"⚠️ Low savings rate of {savings_rate:.1f}%. Try to save more.")
                else:
                    insights.append(f"❌ Negative savings rate ({savings_rate:.1f}%). Spending exceeds income!")
            else:
                insights.append("ℹ️ No income recorded yet.")
            
            # Category analysis
            if summary.categories:
                # Find categories over budget
                over_budget = [c for c in summary.categories if c.remaining is not None and c.remaining < 0]
                if over_budget:
                    for c in over_budget:
                        insights.append(f"🚨 {c.category} is ${abs(c.remaining):.2f} over budget!")
                
                # Find top spending category
                if summary.categories:
                    top_cat = max(summary.categories, key=lambda x: x.total_spent)
                    if top_cat.total_spent > 0:
                        insights.append(f"💰 Highest spending: {top_cat.category} (${top_cat.total_spent:.2f})")
            
            if not insights:
                return "No spending data available yet."
            
            return "**Spending Insights**\n" + "\n".join(insights)
    except Exception as e:
        return f"Error generating insights: {str(e)}"

# ══════════════════════════════════════════════════════════════════════════════
# LOCAL TOOLS (no database, pure logic - for client-side AI decisions)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_budget_methods() -> str:
    """
    Returns a list of popular budget methods with descriptions.
    Useful for guiding users during onboarding when choosing a budget strategy.
    This is a LOCAL TOOL - no database access required.
    """
    methods = [
        {
            "name": "50/30/20 Rule",
            "description": "Allocate 50% of income to needs (rent, groceries, utilities), 30% to wants (entertainment, dining out), and 20% to savings and debt repayment.",
            "best_for": "Beginners who want a simple framework.",
            "config_template": '{"needs": 50, "wants": 30, "savings": 20}'
        },
        {
            "name": "Zero-Based Budgeting",
            "description": "Assign every dollar a specific purpose until income minus expenses equals zero. Every dollar has a job.",
            "best_for": "Detail-oriented planners who want full control.",
            "config_template": '{"method": "zero_based"}'
        },
        {
            "name": "Envelope System",
            "description": "Allocate cash to category 'envelopes'. When an envelope is empty, no more spending in that category.",
            "best_for": "People who struggle with overspending in specific categories.",
            "config_template": '{"categories": ["Groceries", "Entertainment", "Dining Out"]}'
        },
        {
            "name": "Pay Yourself First",
            "description": "Automatically save a fixed percentage of income before spending on anything else.",
            "best_for": "Those prioritizing savings and wealth building.",
            "config_template": '{"savings_percent": 20}'
        },
        {
            "name": "80/20 Rule",
            "description": "Save 20% of income, spend 80% however you want. Simple and flexible.",
            "best_for": "People who want minimal budgeting effort.",
            "config_template": '{"savings": 20, "spending": 80}'
        },
        {
            "name": "Values-Based Budgeting",
            "description": "Prioritize spending on what matters most to you. Cut ruthlessly elsewhere.",
            "best_for": "Those who want alignment between money and values.",
            "config_template": '{"priorities": ["Health", "Education", "Experiences"]}'
        }
    ]
    return json.dumps(methods, indent=2)

@mcp.tool()
def check_budget_for_purchase(
    budget_limit: float,
    amount_spent: float,
    purchase_amount: float,
    category: str = "General"
) -> str:
    """
    Check if a purchase is within budget.
    LOCAL TOOL - no database access, pure calculation.
    
    Args:
        budget_limit: The monthly budget limit for this category.
        amount_spent: How much has already been spent in this category.
        purchase_amount: The cost of the proposed purchase.
        category: The category name (for display purposes).
    
    Returns:
        A recommendation on whether to proceed with the purchase.
    """
    remaining = budget_limit - amount_spent
    after_purchase = remaining - purchase_amount
    
    result = {
        "category": category,
        "budget_limit": budget_limit,
        "already_spent": amount_spent,
        "remaining_before": remaining,
        "purchase_amount": purchase_amount,
        "remaining_after": after_purchase,
    }
    
    if purchase_amount > remaining:
        result["recommendation"] = "DENY"
        result["reason"] = f"This purchase of ${purchase_amount:.2f} would exceed your {category} budget by ${abs(after_purchase):.2f}."
    elif after_purchase < (budget_limit * 0.1):
        result["recommendation"] = "CAUTION"
        result["reason"] = f"This purchase is within budget, but would leave only ${after_purchase:.2f} ({(after_purchase/budget_limit)*100:.1f}%) remaining."
    else:
        result["recommendation"] = "APPROVE"
        result["reason"] = f"This purchase is within budget. You'll have ${after_purchase:.2f} remaining."
    
    return json.dumps(result, indent=2)

@mcp.tool()
def suggest_budget_allocation(
    monthly_income: float,
    method: str = "50/30/20"
) -> str:
    """
    Suggest budget allocations based on income and chosen method.
    LOCAL TOOL - no database access.
    
    Args:
        monthly_income: The user's monthly income.
        method: Budget method to use ("50/30/20", "80/20", "pay_yourself_first").
    """
    allocations = {}
    
    if method == "50/30/20":
        allocations = {
            "needs": {"percent": 50, "amount": monthly_income * 0.50},
            "wants": {"percent": 30, "amount": monthly_income * 0.30},
            "savings": {"percent": 20, "amount": monthly_income * 0.20},
        }
    elif method == "80/20":
        allocations = {
            "spending": {"percent": 80, "amount": monthly_income * 0.80},
            "savings": {"percent": 20, "amount": monthly_income * 0.20},
        }
    elif method == "pay_yourself_first":
        # Default to 25% savings for pay yourself first
        allocations = {
            "savings": {"percent": 25, "amount": monthly_income * 0.25},
            "remainder": {"percent": 75, "amount": monthly_income * 0.75},
        }
    else:
        return json.dumps({"error": f"Unknown method: {method}. Try '50/30/20', '80/20', or 'pay_yourself_first'."})
    
    result = {
        "monthly_income": monthly_income,
        "method": method,
        "allocations": allocations
    }
    return json.dumps(result, indent=2)

@mcp.tool()
def get_budget_health_score(
    total_income: float,
    total_expenses: float,
    categories_over_budget: int = 0,
    has_emergency_fund: bool = False,
    debt_to_income_ratio: float = 0.0
) -> str:
    """
    Calculate a 0-100 financial health score.
    LOCAL TOOL - no database access.
    
    Args:
        total_income: Total monthly income.
        total_expenses: Total monthly expenses.
        categories_over_budget: Number of categories currently over budget.
        has_emergency_fund: Whether user has 3+ months of expenses saved.
        debt_to_income_ratio: Monthly debt payments / monthly income (0.0 to 1.0).
    """
    score = 50  # Start at neutral
    
    # Savings rate impact (-20 to +30)
    if total_income > 0:
        savings_rate = (total_income - total_expenses) / total_income
        if savings_rate >= 0.20:
            score += 30
        elif savings_rate >= 0.10:
            score += 15
        elif savings_rate >= 0:
            score += 5
        else:
            score -= 20  # Spending more than earning
    
    # Categories over budget (-15)
    score -= min(categories_over_budget * 5, 15)
    
    # Emergency fund (+15)
    if has_emergency_fund:
        score += 15
    
    # Debt-to-income ratio (-20 to 0)
    if debt_to_income_ratio > 0.50:
        score -= 20
    elif debt_to_income_ratio > 0.30:
        score -= 10
    elif debt_to_income_ratio > 0.15:
        score -= 5
    
    # Clamp score
    score = max(0, min(100, score))
    
    # Determine grade
    if score >= 80:
        grade = "A"
        message = "Excellent financial health! Keep it up."
    elif score >= 60:
        grade = "B"
        message = "Good financial health with room for improvement."
    elif score >= 40:
        grade = "C"
        message = "Fair financial health. Consider reviewing your budget."
    elif score >= 20:
        grade = "D"
        message = "Poor financial health. Immediate action recommended."
    else:
        grade = "F"
        message = "Critical financial situation. Seek professional advice."
    
    result = {
        "score": score,
        "grade": grade,
        "message": message,
        "factors": {
            "savings_rate_impact": "positive" if total_income > 0 and (total_income - total_expenses) > 0 else "negative",
            "over_budget_categories": categories_over_budget,
            "emergency_fund": has_emergency_fund,
            "debt_to_income": debt_to_income_ratio
        }
    }
    return json.dumps(result, indent=2)

@mcp.tool()
def project_monthly_spending(
    current_day_of_month: int,
    days_in_month: int,
    amount_spent_so_far: float,
    budget_limit: float
) -> str:
    """
    Project end-of-month spending based on current pace.
    LOCAL TOOL - no database access.
    
    Args:
        current_day_of_month: What day of the month it is (1-31).
        days_in_month: Total days in this month (28-31).
        amount_spent_so_far: How much has been spent so far this month.
        budget_limit: The monthly budget limit.
    """
    if current_day_of_month <= 0:
        return json.dumps({"error": "current_day_of_month must be positive"})
    
    daily_rate = amount_spent_so_far / current_day_of_month
    projected_total = daily_rate * days_in_month
    difference = budget_limit - projected_total
    
    result = {
        "current_day": current_day_of_month,
        "days_in_month": days_in_month,
        "spent_so_far": amount_spent_so_far,
        "daily_average": round(daily_rate, 2),
        "projected_month_total": round(projected_total, 2),
        "budget_limit": budget_limit,
        "projected_difference": round(difference, 2),
    }
    
    if difference >= 0:
        result["status"] = "ON_TRACK"
        result["message"] = f"At current pace, you'll finish ${difference:.2f} under budget."
    else:
        result["status"] = "OVER_BUDGET"
        result["message"] = f"Warning: At current pace, you'll be ${abs(difference):.2f} over budget."
        # Calculate how much to reduce daily spending
        remaining_days = days_in_month - current_day_of_month
        if remaining_days > 0:
            remaining_budget = budget_limit - amount_spent_so_far
            safe_daily = remaining_budget / remaining_days
            result["recommended_daily_limit"] = round(max(0, safe_daily), 2)
    
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    mcp.run()

