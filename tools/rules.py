"""Budget rules management tools for Veto Budget MCP Server."""

import json
from dedalus_mcp import tool
from database import supabase, ensure_user


@tool(description="Create a new budget rule. rule_type: 'percentage_allocation', 'category_limit', 'savings_goal', or 'spending_alert'. config: JSON string with rule settings.")
async def create_budget_rule(
    rule_type: str,
    name: str,
    config: str,
    username: str = "default_user"
) -> str:
    try:
        config_obj = json.loads(config)
    except json.JSONDecodeError:
        return "Error: config must be a valid JSON string."
    
    try:
        user_id = ensure_user(username)
        
        result = supabase.table("veto_budget_rules").insert({
            "user_id": user_id,
            "rule_type": rule_type,
            "name": name,
            "config": config_obj,
        }).execute()
        
        rule_id = result.data[0]["id"]
        return f"Budget rule '{name}' created successfully (ID: {rule_id})."
    except Exception as e:
        return f"Error creating budget rule: {str(e)}"


@tool(description="List all active budget rules for a user.")
async def get_budget_rules(username: str = "default_user") -> str:
    try:
        user_id = ensure_user(username)
        
        result = supabase.table("veto_budget_rules").select("*").eq("user_id", user_id).eq("is_active", True).execute()
        
        if not result.data:
            return "No budget rules set."
        
        lines = ["Active Budget Rules:"]
        for rule in result.data:
            lines.append(f"- [{rule['rule_type']}] {rule['name']} (ID: {rule['id']})")
            lines.append(f"  Config: {json.dumps(rule['config'])}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching budget rules: {str(e)}"


@tool(description="Delete a budget rule by its ID.")
async def delete_budget_rule(rule_id: str, username: str = "default_user") -> str:
    try:
        user_id = ensure_user(username)
        
        result = supabase.table("veto_budget_rules").delete().eq("id", rule_id).eq("user_id", user_id).execute()
        
        if result.data:
            return f"Budget rule {rule_id} deleted successfully."
        return f"Budget rule {rule_id} not found or access denied."
    except Exception as e:
        return f"Error deleting budget rule: {str(e)}"


@tool(description="Check if the user is following their active budget rules. Returns compliance status for each rule.")
async def check_rule_compliance(username: str = "default_user") -> str:
    try:
        user_id = ensure_user(username)
        
        rules_result = supabase.table("veto_budget_rules").select("*").eq("user_id", user_id).eq("is_active", True).execute()
        rules = rules_result.data or []
        
        if not rules:
            return "No active budget rules found."
        
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
        
        lines = ["**Budget Rule Compliance Report**", ""]
        
        for rule in rules:
            config = rule["config"]
            status = "⚠️ Cannot determine"
            details = ""
            
            if rule["rule_type"] == "percentage_allocation":
                if total_income > 0 and "savings" in config:
                    target = config["savings"]
                    actual = ((total_income - total_expenses) / total_income) * 100
                    compliant = actual >= target
                    status = "✅ Compliant" if compliant else "❌ Not Compliant"
                    details = f"Target savings: {target}% | Actual: {actual:.1f}%"
            
            elif rule["rule_type"] == "category_limit":
                if "category" in config and "limit" in config:
                    spent = category_spending.get(config["category"], 0)
                    compliant = spent <= config["limit"]
                    status = "✅ Compliant" if compliant else "❌ Not Compliant"
                    details = f"{config['category']}: ${spent:.2f} / ${config['limit']}"
            
            elif rule["rule_type"] == "savings_goal":
                if "goal" in config:
                    saved = total_income - total_expenses
                    compliant = saved >= config["goal"]
                    status = "✅ Compliant" if compliant else "❌ Not Compliant"
                    details = f"Saved: ${saved:.2f} / Goal: ${config['goal']}"
            
            elif rule["rule_type"] == "spending_alert":
                if "category" in config and "threshold" in config:
                    spent = category_spending.get(config["category"], 0)
                    triggered = spent >= config["threshold"]
                    status = "🔔 ALERT TRIGGERED" if triggered else "✅ No alert"
                    details = f"{config['category']}: ${spent:.2f} (threshold: ${config['threshold']})"
            
            lines.append(f"**{rule['name']}** ({rule['rule_type']}): {status}")
            if details:
                lines.append(f"  {details}")
            lines.append("")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error checking compliance: {str(e)}"
