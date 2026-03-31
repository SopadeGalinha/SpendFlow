"use client";

import { useActionState, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import type { FinanceActionState } from "@/app/finance-actions";
import type { CategoryResponse } from "@/lib/finance-client";
import type { AccountResponse, TransactionResponse } from "@/lib/mock-finance";
import { formatCurrency } from "@/lib/finance-selectors";
import { emitShellToast } from "@/lib/ui-feedback";

const INITIAL_STATE: FinanceActionState = {
  error: null,
  ok: false,
  message: null,
  submittedAt: null,
};

const RULES_STORAGE_KEY = "spendflow-transaction-rules";
const LAST_BULK_UNDO_STORAGE_KEY = "spendflow-last-bulk-undo";

type BulkTransactionUpdate = {
  transaction_id: string;
  category_id: string | null;
};

type TransactionRule = {
  id: string;
  merchantContains: string;
  categoryId: string;
  enabled: boolean;
};

type BulkUpdateAction = (
  state: FinanceActionState,
  formData: FormData,
) => Promise<FinanceActionState>;

type TransactionsWorkbenchProps = {
  transactions: TransactionResponse[];
  accounts: AccountResponse[];
  categories: CategoryResponse[];
  bulkUpdateAction: BulkUpdateAction;
};

function isBulkEditable(transaction: TransactionResponse) {
  return (
    transaction.kind === "regular" || transaction.kind === "adjustment"
  );
}

function normalizeRuleInput(input: string) {
  return input.trim().toLowerCase();
}

function normalizeBulkUpdates(value: unknown): BulkTransactionUpdate[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const normalized: BulkTransactionUpdate[] = [];

  for (const candidate of value) {
    if (typeof candidate !== "object" || candidate === null) {
      continue;
    }

    const entry = candidate as {
      transaction_id?: unknown;
      category_id?: unknown;
    };

    if (typeof entry.transaction_id !== "string" || entry.transaction_id.trim() === "") {
      continue;
    }

    if (entry.category_id !== null && typeof entry.category_id !== "string") {
      continue;
    }

    normalized.push({
      transaction_id: entry.transaction_id.trim(),
      category_id:
        entry.category_id === undefined
          ? null
          : (entry.category_id as string | null),
    });
  }

  return normalized;
}

export function TransactionsWorkbench({
  transactions,
  accounts,
  categories,
  bulkUpdateAction,
}: TransactionsWorkbenchProps) {
  const router = useRouter();
  const formRef = useRef<HTMLFormElement>(null);
  const pendingUndoUpdatesRef = useRef<BulkTransactionUpdate[]>([]);
  const [state, formAction, isPending] = useActionState(
    bulkUpdateAction,
    INITIAL_STATE,
  );

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTransactionIds, setSelectedTransactionIds] = useState<Set<string>>(
    new Set(),
  );
  const [bulkCategoryId, setBulkCategoryId] = useState("");
  const [updatesJson, setUpdatesJson] = useState("");
  const [lastHandledSubmissionAt, setLastHandledSubmissionAt] = useState<number | null>(
    null,
  );
  const [lastUndoUpdates, setLastUndoUpdates] = useState<BulkTransactionUpdate[]>([]);
  const [lastOperationWasUndo, setLastOperationWasUndo] = useState(false);

  const [ruleMerchantContains, setRuleMerchantContains] = useState("");
  const [ruleCategoryId, setRuleCategoryId] = useState("");
  const [rules, setRules] = useState<TransactionRule[]>([]);

  const transactionsById = useMemo(
    () => new Map(transactions.map((transaction) => [transaction.id, transaction])),
    [transactions],
  );

  const categoryNameById = useMemo(
    () =>
      Object.fromEntries(
        categories.map((category) => [category.id, category.name]),
      ),
    [categories],
  );

  const accountNameById = useMemo(
    () =>
      Object.fromEntries(accounts.map((account) => [account.id, account.name])),
    [accounts],
  );

  const sortedTransactions = useMemo(
    () =>
      [...transactions].sort((left, right) => {
        const dateCompare = right.transaction_date.localeCompare(
          left.transaction_date,
        );

        if (dateCompare !== 0) {
          return dateCompare;
        }

        return right.updated_at.localeCompare(left.updated_at);
      }),
    [transactions],
  );

  const filteredTransactions = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    if (!normalizedQuery) {
      return sortedTransactions;
    }

    return sortedTransactions.filter((transaction) => {
      const accountName = accountNameById[transaction.account_id] ?? "";
      const categoryName = transaction.category_id
        ? categoryNameById[transaction.category_id] ?? ""
        : "";

      return (
        transaction.description.toLowerCase().includes(normalizedQuery) ||
        accountName.toLowerCase().includes(normalizedQuery) ||
        categoryName.toLowerCase().includes(normalizedQuery)
      );
    });
  }, [
    accountNameById,
    categoryNameById,
    searchQuery,
    sortedTransactions,
  ]);

  const visibleEditableTransactions = filteredTransactions.filter((transaction) =>
    isBulkEditable(transaction),
  );

  useEffect(() => {
    try {
      const storedRules = window.localStorage.getItem(RULES_STORAGE_KEY);
      if (!storedRules) {
        return;
      }

      const parsedRules = JSON.parse(storedRules) as TransactionRule[];
      if (!Array.isArray(parsedRules)) {
        return;
      }

      setRules(
        parsedRules.filter((rule) => {
          return (
            typeof rule.id === "string" &&
            typeof rule.merchantContains === "string" &&
            typeof rule.categoryId === "string" &&
            typeof rule.enabled === "boolean"
          );
        }),
      );
    } catch {
      setRules([]);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(RULES_STORAGE_KEY, JSON.stringify(rules));
  }, [rules]);

  useEffect(() => {
    try {
      const storedUndoUpdates = window.sessionStorage.getItem(
        LAST_BULK_UNDO_STORAGE_KEY,
      );

      if (!storedUndoUpdates) {
        return;
      }

      setLastUndoUpdates(normalizeBulkUpdates(JSON.parse(storedUndoUpdates)));
    } catch {
      setLastUndoUpdates([]);
    }
  }, []);

  useEffect(() => {
    if (!state.submittedAt || state.submittedAt === lastHandledSubmissionAt) {
      return;
    }

    setLastHandledSubmissionAt(state.submittedAt);

    if (state.ok) {
      const nextUndoUpdates = pendingUndoUpdatesRef.current;

      setLastUndoUpdates(nextUndoUpdates);
      if (nextUndoUpdates.length > 0) {
        window.sessionStorage.setItem(
          LAST_BULK_UNDO_STORAGE_KEY,
          JSON.stringify(nextUndoUpdates),
        );
      } else {
        window.sessionStorage.removeItem(LAST_BULK_UNDO_STORAGE_KEY);
      }

      emitShellToast({
        level: "success",
        title: lastOperationWasUndo ? "Undo complete" : "Bulk update complete",
        description: state.message ?? "Transactions were updated.",
      });
      setSelectedTransactionIds(new Set());
      setUpdatesJson("");
      pendingUndoUpdatesRef.current = [];
      setLastOperationWasUndo(false);
      router.refresh();
      return;
    }

    if (state.error) {
      pendingUndoUpdatesRef.current = [];
      setLastOperationWasUndo(false);
      emitShellToast({
        level: "error",
        title: "Bulk update failed",
        description: state.error,
        durationMs: 7000,
      });
    }
  }, [lastHandledSubmissionAt, lastOperationWasUndo, router, state]);

  function selectAllVisibleEditable() {
    setSelectedTransactionIds(
      new Set(visibleEditableTransactions.map((transaction) => transaction.id)),
    );
  }

  function clearSelection() {
    setSelectedTransactionIds(new Set());
  }

  function toggleTransactionSelection(transactionId: string, checked: boolean) {
    setSelectedTransactionIds((current) => {
      const next = new Set(current);
      if (checked) {
        next.add(transactionId);
      } else {
        next.delete(transactionId);
      }
      return next;
    });
  }

  function buildUndoUpdates(updates: BulkTransactionUpdate[]) {
    const undoUpdates: BulkTransactionUpdate[] = [];

    for (const update of updates) {
      const transaction = transactionsById.get(update.transaction_id);

      if (!transaction || !isBulkEditable(transaction)) {
        continue;
      }

      undoUpdates.push({
        transaction_id: transaction.id,
        category_id: transaction.category_id,
      });
    }

    return undoUpdates;
  }

  function submitBulkUpdates(
    updates: BulkTransactionUpdate[],
    options?: {
      isUndo?: boolean;
    },
  ) {
    if (updates.length === 0) {
      emitShellToast({
        level: "info",
        title: "No changes detected",
        description: "Nothing to update from your current selection.",
      });
      return;
    }

    pendingUndoUpdatesRef.current = buildUndoUpdates(updates);
    setLastOperationWasUndo(Boolean(options?.isUndo));

    setUpdatesJson(JSON.stringify(updates));
    window.requestAnimationFrame(() => {
      formRef.current?.requestSubmit();
    });
  }

  function applyBulkCategory() {
    if (!bulkCategoryId) {
      emitShellToast({
        level: "warning",
        title: "Choose a category",
        description: "Select a category before applying bulk updates.",
      });
      return;
    }

    const updates: BulkTransactionUpdate[] = [];

    for (const transactionId of selectedTransactionIds) {
      const transaction = transactionsById.get(transactionId);
      if (!transaction || !isBulkEditable(transaction)) {
        continue;
      }

      if (transaction.category_id === bulkCategoryId) {
        continue;
      }

      updates.push({
        transaction_id: transaction.id,
        category_id: bulkCategoryId,
      });
    }

    submitBulkUpdates(updates, { isUndo: false });
  }

  function createRule() {
    const normalizedMerchantContains = normalizeRuleInput(ruleMerchantContains);

    if (!normalizedMerchantContains || !ruleCategoryId) {
      emitShellToast({
        level: "warning",
        title: "Rule is incomplete",
        description: "Provide a merchant keyword and a category.",
      });
      return;
    }

    const nextRule: TransactionRule = {
      id: `${Date.now()}`,
      merchantContains: normalizedMerchantContains,
      categoryId: ruleCategoryId,
      enabled: true,
    };

    setRules((current) => [nextRule, ...current].slice(0, 30));
    setRuleMerchantContains("");
    setRuleCategoryId("");

    emitShellToast({
      level: "success",
      title: "Rule saved",
      description: "Use Apply Rules to recategorize matching transactions.",
    });
  }

  function applyRulesToScope() {
    const enabledRules = rules.filter((rule) => rule.enabled);

    if (enabledRules.length === 0) {
      emitShellToast({
        level: "warning",
        title: "No enabled rules",
        description: "Create or enable at least one rule first.",
      });
      return;
    }

    const scopedTransactions =
      selectedTransactionIds.size > 0
        ? filteredTransactions.filter((transaction) =>
            selectedTransactionIds.has(transaction.id),
          )
        : filteredTransactions;

    const updates: BulkTransactionUpdate[] = [];

    for (const transaction of scopedTransactions) {
      if (!isBulkEditable(transaction)) {
        continue;
      }

      const description = transaction.description.toLowerCase();
      const matchedRule = enabledRules.find((rule) =>
        description.includes(rule.merchantContains),
      );

      if (!matchedRule) {
        continue;
      }

      if (transaction.category_id === matchedRule.categoryId) {
        continue;
      }

      updates.push({
        transaction_id: transaction.id,
        category_id: matchedRule.categoryId,
      });
    }

    submitBulkUpdates(updates, { isUndo: false });
  }

  function undoLastBatch() {
    if (lastUndoUpdates.length === 0) {
      emitShellToast({
        level: "info",
        title: "Nothing to undo",
        description: "Apply a bulk update first to enable undo.",
      });
      return;
    }

    submitBulkUpdates(lastUndoUpdates, { isUndo: true });
  }

  return (
    <section className="panel wide-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Rules and bulk edit</p>
          <h3>Recategorize faster</h3>
        </div>
        <span className="pill">{selectedTransactionIds.size} selected</span>
      </div>

      <form ref={formRef} action={formAction} className="composer-form">
        <input type="hidden" name="updates_json" value={updatesJson} />
      </form>

      <div className="composer-grid three-columns">
        <label className="composer-field full-width">
          <span>Search transactions</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(event) => {
              setSearchQuery(event.target.value);
            }}
            placeholder="Search by merchant, account, or category"
          />
        </label>

        <label className="composer-field">
          <span>Bulk category</span>
          <select
            value={bulkCategoryId}
            onChange={(event) => {
              setBulkCategoryId(event.target.value);
            }}
          >
            <option value="">Select category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </label>

        <div className="composer-field">
          <span>Selection actions</span>
          <div className="composer-inline-actions">
            <button
              type="button"
              className="day-tray-close"
              onClick={selectAllVisibleEditable}
              disabled={isPending || visibleEditableTransactions.length === 0}
            >
              Select visible
            </button>
            <button
              type="button"
              className="day-tray-close"
              onClick={clearSelection}
              disabled={isPending || selectedTransactionIds.size === 0}
            >
              Clear
            </button>
            <button
              type="button"
              className="composer-submit"
              onClick={applyBulkCategory}
              disabled={isPending || selectedTransactionIds.size === 0 || !bulkCategoryId}
            >
              {isPending ? "Applying..." : "Apply to selected"}
            </button>
            <button
              type="button"
              className="day-tray-close"
              onClick={undoLastBatch}
              disabled={isPending || lastUndoUpdates.length === 0}
            >
              Undo last batch
            </button>
          </div>
        </div>
      </div>

      <section className="composer-preview">
        <p className="eyebrow">Automation rules</p>
        <h4>If merchant contains → category</h4>

        <div className="composer-grid three-columns">
          <label className="composer-field">
            <span>Merchant contains</span>
            <input
              type="text"
              value={ruleMerchantContains}
              onChange={(event) => {
                setRuleMerchantContains(event.target.value);
              }}
              placeholder="uber"
            />
          </label>

          <label className="composer-field">
            <span>Set category</span>
            <select
              value={ruleCategoryId}
              onChange={(event) => {
                setRuleCategoryId(event.target.value);
              }}
            >
              <option value="">Select category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>

          <div className="composer-field">
            <span>Rule actions</span>
            <div className="composer-inline-actions">
              <button
                type="button"
                className="day-tray-close"
                onClick={createRule}
                disabled={isPending}
              >
                Save rule
              </button>
              <button
                type="button"
                className="composer-submit"
                onClick={applyRulesToScope}
                disabled={isPending || rules.length === 0}
              >
                {isPending ? "Applying..." : "Apply rules"}
              </button>
            </div>
          </div>
        </div>

        {rules.length === 0 ? (
          <p className="composer-help">No rules yet. Add one to automate recategorization.</p>
        ) : (
          <div className="rule-list">
            {rules.map((rule) => (
              <div key={rule.id} className="rule-row">
                <div>
                  <strong>contains "{rule.merchantContains}"</strong>
                  <span>
                    set to {categoryNameById[rule.categoryId] ?? "Unknown category"}
                  </span>
                </div>
                <div className="composer-inline-actions">
                  <button
                    type="button"
                    className="day-tray-close"
                    onClick={() => {
                      setRules((current) =>
                        current.map((currentRule) =>
                          currentRule.id === rule.id
                            ? { ...currentRule, enabled: !currentRule.enabled }
                            : currentRule,
                        ),
                      );
                    }}
                  >
                    {rule.enabled ? "Enabled" : "Disabled"}
                  </button>
                  <button
                    type="button"
                    className="day-tray-close"
                    onClick={() => {
                      setRules((current) =>
                        current.filter((currentRule) => currentRule.id !== rule.id),
                      );
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Filtered ledger</p>
            <h3>{filteredTransactions.length} visible transactions</h3>
          </div>
          <span className="pill">Bulk updates skip transfers/opening balances</span>
        </div>

        <div className="activity-list">
          {filteredTransactions.map((transaction) => {
            const editable = isBulkEditable(transaction);
            const checked = selectedTransactionIds.has(transaction.id);
            const amountLabel = `${
              transaction.type === "income" ? "+" : "-"
            }${formatCurrency(Number(transaction.amount))}`;

            return (
              <div key={transaction.id} className="activity-row transaction-row-selectable">
                <label className="transaction-checkbox-field">
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={!editable || isPending}
                    onChange={(event) => {
                      toggleTransactionSelection(transaction.id, event.target.checked);
                    }}
                  />
                  <span>{editable ? "Select" : "Locked"}</span>
                </label>

                <div>
                  <strong>{transaction.description}</strong>
                  <span>
                    {new Date(`${transaction.transaction_date}T00:00:00`).toLocaleDateString(
                      "en-US",
                      {
                        month: "short",
                        day: "numeric",
                      },
                    )} · {accountNameById[transaction.account_id] ?? "Linked account"} · {categoryNameById[transaction.category_id ?? ""] ?? "No category"}
                  </span>
                </div>

                <span className={`amount ${transaction.type}`}>{amountLabel}</span>
              </div>
            );
          })}
        </div>
      </section>
    </section>
  );
}
