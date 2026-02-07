/**
 * Supabase database layer for Veto Budget MCP Server
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";

// Initialize Supabase client
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables");
  process.exit(1);
}

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseKey);

// Types
export interface Transaction {
  id: string;
  user_id: string;
  amount: number;
  description: string;
  category: string;
  transaction_type: "income" | "expense";
  date: string;
  created_at: string;
}

export interface BudgetCategory {
  id: string;
  user_id: string;
  name: string;
  monthly_limit: number;
  created_at: string;
}

export interface BudgetRule {
  id: string;
  user_id: string;
  rule_type: "percentage_allocation" | "category_limit" | "savings_goal" | "spending_alert";
  name: string;
  config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface User {
  id: string;
  username: string;
  created_at: string;
}

// Ensure user exists (create if not)
export async function ensureUser(username: string): Promise<string> {
  // Check if user exists
  const { data: existing } = await supabase
    .from("veto_users")
    .select("id")
    .eq("username", username)
    .single();

  if (existing) return existing.id;

  // Create new user
  const { data: newUser, error } = await supabase
    .from("veto_users")
    .insert({ username })
    .select("id")
    .single();

  if (error) throw new Error(`Failed to create user: ${error.message}`);
  return newUser.id;
}
