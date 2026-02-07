# Veto Budget MCP Server

AI-powered budget management MCP server for the Dedalus Labs marketplace.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

## Project Structure

```
VetoMCP/
├── src/
│   ├── index.ts           # Main Express + MCP server
│   ├── database.ts        # SQLite database layer
│   ├── schemas.ts         # Zod validation schemas
│   └── tools/
│       ├── local-tools.ts   # Pure calculation tools
│       └── server-tools.ts  # Database-backed tools
├── package.json
├── tsconfig.json
└── .env.example
```

## Available Tools

### Local Tools (No Database)
- `get_budget_methods` - Popular budgeting strategies
- `check_budget_for_purchase` - Pre-purchase validation
- `suggest_budget_allocation` - Income allocation
- `get_budget_health_score` - Financial health score (0-100)
- `project_monthly_spending` - Spending projections

### Server Tools (Database)
- `add_transaction` / `delete_transaction` / `get_transactions`
- `create_budget_category` / `get_budget_categories`
- `get_dashboard_summary` - Financial overview
- `create_budget_rule` / `get_budget_rules` / `delete_budget_rule`
- `check_rule_compliance` - Verify rule adherence
- `get_spending_insights` - AI-friendly analytics

## Dedalus Deployment

1. Push to GitHub
2. Go to [dedaluslabs.ai/dashboard/servers](https://www.dedaluslabs.ai/dashboard/servers)
3. Connect repository and deploy

### Usage with Dedalus SDK

```python
from dedalus_labs import AsyncDedalus, DedalusRunner
import asyncio

async def main():
    client = AsyncDedalus()
    runner = DedalusRunner(client)
    response = await runner.run(
        input="Check if I'm following my budget rules",
        model="anthropic/claude-opus-4-6",
        mcp_servers=["your-org/veto-budget"],
    )
    print(response.final_output)

asyncio.run(main())
```

## Environment Variables

```env
PORT=3000
DATABASE_PATH=./veto.db
DEDALUS_API_KEY=your-api-key
```
