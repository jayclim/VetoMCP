"""Local tools - pure calculations without database access."""

from dedalus_mcp import tool


@tool(description="Returns a list of popular budget methods with descriptions. Useful for onboarding users.")
async def get_budget_methods() -> str:
    methods = [
        ("50/30/20 Rule", "50% needs, 30% wants, 20% savings. Simple and balanced."),
        ("80/20 Rule", "Pay yourself first - save 20%, spend 80%. Focus on savings."),
        ("Pay Yourself First", "Prioritize savings/investments before spending."),
        ("Zero-Based Budget", "Every dollar has a job. Income minus expenses equals zero."),
        ("Envelope System", "Allocate cash to categories. When empty, stop spending."),
    ]
    
    lines = ["**Popular Budget Methods:**", ""]
    for name, desc in methods:
        lines.append(f"**{name}**")
        lines.append(f"  {desc}")
        lines.append("")
    
    return "\n".join(lines)


@tool(description="Check if a purchase is within budget. Returns APPROVE/DENY/CAUTION recommendation.")
async def check_budget_for_purchase(
    budget_limit: float,
    amount_spent: float,
    purchase_amount: float,
    category: str = "General"
) -> str:
    remaining = budget_limit - amount_spent
    after_purchase = remaining - purchase_amount
    
    if purchase_amount > remaining:
        return f"❌ **DENY** - This ${purchase_amount} purchase would exceed your {category} budget by ${purchase_amount - remaining:.2f}."
    
    utilization_after = ((amount_spent + purchase_amount) / budget_limit) * 100
    
    if utilization_after >= 90:
        return f"⚠️ **CAUTION** - This purchase is within budget but would use {utilization_after:.1f}% of your {category} budget. Only ${after_purchase:.2f} would remain."
    
    return f"✅ **APPROVE** - This ${purchase_amount} purchase is within your {category} budget. You'll have ${after_purchase:.2f} remaining ({100 - utilization_after:.1f}% available)."


@tool(description="Suggest budget allocations based on income. method: '50/30/20', '80/20', or 'pay_yourself_first'")
async def suggest_budget_allocation(
    monthly_income: float,
    method: str = "50/30/20"
) -> str:
    lines = [f"**Budget Allocation for ${monthly_income:.2f}/month**", f"Method: {method}", ""]
    
    if method == "50/30/20":
        needs = monthly_income * 0.50
        wants = monthly_income * 0.30
        savings = monthly_income * 0.20
        lines.extend([
            f"**Needs (50%):** ${needs:.2f}",
            f"**Wants (30%):** ${wants:.2f}",
            f"**Savings (20%):** ${savings:.2f}",
        ])
    elif method == "80/20":
        savings = monthly_income * 0.20
        spending = monthly_income * 0.80
        lines.extend([
            f"**Savings First (20%):** ${savings:.2f}",
            f"**Everything Else (80%):** ${spending:.2f}",
        ])
    elif method == "pay_yourself_first":
        investment = monthly_income * 0.15
        emergency = monthly_income * 0.10
        remaining = monthly_income * 0.75
        lines.extend([
            f"**Investments (15%):** ${investment:.2f}",
            f"**Emergency Fund (10%):** ${emergency:.2f}",
            f"**Living Expenses (75%):** ${remaining:.2f}",
        ])
    else:
        return f"Unknown method: {method}. Use: 50/30/20, 80/20, or pay_yourself_first"
    
    return "\n".join(lines)


@tool(description="Calculate a 0-100 financial health score with grade (A-F).")
async def get_budget_health_score(
    total_income: float,
    total_expenses: float,
    categories_over_budget: int = 0,
    has_emergency_fund: bool = False,
    debt_to_income_ratio: float = 0.0
) -> str:
    score = 50
    breakdown = []
    
    if total_income > 0:
        savings_rate = ((total_income - total_expenses) / total_income) * 100
        if savings_rate >= 20:
            score += 30
            breakdown.append(f"+30: Excellent savings rate ({savings_rate:.1f}%)")
        elif savings_rate >= 10:
            score += 20
            breakdown.append(f"+20: Good savings rate ({savings_rate:.1f}%)")
        elif savings_rate > 0:
            score += 10
            breakdown.append(f"+10: Some savings ({savings_rate:.1f}%)")
        else:
            score -= 20
            breakdown.append(f"-20: Negative savings ({savings_rate:.1f}%)")
    
    if categories_over_budget > 0:
        penalty = min(categories_over_budget * 5, 20)
        score -= penalty
        breakdown.append(f"-{penalty}: {categories_over_budget} categories over budget")
    else:
        score += 10
        breakdown.append("+10: All categories within budget")
    
    if has_emergency_fund:
        score += 10
        breakdown.append("+10: Has emergency fund")
    
    if debt_to_income_ratio > 0.50:
        score -= 20
        breakdown.append(f"-20: High DTI ratio ({debt_to_income_ratio:.0%})")
    elif debt_to_income_ratio > 0.36:
        score -= 10
        breakdown.append(f"-10: Elevated DTI ratio ({debt_to_income_ratio:.0%})")
    
    score = max(0, min(100, score))
    
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"
    
    lines = [f"**Budget Health Score: {score}/100 (Grade: {grade})**", "", "**Breakdown:**"]
    lines.extend([f"  {b}" for b in breakdown])
    
    return "\n".join(lines)


@tool(description="Project end-of-month spending based on current pace.")
async def project_monthly_spending(
    current_day_of_month: int,
    days_in_month: int,
    amount_spent_so_far: float,
    budget_limit: float
) -> str:
    if current_day_of_month <= 0:
        return "Invalid day of month."
    
    daily_rate = amount_spent_so_far / current_day_of_month
    projected = daily_rate * days_in_month
    
    remaining_days = days_in_month - current_day_of_month
    remaining_budget = budget_limit - amount_spent_so_far
    safe_daily = remaining_budget / remaining_days if remaining_days > 0 else 0
    
    lines = [
        "**Monthly Spending Projection**",
        f"Day {current_day_of_month} of {days_in_month}",
        "",
        f"**Spent so far:** ${amount_spent_so_far:.2f}",
        f"**Daily rate:** ${daily_rate:.2f}/day",
        f"**Projected total:** ${projected:.2f}",
        f"**Budget:** ${budget_limit:.2f}",
        ""
    ]
    
    if projected > budget_limit:
        over = projected - budget_limit
        lines.append(f"⚠️ **At this pace, you'll be ${over:.2f} over budget!**")
        if remaining_days > 0:
            lines.append(f"💡 To stay on budget, spend max ${safe_daily:.2f}/day for remaining {remaining_days} days.")
    else:
        under = budget_limit - projected
        lines.append(f"✅ **On track! Projected to be ${under:.2f} under budget.**")
    
    return "\n".join(lines)
