import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, ApiError } from '../api/client';
import { useToast } from '../context/ToastContext';
import { CategoryTilePicker } from '../components/CategoryTilePicker';
import { EXPENSE_CATEGORY_TILES } from '../components/categoryTiles';
import type { Expense } from '../types';

export function EditExpense() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('');
  const [date, setDate] = useState('');
  const [description, setDescription] = useState('');
  const [loaded, setLoaded] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .get<Expense>(`/expenses/${id}`)
      .then((expense) => {
        setAmount(expense.amount.toFixed(2));
        setCategory(expense.category);
        setDate(expense.date);
        setDescription(expense.description ?? '');
        setLoaded(true);
      })
      .catch((err) => {
        showToast(
          err instanceof ApiError ? err.message : "Expense not found or you don't have permission to edit it.",
          'error',
        );
        navigate('/transactions');
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

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
      await api.put(`/expenses/${id}`, { amount, category, date, description: description || null });
      showToast('Expense updated successfully!', 'success');
      navigate('/transactions');
    } catch (err) {
      showToast(
        err instanceof ApiError ? err.message : 'An error occurred while updating the expense. Please try again.',
        'error',
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (!loaded) return null;

  return (
    <section className="exp-section">
      <div className="exp-container">
        <div className="auth-header">
          <h1 className="auth-title">Edit Expense</h1>
          <p className="auth-subtitle">Update the details of this expense.</p>
        </div>

        <div className="auth-card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="amount">Amount (₹)</label>
              <input
                type="number"
                id="amount"
                className="form-input"
                placeholder="0.00"
                step="0.01"
                min="0.01"
                required
                autoFocus
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
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

            <button type="submit" className="btn-submit" disabled={submitting}>
              Update Expense
            </button>
          </form>
        </div>

        <p className="auth-switch">
          <Link to="/transactions">&larr; Cancel</Link>
        </p>
      </div>
    </section>
  );
}
