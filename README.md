# Veto Budget MCP Server

AI-powered budget management server for the Dedalus Labs marketplace.

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. Run locally:
```bash
python main.py
```

## Tools

| Tool | Description |
|------|-------------|
| `add_transaction` | Record income/expense |
| `delete_transaction` | Remove a transaction |
| `get_transactions` | List transactions |
| `create_budget_category` | Set spending limits |
| `get_budget_categories` | View categories |
| `get_dashboard_summary` | Financial overview |
| `get_spending_insights` | AI analytics |
| `create_budget_rule` | Automated rules |
| `get_budget_rules` | List active rules |
| `delete_budget_rule` | Remove a rule |
| `check_rule_compliance` | Rule adherence check |
| `get_budget_methods` | Budgeting strategies |
| `check_budget_for_purchase` | Pre-purchase validation |
| `suggest_budget_allocation` | Income allocation |
| `get_budget_health_score` | Health score (0-100) |
| `project_monthly_spending` | Spending projection |

## Structure

```
VetoMCP/
├── main.py           # Entry point
├── database.py       # Supabase client
├── pyproject.toml    # Dependencies
└── tools/
    ├── transactions.py
    ├── categories.py
    ├── dashboard.py
    ├── rules.py
    └── local.py
```
