export interface User {
  id: number;
  full_name: string;
  email: string;
}

export interface Expense {
  id: number;
  user_id: number;
  amount: number;
  category: string;
  date: string;
  description: string | null;
  created_at: string;
}

export interface CategoryTotal {
  category: string;
  total: number;
}

export interface MonthlyTrendPoint {
  year_month: string;
  label: string;
  total: number;
}

export type BudgetHealthStatus = 'ok' | 'warning' | 'over';

export interface Budget {
  id: number;
  user_id: number;
  category: string;
  monthly_limit: number;
  created_at: string;
  updated_at: string;
}

export interface BudgetStatus {
  id: number;
  category: string;
  monthly_limit: number;
  spent: number;
  percent_used: number;
  remaining: number;
  status: BudgetHealthStatus;
}

export interface BudgetSuggestion {
  suggested_limit: number;
  rationale: string;
}

export interface DashboardData {
  user: User;
  today_date: string;
  current_time: string;
  total_expenses: number;
  total_income: number;
  remaining_balance: number;
  transaction_count: number;
  categories: CategoryTotal[];
  recent_transactions: Expense[];
  has_transactions: boolean;
  monthly_trend: MonthlyTrendPoint[];
  budgets: BudgetStatus[];
}

export interface TransactionsPage {
  items: Expense[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  invalid_range: boolean;
}

export interface BillExtraction {
  amount: number | null;
  date: string | null;
  description: string | null;
  category?: string | null;
  source?: string | null;
}

export interface Profile {
  id: number;
  full_name: string;
  email: string;
  created_at: string;
  total_expenses_all_time: number;
  total_income_all_time: number;
  transaction_count_all_time: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface MessageResponse {
  message: string;
}

export const VALID_CATEGORIES = [
  'Food',
  'Transport',
  'Bills',
  'Health',
  'Entertainment',
  'Shopping',
  'Other',
] as const;

export const VALID_INCOME_SOURCES = [
  'Salary',
  'Freelance',
  'Business',
  'Investment',
  'Gift',
  'Other',
] as const;

export type ToastCategory = 'success' | 'error' | 'info' | 'warning';
