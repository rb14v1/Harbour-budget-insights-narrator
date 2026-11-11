export interface User {
  id: number;
  email: string;
  full_name: string;
  date_joined: string;
}

export interface Category {
  id: number;
  name: string;
  created_at: string;
}

export type TransactionType = "income" | "expense";

export interface Transaction {
  id: number;
  category: number;
  category_name: string;
  transaction_type: TransactionType;
  amount: string;
  description: string;
  transaction_date: string;
  created_at: string;
}

export interface MonthlyInsightResponse {
  month: string;
  total_income: number;
  total_expenses: number;
  category_totals: Record<string, number>;
  prior_month_category_totals: Record<string, number>;
  narrative: string | null;
  generated_at: string | null;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
