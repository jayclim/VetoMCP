"""
Veto Budget MCP Server - Main entry point for Dedalus Labs marketplace.

This server provides budget management tools for AI agents,
enabling interaction with budget tracking, spending analysis,
and financial planning features.
"""

import asyncio

from dedalus_mcp import MCPServer

from tools.transactions import (
    add_transaction, delete_transaction, get_transactions
)
from tools.categories import (
    create_budget_category, get_budget_categories
)
from tools.dashboard import (
    get_dashboard_summary, get_spending_insights
)
from tools.rules import (
    create_budget_rule, get_budget_rules, delete_budget_rule, check_rule_compliance
)
from tools.local import (
    get_budget_methods, check_budget_for_purchase,
    suggest_budget_allocation, get_budget_health_score, project_monthly_spending
)
from tools.agent_guard_rails import (
    authorize_purchase,
    get_agent_spending_limits,
    assess_purchase_risk,
    validate_agent_action,
    set_agent_spending_limits,
    get_agent_settings_tool,
    get_cumulative_agent_spend_tool,
    log_agent_authorization,
    get_agent_authorization_history_tool,
)

# Create the MCP server
server = MCPServer("veto-budget")

# Collect all tools
server.collect(
    # Transactions
    add_transaction, delete_transaction, get_transactions,
    # Budget Categories
    create_budget_category, get_budget_categories,
    # Dashboard & Insights
    get_dashboard_summary, get_spending_insights,
    # Budget Rules
    create_budget_rule, get_budget_rules, delete_budget_rule, check_rule_compliance,
    # Local Tools (no database)
    get_budget_methods, check_budget_for_purchase,
    suggest_budget_allocation, get_budget_health_score, project_monthly_spending,
    # Agent Guard Rails (New)
    authorize_purchase,
    get_agent_spending_limits,
    assess_purchase_risk,
    validate_agent_action,
    set_agent_spending_limits,
    get_agent_settings_tool,
    get_cumulative_agent_spend_tool,
    log_agent_authorization,
    get_agent_authorization_history_tool,
)

def run():
    asyncio.run(server.serve(host="0.0.0.0"))

if __name__ == "__main__":
    run()
