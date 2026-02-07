"""Supabase database client for Veto Budget MCP Server."""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_url = os.getenv("SUPABASE_URL")
_supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not _supabase_url or not _supabase_key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")

supabase: Client = create_client(_supabase_url, _supabase_key)


def ensure_user(username: str) -> str:
    """Ensure user exists, create if not. Returns user ID."""
    result = supabase.table("veto_users").select("id").eq("username", username).execute()
    
    if result.data:
        return result.data[0]["id"]
    
    # Create new user
    new_user = supabase.table("veto_users").insert({"username": username}).execute()
    return new_user.data[0]["id"]
