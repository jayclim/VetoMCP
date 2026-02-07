"""Transaction management tools for Veto Budget MCP Server."""

import json
from dedalus_mcp import tool
from database import supabase, ensure_user


@tool(description="Record a new financial transaction (expense or income). transaction_type: 'income' or 'expense'")
async def add_transaction(
    amount: float,
    description: str,
    category: str = "Uncategorized",
    transaction_type: str = "expense",
    username: str = "default_user",
    date: str = None
) -> str:
    try:
        user_id = ensure_user(username)
        
        data = {
            "user_id": user_id,
            "amount": amount,
            "description": description,
            "category": category,
            "transaction_type": transaction_type,
        }
        if date:
            data["date"] = date
        
        result = supabase.table("veto_transactions").insert(data).execute()
        tx_id = result.data[0]["id"]
        return f"Transaction added: {description} (${amount}) - ID: {tx_id}"
    except Exception as e:
        return f"Error adding transaction: {str(e)}"


@tool(description="Delete a transaction by its ID.")
async def delete_transaction(transaction_id: str, username: str = "default_user") -> str:
    try:
        user_id = ensure_user(username)
        
        result = supabase.table("veto_transactions").delete().eq("id", transaction_id).eq("user_id", user_id).execute()
        
        if result.data:
            return f"Transaction {transaction_id} deleted successfully."
        return f"Transaction {transaction_id} not found or access denied."
    except Exception as e:
        return f"Error deleting transaction: {str(e)}"


@tool(description="List recent transactions with optional filtering by category and type.")
async def get_transactions(
    username: str = "default_user",
    category: str = None,
    transaction_type: str = None,
    limit: int = 10
) -> str:
    try:
        user_id = ensure_user(username)
        
        query = supabase.table("veto_transactions").select("*").eq("user_id", user_id).order("date", desc=True).limit(limit)
        
        if category:
            query = query.eq("category", category)
        if transaction_type:
            query = query.eq("transaction_type", transaction_type)
        
        result = query.execute()
        
        if not result.data:
            return "No transactions found."
        
        lines = [f"Found {len(result.data)} transactions:"]
        for tx in result.data:
            date_str = tx.get("date", "N/A")[:10] if tx.get("date") else "N/A"
            lines.append(f"- [{date_str}] {tx['description']}: ${tx['amount']} ({tx['category']}) [{tx['transaction_type']}] ID: {tx['id']}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching transactions: {str(e)}"
