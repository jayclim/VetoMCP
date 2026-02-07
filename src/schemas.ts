import { z } from "zod";

// Transaction schemas
export const TransactionTypeSchema = z.enum(["income", "expense"]);
export type TransactionType = z.infer<typeof TransactionTypeSchema>;

export const AddTransactionSchema = z.object({
    amount: z.number().describe("The monetary value of the transaction"),
    description: z.string().describe("A brief description of the transaction"),
    category: z.string().default("Uncategorized").describe("Budget category (e.g., 'Food', 'Transport')"),
    transaction_type: TransactionTypeSchema.default("expense").describe("Either 'expense' or 'income'"),
    username: z.string().default("default_user").describe("User identifier"),
    date: z.string().optional().describe("Optional ISO date string"),
});

export const GetTransactionsSchema = z.object({
    username: z.string().default("default_user"),
    category: z.string().optional(),
    transaction_type: TransactionTypeSchema.optional(),
    limit: z.number().default(10),
});

export const DeleteTransactionSchema = z.object({
    transaction_id: z.string().describe("The transaction ID to delete"),
    username: z.string().default("default_user"),
});

// Budget category schemas
export const CreateCategorySchema = z.object({
    name: z.string().describe("Category name"),
    monthly_limit: z.number().describe("Monthly spending limit"),
    username: z.string().default("default_user"),
});

export const GetCategoriesSchema = z.object({
    username: z.string().default("default_user"),
});

// Budget rule schemas
export const RuleTypeSchema = z.enum([
    "percentage_allocation",
    "category_limit",
    "savings_goal",
    "spending_alert"
]);
export type RuleType = z.infer<typeof RuleTypeSchema>;

export const CreateRuleSchema = z.object({
    rule_type: RuleTypeSchema.describe("Type: percentage_allocation, category_limit, savings_goal, or spending_alert"),
    name: z.string().describe("Friendly name for the rule"),
    config: z.string().describe("JSON configuration string"),
    username: z.string().default("default_user"),
});

export const GetRulesSchema = z.object({
    username: z.string().default("default_user"),
});

export const DeleteRuleSchema = z.object({
    rule_id: z.string().describe("The rule ID to delete"),
    username: z.string().default("default_user"),
});

// Local tool schemas (no database)
export const CheckBudgetSchema = z.object({
    budget_limit: z.number().describe("Monthly budget limit for this category"),
    amount_spent: z.number().describe("Amount already spent"),
    purchase_amount: z.number().describe("Cost of proposed purchase"),
    category: z.string().default("General").describe("Category name"),
});

export const SuggestAllocationSchema = z.object({
    monthly_income: z.number().describe("Monthly income"),
    method: z.string().default("50/30/20").describe("Budget method: '50/30/20', '80/20', or 'pay_yourself_first'"),
});

export const HealthScoreSchema = z.object({
    total_income: z.number().describe("Total monthly income"),
    total_expenses: z.number().describe("Total monthly expenses"),
    categories_over_budget: z.number().default(0),
    has_emergency_fund: z.boolean().default(false),
    debt_to_income_ratio: z.number().default(0),
});

export const ProjectSpendingSchema = z.object({
    current_day_of_month: z.number().describe("Current day (1-31)"),
    days_in_month: z.number().describe("Total days in month (28-31)"),
    amount_spent_so_far: z.number().describe("Amount spent so far"),
    budget_limit: z.number().describe("Monthly budget limit"),
});

export const GetDashboardSchema = z.object({
    username: z.string().default("default_user"),
});

export const CheckComplianceSchema = z.object({
    username: z.string().default("default_user"),
});

export const GetInsightsSchema = z.object({
    username: z.string().default("default_user"),
});
