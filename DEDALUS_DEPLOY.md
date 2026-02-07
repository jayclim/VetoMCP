# Veto Budget MCP Server

An AI-powered budget management MCP server for the Dedalus Labs marketplace.

## Dedalus Deployment

### Prerequisites

1. Create an account at [dedaluslabs.ai](https://dedaluslabs.ai)
2. Get your API key from the [dashboard](https://www.dedaluslabs.ai/dashboard/api-keys)
3. Push this repository to GitHub

### Deployment Steps

1. **Go to the Dedalus Dashboard**
   - Visit [dedaluslabs.ai/dashboard/servers](https://www.dedaluslabs.ai/dashboard/servers)
   - Click "Add Server"

2. **Connect Repository**
   - Connect your GitHub account
   - Select this repository

3. **Configure Deployment**
   - **Entry Point**: `main.py` (Dedalus requires this exact filename)
   - **Port**: Server listens on port 8080 at `/mcp` endpoint
   - **Environment Variables**: Add any required secrets (e.g., `DEDALUS_API_KEY`)
   - Click "Deploy"

4. **Publish to Marketplace** (Optional)
   - Once deployed, click "Publish" to share with others

### Using the Deployed Server

```python
from dedalus import Dedalus

runner = Dedalus()
result = runner.run(
    "Check if I'm following my budget rules",
    mcp_servers=["your-org/veto-budget"]
)
```

## Server Structure

```
VetoMCP/
├── main.py            # Dedalus MCP entry point (REQUIRED name)
├── pyproject.toml     # Dependencies for Dedalus
├── fastapi_app.py     # FastAPI REST API (renamed)
├── mcp_server.py      # Original FastMCP server (local dev)
├── models.py          # SQLModel database models
├── database.py        # Database configuration
├── services/          # Business logic
└── routes/            # FastAPI routes
```

## Available Tools

### Transaction Tools
- `add_transaction` - Record expenses and income
- `delete_transaction` - Remove a transaction
- `get_transactions` - List and filter transactions

### Budget Tools
- `create_budget_category` - Set spending limits
- `get_budget_categories` - View all categories
- `get_dashboard_summary` - Financial overview

### Budget Rules
- `create_budget_rule` - Automated budget management
- `get_budget_rules` - List active rules
- `delete_budget_rule` - Remove a rule
- `check_rule_compliance` - Verify rule adherence
- `get_spending_insights` - AI-friendly analytics

### Local Tools (No Database)
- `get_budget_methods` - Popular budgeting strategies
- `check_budget_for_purchase` - Pre-purchase validation
- `suggest_budget_allocation` - Income allocation
- `get_budget_health_score` - Financial health score
- `project_monthly_spending` - Spending projections

## Local Development

```bash
# Install dependencies
pip install -e .

# Run the MCP server locally
python mcp_main.py

# The server will be available at http://127.0.0.1:8000/mcp
```

## Testing with Dedalus Client

```python
from dedalus_mcp.client import MCPClient
import asyncio

async def test():
    client = await MCPClient.connect("http://127.0.0.1:8000/mcp")
    tools = await client.list_tools()
    print([t.name for t in tools.tools])
    await client.close()

asyncio.run(test())
```
