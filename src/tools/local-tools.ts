/**
 * Local budget tools - pure calculations, no database access
 */

interface BudgetMethod {
    name: string;
    description: string;
    best_for: string;
    config_template: string;
}

export function getBudgetMethods(): string {
    const methods: BudgetMethod[] = [
        {
            name: "50/30/20 Rule",
            description: "Allocate 50% of income to needs (rent, groceries, utilities), 30% to wants (entertainment, dining out), and 20% to savings and debt repayment.",
            best_for: "Beginners who want a simple framework.",
            config_template: '{"needs": 50, "wants": 30, "savings": 20}'
        },
        {
            name: "Zero-Based Budgeting",
            description: "Assign every dollar a specific purpose until income minus expenses equals zero. Every dollar has a job.",
            best_for: "Detail-oriented planners who want full control.",
            config_template: '{"method": "zero_based"}'
        },
        {
            name: "Envelope System",
            description: "Allocate cash to category 'envelopes'. When an envelope is empty, no more spending in that category.",
            best_for: "People who struggle with overspending in specific categories.",
            config_template: '{"categories": ["Groceries", "Entertainment", "Dining Out"]}'
        },
        {
            name: "Pay Yourself First",
            description: "Automatically save a fixed percentage of income before spending on anything else.",
            best_for: "Those prioritizing savings and wealth building.",
            config_template: '{"savings_percent": 20}'
        },
        {
            name: "80/20 Rule",
            description: "Save 20% of income, spend 80% however you want. Simple and flexible.",
            best_for: "People who want minimal budgeting effort.",
            config_template: '{"savings": 20, "spending": 80}'
        },
        {
            name: "Values-Based Budgeting",
            description: "Prioritize spending on what matters most to you. Cut ruthlessly elsewhere.",
            best_for: "Those who want alignment between money and values.",
            config_template: '{"priorities": ["Health", "Education", "Experiences"]}'
        }
    ];
    return JSON.stringify(methods, null, 2);
}

interface PurchaseCheckResult {
    category: string;
    budget_limit: number;
    already_spent: number;
    remaining_before: number;
    purchase_amount: number;
    remaining_after: number;
    recommendation: "APPROVE" | "DENY" | "CAUTION";
    reason: string;
}

export function checkBudgetForPurchase(
    budgetLimit: number,
    amountSpent: number,
    purchaseAmount: number,
    category: string = "General"
): string {
    const remaining = budgetLimit - amountSpent;
    const afterPurchase = remaining - purchaseAmount;

    const result: PurchaseCheckResult = {
        category,
        budget_limit: budgetLimit,
        already_spent: amountSpent,
        remaining_before: remaining,
        purchase_amount: purchaseAmount,
        remaining_after: afterPurchase,
        recommendation: "APPROVE",
        reason: ""
    };

    if (purchaseAmount > remaining) {
        result.recommendation = "DENY";
        result.reason = `This purchase of $${purchaseAmount.toFixed(2)} would exceed your ${category} budget by $${Math.abs(afterPurchase).toFixed(2)}.`;
    } else if (afterPurchase < budgetLimit * 0.1) {
        result.recommendation = "CAUTION";
        result.reason = `This purchase is within budget, but would leave only $${afterPurchase.toFixed(2)} (${((afterPurchase / budgetLimit) * 100).toFixed(1)}%) remaining.`;
    } else {
        result.recommendation = "APPROVE";
        result.reason = `This purchase is within budget. You'll have $${afterPurchase.toFixed(2)} remaining.`;
    }

    return JSON.stringify(result, null, 2);
}

export function suggestBudgetAllocation(monthlyIncome: number, method: string = "50/30/20"): string {
    let allocations: Record<string, { percent: number; amount: number }> = {};

    switch (method) {
        case "50/30/20":
            allocations = {
                needs: { percent: 50, amount: monthlyIncome * 0.50 },
                wants: { percent: 30, amount: monthlyIncome * 0.30 },
                savings: { percent: 20, amount: monthlyIncome * 0.20 },
            };
            break;
        case "80/20":
            allocations = {
                spending: { percent: 80, amount: monthlyIncome * 0.80 },
                savings: { percent: 20, amount: monthlyIncome * 0.20 },
            };
            break;
        case "pay_yourself_first":
            allocations = {
                savings: { percent: 25, amount: monthlyIncome * 0.25 },
                remainder: { percent: 75, amount: monthlyIncome * 0.75 },
            };
            break;
        default:
            return JSON.stringify({ error: `Unknown method: ${method}. Try '50/30/20', '80/20', or 'pay_yourself_first'.` });
    }

    return JSON.stringify({
        monthly_income: monthlyIncome,
        method,
        allocations
    }, null, 2);
}

export function getBudgetHealthScore(
    totalIncome: number,
    totalExpenses: number,
    categoriesOverBudget: number = 0,
    hasEmergencyFund: boolean = false,
    debtToIncomeRatio: number = 0
): string {
    let score = 50;

    // Savings rate impact
    if (totalIncome > 0) {
        const savingsRate = (totalIncome - totalExpenses) / totalIncome;
        if (savingsRate >= 0.20) score += 30;
        else if (savingsRate >= 0.10) score += 15;
        else if (savingsRate >= 0) score += 5;
        else score -= 20;
    }

    // Over budget penalty
    score -= Math.min(categoriesOverBudget * 5, 15);

    // Emergency fund bonus
    if (hasEmergencyFund) score += 15;

    // Debt ratio penalty
    if (debtToIncomeRatio > 0.50) score -= 20;
    else if (debtToIncomeRatio > 0.30) score -= 10;
    else if (debtToIncomeRatio > 0.15) score -= 5;

    // Clamp
    score = Math.max(0, Math.min(100, score));

    // Grade
    let grade: string, message: string;
    if (score >= 80) { grade = "A"; message = "Excellent financial health! Keep it up."; }
    else if (score >= 60) { grade = "B"; message = "Good financial health with room for improvement."; }
    else if (score >= 40) { grade = "C"; message = "Fair financial health. Consider reviewing your budget."; }
    else if (score >= 20) { grade = "D"; message = "Poor financial health. Immediate action recommended."; }
    else { grade = "F"; message = "Critical financial situation. Seek professional advice."; }

    return JSON.stringify({
        score,
        grade,
        message,
        factors: {
            savings_rate_impact: totalIncome > 0 && (totalIncome - totalExpenses) > 0 ? "positive" : "negative",
            over_budget_categories: categoriesOverBudget,
            emergency_fund: hasEmergencyFund,
            debt_to_income: debtToIncomeRatio
        }
    }, null, 2);
}

export function projectMonthlySpending(
    currentDayOfMonth: number,
    daysInMonth: number,
    amountSpentSoFar: number,
    budgetLimit: number
): string {
    if (currentDayOfMonth <= 0) {
        return JSON.stringify({ error: "current_day_of_month must be positive" });
    }

    const dailyRate = amountSpentSoFar / currentDayOfMonth;
    const projectedTotal = dailyRate * daysInMonth;
    const difference = budgetLimit - projectedTotal;

    const result: Record<string, any> = {
        current_day: currentDayOfMonth,
        days_in_month: daysInMonth,
        spent_so_far: amountSpentSoFar,
        daily_average: Math.round(dailyRate * 100) / 100,
        projected_month_total: Math.round(projectedTotal * 100) / 100,
        budget_limit: budgetLimit,
        projected_difference: Math.round(Math.abs(difference) * 100) / 100,
    };

    if (difference >= 0) {
        result.status = "ON_TRACK";
        result.message = `At current pace, you'll finish $${difference.toFixed(2)} under budget.`;
    } else {
        result.status = "OVER_BUDGET";
        result.message = `Warning: At current pace, you'll be $${Math.abs(difference).toFixed(2)} over budget.`;
        const remainingDays = daysInMonth - currentDayOfMonth;
        if (remainingDays > 0) {
            const remainingBudget = budgetLimit - amountSpentSoFar;
            const safeDaily = remainingBudget / remainingDays;
            result.recommended_daily_limit = Math.round(Math.max(0, safeDaily) * 100) / 100;
        }
    }

    return JSON.stringify(result, null, 2);
}
