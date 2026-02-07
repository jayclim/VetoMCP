/**
 * Veto Budget Agent - MCP Server
 * 
 * Entry point for the TypeScript MCP server following
 * the nessie-mcp-server architecture pattern.
 */

import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import cors from "cors";
import dotenv from "dotenv";

// Import schemas
import {
    AddTransactionSchema,
    GetTransactionsSchema,
    DeleteTransactionSchema,
    CreateCategorySchema,
    GetCategoriesSchema,
    CreateRuleSchema,
    GetRulesSchema,
    DeleteRuleSchema,
    CheckBudgetSchema,
    SuggestAllocationSchema,
    HealthScoreSchema,
    ProjectSpendingSchema,
    GetDashboardSchema,
    CheckComplianceSchema,
    GetInsightsSchema,
} from "./schemas.js";

// Import tools
import {
    getBudgetMethods,
    checkBudgetForPurchase,
    suggestBudgetAllocation,
    getBudgetHealthScore,
    projectMonthlySpending,
} from "./tools/local-tools.js";

import {
    addTransaction,
    deleteTransaction,
    getTransactions,
    createBudgetCategory,
    getBudgetCategories,
    getDashboardSummary,
    createBudgetRule,
    getBudgetRules,
    deleteBudgetRule,
    checkRuleCompliance,
    getSpendingInsights,
} from "./tools/server-tools.js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3000;

// Initialize MCP Server
const mcpServer = new McpServer({
    name: "VetoBudgetAgent",
    version: "1.0.0",
});

// ═══════════════════════════════════════════════════════════════════════════════
// LOCAL TOOLS (pure calculations, no database)
// ═══════════════════════════════════════════════════════════════════════════════

mcpServer.tool(
    "get_budget_methods",
    "Returns a list of popular budget methods with descriptions. Useful for onboarding.",
    {},
    async () => ({
        content: [{ type: "text", text: getBudgetMethods() }]
    })
);

mcpServer.tool(
    "check_budget_for_purchase",
    "Check if a purchase is within budget. Returns APPROVE/DENY/CAUTION recommendation.",
    CheckBudgetSchema.shape,
    async ({ budget_limit, amount_spent, purchase_amount, category }) => ({
        content: [{ type: "text", text: checkBudgetForPurchase(budget_limit, amount_spent, purchase_amount, category) }]
    })
);

mcpServer.tool(
    "suggest_budget_allocation",
    "Suggest budget allocations based on income and chosen method (50/30/20, 80/20, pay_yourself_first).",
    SuggestAllocationSchema.shape,
    async ({ monthly_income, method }) => ({
        content: [{ type: "text", text: suggestBudgetAllocation(monthly_income, method) }]
    })
);

mcpServer.tool(
    "get_budget_health_score",
    "Calculate a 0-100 financial health score with grade (A-F).",
    HealthScoreSchema.shape,
    async ({ total_income, total_expenses, categories_over_budget, has_emergency_fund, debt_to_income_ratio }) => ({
        content: [{ type: "text", text: getBudgetHealthScore(total_income, total_expenses, categories_over_budget, has_emergency_fund, debt_to_income_ratio) }]
    })
);

mcpServer.tool(
    "project_monthly_spending",
    "Project end-of-month spending based on current pace.",
    ProjectSpendingSchema.shape,
    async ({ current_day_of_month, days_in_month, amount_spent_so_far, budget_limit }) => ({
        content: [{ type: "text", text: projectMonthlySpending(current_day_of_month, days_in_month, amount_spent_so_far, budget_limit) }]
    })
);

// ═══════════════════════════════════════════════════════════════════════════════
// SERVER TOOLS (require database access - async)
// ═══════════════════════════════════════════════════════════════════════════════

mcpServer.tool(
    "add_transaction",
    "Record a new financial transaction (expense or income).",
    AddTransactionSchema.shape,
    async ({ amount, description, category, transaction_type, username, date }) => ({
        content: [{ type: "text", text: await addTransaction(amount, description, category, transaction_type, username, date) }]
    })
);

mcpServer.tool(
    "delete_transaction",
    "Delete a transaction by its ID.",
    DeleteTransactionSchema.shape,
    async ({ transaction_id, username }) => ({
        content: [{ type: "text", text: await deleteTransaction(transaction_id, username) }]
    })
);

mcpServer.tool(
    "get_transactions",
    "List recent transactions with optional filtering by category and type.",
    GetTransactionsSchema.shape,
    async ({ username, category, transaction_type, limit }) => ({
        content: [{ type: "text", text: await getTransactions(username, category, transaction_type, limit) }]
    })
);

mcpServer.tool(
    "create_budget_category",
    "Create a new budget category with a monthly spending limit.",
    CreateCategorySchema.shape,
    async ({ name, monthly_limit, username }) => ({
        content: [{ type: "text", text: await createBudgetCategory(name, monthly_limit, username) }]
    })
);

mcpServer.tool(
    "get_budget_categories",
    "List all budget categories and their limits.",
    GetCategoriesSchema.shape,
    async ({ username }) => ({
        content: [{ type: "text", text: await getBudgetCategories(username) }]
    })
);

mcpServer.tool(
    "get_dashboard_summary",
    "Get a financial dashboard summary including income, expenses, and category breakdowns.",
    GetDashboardSchema.shape,
    async ({ username }) => ({
        content: [{ type: "text", text: await getDashboardSummary(username) }]
    })
);

mcpServer.tool(
    "create_budget_rule",
    "Create a new budget rule (percentage_allocation, category_limit, savings_goal, spending_alert).",
    CreateRuleSchema.shape,
    async ({ rule_type, name, config, username }) => ({
        content: [{ type: "text", text: await createBudgetRule(rule_type, name, config, username) }]
    })
);

mcpServer.tool(
    "get_budget_rules",
    "List all active budget rules for a user.",
    GetRulesSchema.shape,
    async ({ username }) => ({
        content: [{ type: "text", text: await getBudgetRules(username) }]
    })
);

mcpServer.tool(
    "delete_budget_rule",
    "Delete a budget rule by its ID.",
    DeleteRuleSchema.shape,
    async ({ rule_id, username }) => ({
        content: [{ type: "text", text: await deleteBudgetRule(rule_id, username) }]
    })
);

mcpServer.tool(
    "check_rule_compliance",
    "Check if the user is following their active budget rules. Returns compliance status for each rule.",
    CheckComplianceSchema.shape,
    async ({ username }) => ({
        content: [{ type: "text", text: await checkRuleCompliance(username) }]
    })
);

mcpServer.tool(
    "get_spending_insights",
    "Get AI-friendly spending insights and patterns. Useful for proactive budget advice.",
    GetInsightsSchema.shape,
    async ({ username }) => ({
        content: [{ type: "text", text: await getSpendingInsights(username) }]
    })
);

// ═══════════════════════════════════════════════════════════════════════════════
// EXPRESS ENDPOINTS (Dedalus-compatible)
// ═══════════════════════════════════════════════════════════════════════════════

// Store active SSE transports
const transports: Map<string, SSEServerTransport> = new Map();

// Main MCP entry point - required by Dedalus
app.get("/mcp", async (req, res) => {
    const sessionId = crypto.randomUUID();
    const transport = new SSEServerTransport(`/messages/${sessionId}`, res);
    transports.set(sessionId, transport);

    res.on("close", () => {
        transports.delete(sessionId);
    });

    await mcpServer.connect(transport);
});

// POST endpoint for client messages
app.post("/messages/:sessionId", async (req, res) => {
    const { sessionId } = req.params;
    const transport = transports.get(sessionId);

    if (!transport) {
        res.status(404).json({ error: "Session not found" });
        return;
    }

    // Handle incoming message
    await transport.handlePostMessage(req, res);
});

// Health check
app.get("/health", (req, res) => {
    res.json({ status: "ok", server: "VetoBudgetAgent", version: "1.0.0" });
});

// Start server
app.listen(PORT, () => {
    console.log(`Veto MCP Server running on port ${PORT}`);
    console.log(`MCP endpoint: http://localhost:${PORT}/mcp`);
});
