/**
 * Database-backed budget tools - using Supabase
 */

import { supabase, ensureUser, Transaction, BudgetCategory, BudgetRule } from "../database.js";

// ─── Transaction Tools ───────────────────────────────────────────────────────

export async function addTransaction(
    amount: number,
    description: string,
    category: string,
    transactionType: "income" | "expense",
    username: string = "default_user",
    date?: string
): Promise<string> {
    try {
        const userId = await ensureUser(username);
        const txDate = date || new Date().toISOString();

        const { data, error } = await supabase
            .from("veto_transactions")
            .insert({
                user_id: userId,
                amount,
                description,
                category,
                transaction_type: transactionType,
                date: txDate,
            })
            .select("id")
            .single();

        if (error) throw error;
        return `Transaction added: ${description} ($${amount}) - ID: ${data.id}`;
    } catch (error: any) {
        return `Error adding transaction: ${error.message}`;
    }
}

export async function deleteTransaction(transactionId: string, username: string = "default_user"): Promise<string> {
    try {
        const userId = await ensureUser(username);

        const { error, count } = await supabase
            .from("veto_transactions")
            .delete()
            .eq("id", transactionId)
            .eq("user_id", userId);

        if (error) throw error;
        if (count && count > 0) {
            return `Transaction ${transactionId} deleted successfully.`;
        }
        return `Transaction ${transactionId} not found or access denied.`;
    } catch (error: any) {
        return `Error deleting transaction: ${error.message}`;
    }
}

export async function getTransactions(
    username: string = "default_user",
    category?: string,
    transactionType?: "income" | "expense",
    limit: number = 10
): Promise<string> {
    try {
        const userId = await ensureUser(username);

        let query = supabase
            .from("veto_transactions")
            .select("*")
            .eq("user_id", userId)
            .order("date", { ascending: false })
            .limit(limit);

        if (category) query = query.eq("category", category);
        if (transactionType) query = query.eq("transaction_type", transactionType);

        const { data: txs, error } = await query;

        if (error) throw error;
        if (!txs || txs.length === 0) return "No transactions found.";

        const lines = [`Found ${txs.length} transactions:`];
        for (const tx of txs as Transaction[]) {
            const dateStr = tx.date ? tx.date.split("T")[0] : "N/A";
            lines.push(`- [${dateStr}] ${tx.description}: $${tx.amount} (${tx.category}) [${tx.transaction_type}] ID: ${tx.id}`);
        }

        return lines.join("\n");
    } catch (error: any) {
        return `Error fetching transactions: ${error.message}`;
    }
}

// ─── Budget Category Tools ───────────────────────────────────────────────────

export async function createBudgetCategory(name: string, monthlyLimit: number, username: string = "default_user"): Promise<string> {
    try {
        const userId = await ensureUser(username);

        const { error } = await supabase
            .from("veto_budget_categories")
            .insert({
                user_id: userId,
                name,
                monthly_limit: monthlyLimit,
            });

        if (error) throw error;
        return `Category '${name}' created with limit $${monthlyLimit}.`;
    } catch (error: any) {
        return `Error creating category: ${error.message}`;
    }
}

export async function getBudgetCategories(username: string = "default_user"): Promise<string> {
    try {
        const userId = await ensureUser(username);

        const { data: cats, error } = await supabase
            .from("veto_budget_categories")
            .select("*")
            .eq("user_id", userId);

        if (error) throw error;
        if (!cats || cats.length === 0) return "No categories set.";

        const lines = ["Budget Categories:"];
        for (const c of cats as BudgetCategory[]) {
            lines.push(`- ${c.name}: $${c.monthly_limit}/month`);
        }

        return lines.join("\n");
    } catch (error: any) {
        return `Error fetching categories: ${error.message}`;
    }
}

// ─── Dashboard Summary ───────────────────────────────────────────────────────

export async function getDashboardSummary(username: string = "default_user"): Promise<string> {
    try {
        const userId = await ensureUser(username);

        // Get all transactions
        const { data: transactions, error: txError } = await supabase
            .from("veto_transactions")
            .select("*")
            .eq("user_id", userId);

        if (txError) throw txError;

        const txs = (transactions || []) as Transaction[];

        let totalIncome = 0;
        let totalExpenses = 0;
        const categorySpending: Record<string, number> = {};

        for (const tx of txs) {
            if (tx.transaction_type === "income") {
                totalIncome += Number(tx.amount);
            } else {
                totalExpenses += Number(tx.amount);
                categorySpending[tx.category] = (categorySpending[tx.category] || 0) + Number(tx.amount);
            }
        }

        const net = totalIncome - totalExpenses;

        // Get budget limits
        const { data: budgetLimits } = await supabase
            .from("veto_budget_categories")
            .select("name, monthly_limit")
            .eq("user_id", userId);

        const limitMap = new Map((budgetLimits || []).map((b: any) => [b.name, b.monthly_limit]));

        const lines = [
            "**Dashboard Summary**",
            `Total Income: $${totalIncome.toFixed(2)}`,
            `Total Expenses: $${totalExpenses.toFixed(2)}`,
            `Net: $${net.toFixed(2)}`,
            "",
            "**Category Breakdown:**"
        ];

        for (const [category, spent] of Object.entries(categorySpending)) {
            const limit = limitMap.get(category);
            let line = `- ${category}: $${spent.toFixed(2)}`;
            if (limit !== undefined) {
                const remaining = Number(limit) - spent;
                line += ` / $${limit} (Remaining: $${remaining.toFixed(2)})`;
            }
            lines.push(line);
        }

        return lines.join("\n");
    } catch (error: any) {
        return `Error fetching dashboard: ${error.message}`;
    }
}

// ─── Budget Rules ────────────────────────────────────────────────────────────

export async function createBudgetRule(
    ruleType: "percentage_allocation" | "category_limit" | "savings_goal" | "spending_alert",
    name: string,
    config: string,
    username: string = "default_user"
): Promise<string> {
    try {
        // Validate JSON
        const configObj = JSON.parse(config);

        const userId = await ensureUser(username);

        const { data, error } = await supabase
            .from("veto_budget_rules")
            .insert({
                user_id: userId,
                rule_type: ruleType,
                name,
                config: configObj,
            })
            .select("id")
            .single();

        if (error) throw error;
        return `Budget rule '${name}' created successfully (ID: ${data.id}).`;
    } catch (error: any) {
        if (error instanceof SyntaxError) {
            return "Error: config must be a valid JSON string.";
        }
        return `Error creating budget rule: ${error.message}`;
    }
}

export async function getBudgetRules(username: string = "default_user"): Promise<string> {
    try {
        const userId = await ensureUser(username);

        const { data: rules, error } = await supabase
            .from("veto_budget_rules")
            .select("*")
            .eq("user_id", userId)
            .eq("is_active", true);

        if (error) throw error;
        if (!rules || rules.length === 0) return "No budget rules set.";

        const lines = ["Active Budget Rules:"];
        for (const r of rules as BudgetRule[]) {
            lines.push(`- [${r.rule_type}] ${r.name} (ID: ${r.id})`);
            lines.push(`  Config: ${JSON.stringify(r.config)}`);
        }

        return lines.join("\n");
    } catch (error: any) {
        return `Error fetching budget rules: ${error.message}`;
    }
}

export async function deleteBudgetRule(ruleId: string, username: string = "default_user"): Promise<string> {
    try {
        const userId = await ensureUser(username);

        const { error, count } = await supabase
            .from("veto_budget_rules")
            .delete()
            .eq("id", ruleId)
            .eq("user_id", userId);

        if (error) throw error;
        if (count && count > 0) {
            return `Budget rule ${ruleId} deleted successfully.`;
        }
        return `Budget rule ${ruleId} not found or access denied.`;
    } catch (error: any) {
        return `Error deleting budget rule: ${error.message}`;
    }
}

// ─── Rule Compliance ─────────────────────────────────────────────────────────

export async function checkRuleCompliance(username: string = "default_user"): Promise<string> {
    try {
        const userId = await ensureUser(username);

        // Get active rules
        const { data: rules, error: rulesError } = await supabase
            .from("veto_budget_rules")
            .select("*")
            .eq("user_id", userId)
            .eq("is_active", true);

        if (rulesError) throw rulesError;
        if (!rules || rules.length === 0) return "No active budget rules found.";

        // Get transactions
        const { data: transactions } = await supabase
            .from("veto_transactions")
            .select("*")
            .eq("user_id", userId);

        const txs = (transactions || []) as Transaction[];

        let totalIncome = 0;
        let totalExpenses = 0;
        const categorySpending: Record<string, number> = {};

        for (const tx of txs) {
            if (tx.transaction_type === "income") {
                totalIncome += Number(tx.amount);
            } else {
                totalExpenses += Number(tx.amount);
                categorySpending[tx.category] = (categorySpending[tx.category] || 0) + Number(tx.amount);
            }
        }

        const lines = ["**Budget Rule Compliance Report**", ""];

        for (const rule of rules as BudgetRule[]) {
            const config = rule.config;
            let status = "⚠️ Cannot determine";
            let details = "";

            switch (rule.rule_type) {
                case "percentage_allocation":
                    if (totalIncome > 0 && (config as any).savings !== undefined) {
                        const targetSavings = (config as any).savings;
                        const actualSavings = ((totalIncome - totalExpenses) / totalIncome) * 100;
                        const compliant = actualSavings >= targetSavings;
                        status = compliant ? "✅ Compliant" : "❌ Not Compliant";
                        details = `Target savings: ${targetSavings}% | Actual: ${actualSavings.toFixed(1)}%`;
                    }
                    break;

                case "category_limit":
                    if ((config as any).category && (config as any).limit !== undefined) {
                        const spent = categorySpending[(config as any).category] || 0;
                        const compliant = spent <= (config as any).limit;
                        status = compliant ? "✅ Compliant" : "❌ Not Compliant";
                        details = `${(config as any).category}: $${spent.toFixed(2)} / $${(config as any).limit}`;
                    }
                    break;

                case "savings_goal":
                    if ((config as any).goal !== undefined) {
                        const saved = totalIncome - totalExpenses;
                        const compliant = saved >= (config as any).goal;
                        status = compliant ? "✅ Compliant" : "❌ Not Compliant";
                        details = `Saved: $${saved.toFixed(2)} / Goal: $${(config as any).goal}`;
                    }
                    break;

                case "spending_alert":
                    if ((config as any).category && (config as any).threshold !== undefined) {
                        const spent = categorySpending[(config as any).category] || 0;
                        const alertTriggered = spent >= (config as any).threshold;
                        status = alertTriggered ? "🔔 ALERT TRIGGERED" : "✅ No alert";
                        details = `${(config as any).category}: $${spent.toFixed(2)} (threshold: $${(config as any).threshold})`;
                    }
                    break;
            }

            lines.push(`**${rule.name}** (${rule.rule_type}): ${status}`);
            if (details) lines.push(`  ${details}`);
            lines.push("");
        }

        return lines.join("\n");
    } catch (error: any) {
        return `Error checking compliance: ${error.message}`;
    }
}

// ─── Spending Insights ───────────────────────────────────────────────────────

export async function getSpendingInsights(username: string = "default_user"): Promise<string> {
    try {
        const userId = await ensureUser(username);

        // Get transactions
        const { data: transactions } = await supabase
            .from("veto_transactions")
            .select("*")
            .eq("user_id", userId);

        const txs = (transactions || []) as Transaction[];

        let totalIncome = 0;
        let totalExpenses = 0;
        const categorySpending: Record<string, number> = {};

        for (const tx of txs) {
            if (tx.transaction_type === "income") {
                totalIncome += Number(tx.amount);
            } else {
                totalExpenses += Number(tx.amount);
                categorySpending[tx.category] = (categorySpending[tx.category] || 0) + Number(tx.amount);
            }
        }

        const insights: string[] = [];

        // Savings rate insight
        if (totalIncome > 0) {
            const savingsRate = ((totalIncome - totalExpenses) / totalIncome) * 100;
            if (savingsRate >= 20) {
                insights.push(`✅ Great savings rate of ${savingsRate.toFixed(1)}%!`);
            } else if (savingsRate >= 10) {
                insights.push(`⚠️ Savings rate is ${savingsRate.toFixed(1)}%. Consider increasing to 20%.`);
            } else if (savingsRate > 0) {
                insights.push(`⚠️ Low savings rate of ${savingsRate.toFixed(1)}%. Try to save more.`);
            } else {
                insights.push(`❌ Negative savings rate (${savingsRate.toFixed(1)}%). Spending exceeds income!`);
            }
        } else {
            insights.push("ℹ️ No income recorded yet.");
        }

        // Get budget limits
        const { data: budgetLimits } = await supabase
            .from("veto_budget_categories")
            .select("name, monthly_limit")
            .eq("user_id", userId);

        const limitMap = new Map((budgetLimits || []).map((b: any) => [b.name, Number(b.monthly_limit)]));

        // Over budget categories
        for (const [category, spent] of Object.entries(categorySpending)) {
            const limit = limitMap.get(category);
            if (limit !== undefined && spent > limit) {
                insights.push(`🚨 ${category} is $${(spent - limit).toFixed(2)} over budget!`);
            }
        }

        // Highest spending
        const sortedCategories = Object.entries(categorySpending).sort((a, b) => b[1] - a[1]);
        if (sortedCategories.length > 0 && sortedCategories[0][1] > 0) {
            insights.push(`💰 Highest spending: ${sortedCategories[0][0]} ($${sortedCategories[0][1].toFixed(2)})`);
        }

        if (insights.length === 0) {
            return "No spending data available yet.";
        }

        return "**Spending Insights**\n" + insights.join("\n");
    } catch (error: any) {
        return `Error generating insights: ${error.message}`;
    }
}
