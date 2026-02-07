"""Budget category management tools for Veto Budget MCP Server."""

from dedalus_mcp import tool
from database import supabase, ensure_user


@tool(description="Create a new budget category with a monthly spending limit.")
async def create_budget_category(
    name: str,
    monthly_limit: float,
    username: str = "default_user"
) -> str:
    try:
        user_id = ensure_user(username)
        
        supabase.table("veto_budget_categories").insert({
            "user_id": user_id,
            "name": name,
            "monthly_limit": monthly_limit,
        }).execute()
        
        return f"Category '{name}' created with limit ${monthly_limit}."
    except Exception as e:
        return f"Error creating category: {str(e)}"


@tool(description="List all budget categories and their limits.")
async def get_budget_categories(username: str = "default_user") -> str:
    try:
        user_id = ensure_user(username)
        
        result = supabase.table("veto_budget_categories").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            return "No categories set."
        
        lines = ["Budget Categories:"]
        for cat in result.data:
            lines.append(f"- {cat['name']}: ${cat['monthly_limit']}/month")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching categories: {str(e)}"
