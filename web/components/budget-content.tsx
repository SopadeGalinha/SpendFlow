"use client";

import { useEffect, useMemo, useState } from "react";

import { FeatureEmptyState } from "@/components/feature-empty-state";
import { CreateBudgetForm } from "@/components/finance-forms";
import { buildBudgetViews, formatCurrency, formatMonthLabel } from "@/lib/finance-selectors";
import type { BudgetResponse } from "@/lib/mock-finance";
import type { CategoryResponse } from "@/lib/finance-client";
import type { FinanceActionState } from "@/app/finance-actions";

const USER_PREFERENCES_ENDPOINT = "/api/user-preferences";

type BudgetViewMode = "category" | "flex";

function isEssentialBudget(name: string) {
  const normalized = name.toLowerCase();
  return ["rent", "housing", "utility", "insurance", "debt", "loan", "mortgage"].some(
    (keyword) => normalized.includes(keyword),
  );
}

function daysRemainingInMonth(monthKey: string) {
  const [year, month] = monthKey.split("-").map(Number);
  const today = new Date();
  const lastDay = new Date(year, month, 0).getDate();
  const isCurrentMonth =
    year === today.getFullYear() &&
    month === today.getMonth() + 1;

  if (isCurrentMonth) {
    return Math.max(lastDay - today.getDate() + 1, 1);
  }

  return lastDay;
}

type BudgetContentProps = {
  budgets: BudgetResponse[];
  monthKey: string;
  expenseCategories: CategoryResponse[];
  createBudgetAction: (
    state: FinanceActionState,
    formData: FormData,
  ) => Promise<FinanceActionState>;
};

function BudgetBar({ spent, limit }: { spent: number; limit: number }) {
  const progress = Math.min((spent / limit) * 100, 100);
  return (
    <div className="budget-bar">
      <div className="budget-bar-fill" style={{ width: `${progress}%` }} />
    </div>
  );
}

export function BudgetContent({
  budgets,
  monthKey,
  expenseCategories,
  createBudgetAction,
}: BudgetContentProps) {
  const [viewMode, setViewMode] = useState<BudgetViewMode>("category");
  const [preferencesReady, setPreferencesReady] = useState(false);
  const currentBudgets = buildBudgetViews(budgets, monthKey);

  useEffect(() => {
    let cancelled = false;

    async function loadPreferences() {
      try {
        const response = await fetch(USER_PREFERENCES_ENDPOINT, {
          method: "GET",
          cache: "no-store",
        });

        if (!response.ok) {
          return;
        }

        const payload = (await response.json()) as {
          budget?: {
            view_mode?: unknown;
          };
        };

        const nextViewMode = payload.budget?.view_mode;
        if (!cancelled && (nextViewMode === "category" || nextViewMode === "flex")) {
          setViewMode(nextViewMode);
        }
      } catch {
        return;
      } finally {
        if (!cancelled) {
          setPreferencesReady(true);
        }
      }
    }

    loadPreferences();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!preferencesReady) {
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(async () => {
      try {
        await fetch(USER_PREFERENCES_ENDPOINT, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            budget: {
              view_mode: viewMode,
            },
          }),
          signal: controller.signal,
        });
      } catch {
        return;
      }
    }, 300);

    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [preferencesReady, viewMode]);

  if (currentBudgets.length === 0) {
    return (
      <>
        <CreateBudgetForm
          action={createBudgetAction}
          categories={expenseCategories}
          templates={budgets}
        />
        <FeatureEmptyState
          eyebrow="Budget"
          title="No budgets for this period"
          description="Create a category budget to start tracking planned versus actual spending."
        />
      </>
    );
  }

  const planned = currentBudgets.reduce((sum, budget) => sum + budget.limit, 0);
  const spent = currentBudgets.reduce((sum, budget) => sum + budget.spent, 0);
  const essentialBudgets = useMemo(
    () => currentBudgets.filter((budget) => isEssentialBudget(budget.name)),
    [currentBudgets],
  );
  const flexibleBudgets = useMemo(
    () => currentBudgets.filter((budget) => !isEssentialBudget(budget.name)),
    [currentBudgets],
  );
  const essentialPlanned = essentialBudgets.reduce((sum, budget) => sum + budget.limit, 0);
  const essentialSpent = essentialBudgets.reduce((sum, budget) => sum + budget.spent, 0);
  const flexPlanned = flexibleBudgets.reduce((sum, budget) => sum + budget.limit, 0);
  const flexSpent = flexibleBudgets.reduce((sum, budget) => sum + budget.spent, 0);
  const flexRemaining = flexPlanned - flexSpent;
  const remainingDays = daysRemainingInMonth(monthKey);
  const flexDailyTarget = remainingDays > 0 ? flexRemaining / remainingDays : flexRemaining;

  return (
    <>
      <CreateBudgetForm
        action={createBudgetAction}
        categories={expenseCategories}
        templates={budgets}
      />

      <section className="panel budget-mode-panel">
        <div>
          <p className="eyebrow">Budget style</p>
          <h3>Choose your planning lens</h3>
        </div>
        <div className="composer-inline-actions">
          <button
            type="button"
            className={`day-tray-close ${viewMode === "category" ? "active" : ""}`}
            onClick={() => setViewMode("category")}
          >
            Category guardrails
          </button>
          <button
            type="button"
            className={`day-tray-close ${viewMode === "flex" ? "active" : ""}`}
            onClick={() => setViewMode("flex")}
          >
            Flex envelope
          </button>
        </div>
      </section>

      <section className="hero-panel placeholder-hero">
        <div>
          <p className="eyebrow">Budget</p>
          <h2>
            {formatMonthLabel(monthKey)} {viewMode === "flex" ? "flex plan" : "guardrails"}
          </h2>
          <p className="hero-copy">
            {viewMode === "flex"
              ? "Keep essentials protected while giving yourself one discretionary envelope for the rest of the month."
              : "Monthly budgets are loaded through the authenticated API path using the same response contract and tone calculations as the rest of the app."}
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Planned</span>
            <strong>{formatCurrency(planned)}</strong>
          </div>
          <div>
            <span>Spent</span>
            <strong>{formatCurrency(spent)}</strong>
          </div>
        </div>
      </section>

      <section className="panel wide-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Active budgets</p>
            <h3>
              {viewMode === "flex"
                ? "Essential vs flexible spending"
                : "Remaining room by category"}
            </h3>
          </div>
          <span className="pill">{currentBudgets.length} tracked categories</span>
        </div>
        {viewMode === "category" ? (
          <div className="budget-list">
            {currentBudgets.map((budget) => (
              <div key={budget.id} className="budget-row">
                <div className="budget-copy">
                  <strong>{budget.name}</strong>
                  <span>
                    Used {formatCurrency(budget.spent)} · Remaining {formatCurrency(budget.remaining)}
                  </span>
                </div>
                <div className={`budget-chip ${budget.tone}`}>{formatCurrency(budget.limit)}</div>
                <BudgetBar spent={budget.spent} limit={budget.limit} />
              </div>
            ))}
          </div>
        ) : (
          <div className="budget-flex-grid">
            <article className="budget-flex-card">
              <p className="eyebrow">Essentials</p>
              <strong>{formatCurrency(essentialSpent)} / {formatCurrency(essentialPlanned)}</strong>
              <BudgetBar spent={essentialSpent} limit={Math.max(essentialPlanned, 1)} />
              <span>{essentialBudgets.length} categories protected</span>
            </article>

            <article className="budget-flex-card">
              <p className="eyebrow">Flexible envelope</p>
              <strong>{formatCurrency(flexRemaining)} left</strong>
              <BudgetBar spent={flexSpent} limit={Math.max(flexPlanned, 1)} />
              <span>Spent {formatCurrency(flexSpent)} of {formatCurrency(flexPlanned)}</span>
            </article>

            <article className="budget-flex-card">
              <p className="eyebrow">Daily flex pace</p>
              <strong>{formatCurrency(flexDailyTarget)}</strong>
              <span>{remainingDays} day(s) remaining in this month.</span>
            </article>
          </div>
        )}
      </section>
    </>
  );
}