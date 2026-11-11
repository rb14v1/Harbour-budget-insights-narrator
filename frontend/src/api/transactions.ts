import { apiClient } from "./client";
import type { Paginated, Transaction, TransactionType } from "../types";

export interface TransactionInput {
  category: number;
  transaction_type: TransactionType;
  amount: string;
  description?: string;
  transaction_date: string;
}

export function listTransactions(month?: string) {
  return apiClient.get<Paginated<Transaction>>("/transactions/", {
    params: { page_size: 100, ...(month ? { month } : {}) },
  });
}

export function createTransaction(data: TransactionInput) {
  return apiClient.post<Transaction>("/transactions/", data);
}

export function updateTransaction(id: number, data: Partial<TransactionInput>) {
  return apiClient.patch<Transaction>(`/transactions/${id}/`, data);
}

export function deleteTransaction(id: number) {
  return apiClient.delete(`/transactions/${id}/`);
}
