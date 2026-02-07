"""Dashboard and insights tools for Veto Budget MCP Server."""

from dedalus_mcp import tool
from database import supabase, ensure_user


@tool(description="Get a financial dashboard summary including income, expenses, and category breakdowns.")
async def get_dashboard_summary(username: str = "default_user") -> str:
    try:
        user_id = ensure_user(username)
        
        tx_result = supabase.table("veto_transactions").select("*").eq("user_id", user_id).execute()
        txs = tx_result.data or []
        
        total_income = 0
        total_expenses = 0
        category_spending = {}
        
        for tx in txs:
            amount = float(tx["amount"])
            if tx["transaction_type"] == "income":
                total_income += amount
            else:
                total_expenses += amount
                cat = tx["category"]
                category_spending[cat] = category_spending.get(cat, 0) + amount
        
        net = total_income - total_expenses
        
        limits_result = supabase.table("veto_budget_categories").select("name, monthly_limit").eq("user_id", user_id).execute()
        limit_map = {b["name"]: float(b["monthly_limit"]) for b in (limits_result.data or [])}
        
        lines = [
            "**Dashboard Summary**",
            f"Total Income: ${total_income:.2f}",
            f"Total Expenses: ${total_expenses:.2f}",
            f"Net: ${net:.2f}",
            "",
            "**Category Breakdown:**"
        ]
        
        for category, spent in category_spending.items():
            line = f"- {category}: ${spent:.2f}"
            if category in limit_map:
                remaining = limit_map[category] - spent
                line += f" / ${limit_map[category]} (Remaining: ${remaining:.2f})"
            lines.append(line)
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching dashboard: {str(e)}"


@tool(description="Get AI-friendly spending insights and patterns. Useful for proactive budget advice.")
async def get_spending_insights(username: str = "default_user") -> str:
    try:
        user_id = ensure_user(username)
        
        tx_result = supabase.table("veto_transactions").select("*").eq("user_id", user_id).execute()
        txs = tx_result.data or []
        
        total_income = 0
        total_expenses = 0
        category_spending = {}
        
        for tx in txs:
            amount = float(tx["amount"])
            if tx["transaction_type"] == "income":
                total_income += amount
            else:
                total_expenses += amount
                cat = tx["category"]
                category_spending[cat] = category_spending.get(cat, 0) + amount
        
        insights = []
        
        if total_income > 0:
            savings_rate = ((total_income - total_expenses) / total_income) * 100
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
        
        limits_result = supabase.table("veto_budget_categories").select("name, monthly_limit").eq("user_id", user_id).execute()
        limit_map = {b["name"]: float(b["monthly_limit"]) for b in (limits_result.data or [])}
        
        for category, spent in category_spending.items():
            if category in limit_map and spent > limit_map[category]:
                over = spent - limit_map[category]
                insights.append(f"🚨 {category} is ${over:.2f} over budget!")
        
        if category_spending:
            sorted_cats = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
            if sorted_cats[0][1] > 0:
                insights.append(f"💰 Highest spending: {sorted_cats[0][0]} (${sorted_cats[0][1]:.2f})")
        
        if not insights:
            return "No spending data available yet."
        
        return "**Spending Insights**\n" + "\n".join(insights)
    except Exception as e:
        return f"Error generating insights: {str(e)}"
