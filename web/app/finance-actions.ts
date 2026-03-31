"use server";

import { revalidatePath } from "next/cache";

import {
  cloneBudget,
  createAccount,
  createBudget,
  createRecurringRule,
  createTransaction,
  updateTransaction,
} from "@/lib/finance-client";

export type FinanceActionState = {
  error: string | null;
  ok: boolean;
  message: string | null;
  submittedAt: number | null;
};

type BulkTransactionUpdate = {
  transaction_id: string;
  category_id: string | null;
};

function asString(formData: FormData, key: string) {
  return String(formData.get(key) ?? "").trim();
}

function ensurePositiveDecimal(raw: string, fieldName: string) {
  const value = Number(raw);
  if (Number.isNaN(value) || value <= 0) {
    throw new Error(`${fieldName} must be greater than zero.`);
  }

  return raw;
}

function ensureNonNegativeDecimal(raw: string, fieldName: string) {
  const value = Number(raw);
  if (Number.isNaN(value) || value < 0) {
    throw new Error(`${fieldName} must be zero or greater.`);
  }

  return raw;
}

function ensureDate(raw: string, fieldName: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    throw new Error(`${fieldName} must use YYYY-MM-DD format.`);
  }

  return raw;
}

function errorMessage(error: unknown) {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Unable to complete this request.";
}

function failureState(message: string): FinanceActionState {
  return {
    error: message,
    ok: false,
    message,
    submittedAt: Date.now(),
  };
}

function successState(message: string): FinanceActionState {
  return {
    error: null,
    ok: true,
    message,
    submittedAt: Date.now(),
  };
}

function ensureInterval(raw: string) {
  const value = Number(raw);
  if (!Number.isInteger(value) || value < 1) {
    throw new Error("Interval must be a whole number greater than zero.");
  }

  return value;
}

function parseBulkUpdates(raw: string): BulkTransactionUpdate[] {
  let parsed: unknown;

  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error("Invalid bulk update payload.");
  }

  if (!Array.isArray(parsed) || parsed.length === 0) {
    throw new Error("No transaction updates were provided.");
  }

  if (parsed.length > 250) {
    throw new Error("Bulk update limit is 250 transactions per action.");
  }

  return parsed.map((item) => {
    if (typeof item !== "object" || item === null) {
      throw new Error("Invalid transaction update entry.");
    }

    const candidate = item as {
      transaction_id?: unknown;
      category_id?: unknown;
    };

    if (
      typeof candidate.transaction_id !== "string" ||
      candidate.transaction_id.trim().length === 0
    ) {
      throw new Error("Each bulk update requires a valid transaction id.");
    }

    if (
      candidate.category_id !== null &&
      candidate.category_id !== undefined &&
      typeof candidate.category_id !== "string"
    ) {
      throw new Error("Category id must be a string or null.");
    }

    return {
      transaction_id: candidate.transaction_id.trim(),
      category_id:
        candidate.category_id === undefined
          ? null
          : (candidate.category_id as string | null),
    };
  });
}

export async function createAccountAction(
  _previousState: FinanceActionState,
  formData: FormData,
): Promise<FinanceActionState> {
  const name = asString(formData, "name");
  const accountType = asString(formData, "account_type");
  const openingBalance = asString(formData, "opening_balance");

  if (!name) {
    return failureState("Account name is required.");
  }

  if (accountType !== "checking" && accountType !== "savings") {
    return failureState("Invalid account type.");
  }

  try {
    await createAccount({
      name,
      account_type: accountType,
      opening_balance: openingBalance
        ? ensureNonNegativeDecimal(openingBalance, "Opening balance")
        : undefined,
    });
  } catch (error) {
    return failureState(errorMessage(error));
  }

  revalidatePath("/accounts");
  revalidatePath("/");
  return successState("Account created.");
}

export async function createTransactionAction(
  _previousState: FinanceActionState,
  formData: FormData,
): Promise<FinanceActionState> {
  const description = asString(formData, "description");
  const amount = asString(formData, "amount");
  const transactionType = asString(formData, "type");
  const transactionDate = asString(formData, "transaction_date");
  const accountId = asString(formData, "account_id");
  const categoryId = asString(formData, "category_id");

  if (!description) {
    return failureState("Description is required.");
  }

  if (transactionType !== "income" && transactionType !== "expense") {
    return failureState("Invalid transaction type.");
  }

  if (!accountId) {
    return failureState("Account is required.");
  }

  try {
    await createTransaction({
      description,
      amount: ensurePositiveDecimal(amount, "Amount"),
      type: transactionType,
      transaction_date: ensureDate(transactionDate, "Transaction date"),
      account_id: accountId,
      category_id: categoryId || undefined,
    });
  } catch (error) {
    return failureState(errorMessage(error));
  }

  revalidatePath("/transactions");
  revalidatePath("/budget");
  revalidatePath("/");
  return successState("Transaction created.");
}

export async function bulkUpdateTransactionsAction(
  _previousState: FinanceActionState,
  formData: FormData,
): Promise<FinanceActionState> {
  const updatesRaw = asString(formData, "updates_json");

  if (!updatesRaw) {
    return failureState("No bulk updates were provided.");
  }

  let updates: BulkTransactionUpdate[];

  try {
    updates = parseBulkUpdates(updatesRaw);
  } catch (error) {
    return failureState(errorMessage(error));
  }

  let updatedCount = 0;
  const failures: string[] = [];

  for (const update of updates) {
    try {
      await updateTransaction(update.transaction_id, {
        category_id: update.category_id,
      });
      updatedCount += 1;
    } catch (error) {
      failures.push(errorMessage(error));
    }
  }

  if (updatedCount > 0) {
    revalidatePath("/transactions");
    revalidatePath("/budget");
    revalidatePath("/");
  }

  if (updatedCount === 0) {
    return failureState(
      failures[0] ?? "None of the selected transactions could be updated.",
    );
  }

  const failureSuffix =
    failures.length > 0 ? ` ${failures.length} item(s) failed to update.` : "";

  return successState(
    `${updatedCount} transaction(s) updated.${failureSuffix}`,
  );
}

export async function createBudgetAction(
  _previousState: FinanceActionState,
  formData: FormData,
): Promise<FinanceActionState> {
  const name = asString(formData, "name");
  const amount = asString(formData, "amount");
  const periodStart = asString(formData, "period_start");
  const periodEnd = asString(formData, "period_end");
  const categoryId = asString(formData, "category_id");
  const templateBudgetId = asString(formData, "template_budget_id");

  try {
    const normalizedStart = ensureDate(periodStart, "Start date");
    const normalizedEnd = ensureDate(periodEnd, "End date");

    if (normalizedEnd < normalizedStart) {
      return failureState("End date must be on or after start date.");
    }

    if (templateBudgetId) {
      await cloneBudget({
        source_budget_id: templateBudgetId,
        period_start: normalizedStart,
        period_end: normalizedEnd,
        name: name || undefined,
        amount: amount ? ensurePositiveDecimal(amount, "Amount") : undefined,
      });

      revalidatePath("/budget");
      revalidatePath("/transactions");
      revalidatePath("/");
      return successState("Budget created from template.");
    }

    if (!name) {
      return failureState("Budget name is required.");
    }

    if (!categoryId) {
      return failureState("Category is required.");
    }

    await createBudget({
      name,
      amount: ensurePositiveDecimal(amount, "Amount"),
      period_start: normalizedStart,
      period_end: normalizedEnd,
      category_id: categoryId,
    });
  } catch (error) {
    return failureState(errorMessage(error));
  }

  revalidatePath("/budget");
  revalidatePath("/transactions");
  revalidatePath("/");
  return successState("Budget created.");
}

export async function createRecurringRuleAction(
  _previousState: FinanceActionState,
  formData: FormData,
): Promise<FinanceActionState> {
  const description = asString(formData, "description");
  const amount = asString(formData, "amount");
  const frequency = asString(formData, "frequency");
  const interval = asString(formData, "interval");
  const startDate = asString(formData, "start_date");
  const endDate = asString(formData, "end_date");
  const weekendAdjustment = asString(formData, "weekend_adjustment");
  const accountId = asString(formData, "account_id");

  if (!description) {
    return failureState("Description is required.");
  }

  if (!accountId) {
    return failureState("Account is required.");
  }

  if (
    frequency !== "daily" &&
    frequency !== "weekly" &&
    frequency !== "monthly" &&
    frequency !== "yearly"
  ) {
    return failureState("Invalid frequency.");
  }

  if (
    weekendAdjustment !== "keep" &&
    weekendAdjustment !== "following" &&
    weekendAdjustment !== "preceding"
  ) {
    return failureState("Invalid weekend adjustment.");
  }

  try {
    const normalizedStart = ensureDate(startDate, "Start date");
    const normalizedEnd = endDate ? ensureDate(endDate, "End date") : undefined;

    if (normalizedEnd && normalizedEnd < normalizedStart) {
      return failureState("End date must be on or after start date.");
    }

    await createRecurringRule({
      description,
      amount: ensurePositiveDecimal(amount, "Amount"),
      type: "expense",
      frequency,
      interval: ensureInterval(interval),
      start_date: normalizedStart,
      end_date: normalizedEnd,
      weekend_adjustment: weekendAdjustment,
      account_id: accountId,
    });
  } catch (error) {
    return failureState(errorMessage(error));
  }

  revalidatePath("/recurring");
  revalidatePath("/calendar");
  revalidatePath("/");
  return successState("Recurring expense created.");
}
