import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, ApiError } from '../api/client';
import { useToast } from '../context/ToastContext';
import { CategoryTilePicker } from '../components/CategoryTilePicker';
import { BillUploadDropzone } from '../components/BillUploadDropzone';
import { EXPENSE_CATEGORY_TILES } from '../components/categoryTiles';
import type { BillExtraction, BudgetStatus } from '../types';

export function AddExpense() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('');
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const checkBudgetThreshold = async (submittedCategory: string) => {
    try {
      const statuses = await api.get<BudgetStatus[]>('/budgets');
      const match = statuses.find((b) => b.category === submittedCategory);
      if (!match) return;
      if (match.status === 'over') {
        showToast(
          `You're ₹${Math.abs(match.remaining).toFixed(0)} over your ${submittedCategory} budget this month.`,
          'error'
        );
      } else if (match.status === 'warning') {
        showToast(
          `You've used ${match.percent_used.toFixed(0)}% of your ${submittedCategory} budget this month.`,
          'warning'
        );
      }
    } catch {
      // Best-effort only — never let this fail the already-successful expense save.
    }
  };

  const handleExtracted = (data: BillExtraction) => {
    if (data.amount != null) setAmount(String(data.amount));
    if (data.category) setCategory(data.category);
    if (data.date) setDate(data.date);
    if (data.description) setDescription(data.description);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!category) {
      showToast('Please select a category.', 'error');
      return;
    }
    if (!date) {
      showToast('Please select a date.', 'error');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/expenses', { amount, category, date, description: description || null });
      showToast('Expense added successfully!', 'success');
      await checkBudgetThreshold(category);
      navigate('/dashboard');
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'An error occurred while adding the expense. Please try again.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="exp-section">
      <div className="exp-container">
        <div className="entry-page-header">
          <div className="expense-badge">
            <svg className="expense-badge-arrow" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M6 2V10M6 10L2.5 6.5M6 10L9.5 6.5"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Expense Entry
          </div>
          <h1 className="auth-title">Add Expense</h1>
          <p className="auth-subtitle">Log a new expense to keep your finances on track.</p>
        </div>

        <div className="auth-card expense-card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <BillUploadDropzone
                endpoint="/expenses/extract-bill"
                fieldKey="category"
                idleText="Drop a bill photo here, or click to choose one"
                scanningText="Reading your bill…"
                emptyMessage="Nothing could be read from that image — make sure it's a clear bill or receipt, or enter the details manually."
                successMessage="Filled in from your bill — check it over before saving."
                onExtracted={handleExtracted}
              />
            </div>

            <div className="form-group">
              <label htmlFor="amount">Amount</label>
              <div className="amount-slip">
                <span className="amount-slip-currency">₹</span>
                <input
                  type="number"
                  id="amount"
                  className="amount-slip-input"
                  placeholder="0.00"
                  step="0.01"
                  min="0.01"
                  required
                  autoFocus
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Category</label>
              <CategoryTilePicker options={EXPENSE_CATEGORY_TILES} value={category} onChange={setCategory} />
            </div>

            <div className="form-group">
              <label htmlFor="date">Date</label>
              <input
                type="date"
                id="date"
                className="form-input"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">
                Description <span style={{ color: 'var(--ink-faint)', fontWeight: 400 }}>(optional)</span>
              </label>
              <textarea
                id="description"
                className="form-input"
                placeholder="What was this expense for?"
                rows={2}
                style={{ resize: 'vertical' }}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-submit expense-submit" disabled={submitting}>
                <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z" />
                </svg>
                Save Expense
              </button>
              <Link to="/dashboard" className="btn-cancel">
                Cancel
              </Link>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
