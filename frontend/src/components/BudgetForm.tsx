import { useState, type FormEvent } from 'react';
import { api, ApiError } from '../api/client';
import { useToast } from '../context/ToastContext';
import { CategoryTilePicker } from './CategoryTilePicker';
import { EXPENSE_CATEGORY_TILES, OVERALL_BUDGET_TILE } from './categoryTiles';
import type { BudgetSuggestion } from '../types';

interface BudgetFormProps {
  mode: 'create' | 'edit';
  initialCategory?: string;
  initialLimit?: number;
  budgetId?: number;
  excludedCategories: string[];
  onSaved: () => void;
  onCancel: () => void;
}

const ALL_BUDGET_TILES = [...EXPENSE_CATEGORY_TILES, OVERALL_BUDGET_TILE];

export function BudgetForm({
  mode,
  initialCategory,
  initialLimit,
  budgetId,
  excludedCategories,
  onSaved,
  onCancel,
}: BudgetFormProps) {
  const { showToast } = useToast();

  const [category, setCategory] = useState(initialCategory ?? '');
  const [amount, setAmount] = useState(initialLimit != null ? String(initialLimit) : '');
  const [rationale, setRationale] = useState<string | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const lockedTile = mode === 'edit' ? ALL_BUDGET_TILES.find((t) => t.value === category) : undefined;
  const pickerOptions = ALL_BUDGET_TILES.filter((t) => !excludedCategories.includes(t.value));

  const handleSuggest = async () => {
    if (!category) {
      showToast('Choose a category first.', 'error');
      return;
    }
    setSuggesting(true);
    try {
      const suggestion = await api.get<BudgetSuggestion>(`/budgets/suggest/${category}`);
      setAmount(String(suggestion.suggested_limit));
      setRationale(suggestion.rationale);
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Could not get a suggestion right now.', 'error');
    } finally {
      setSuggesting(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!category) {
      showToast('Please select a category.', 'error');
      return;
    }

    setSubmitting(true);
    try {
      if (mode === 'create') {
        await api.post('/budgets', { category, monthly_limit: amount });
        showToast('Budget added successfully!', 'success');
      } else {
        await api.put(`/budgets/${budgetId}`, { monthly_limit: amount });
        showToast('Budget updated successfully!', 'success');
      }
      onSaved();
    } catch (err) {
      showToast(
        err instanceof ApiError ? err.message : 'An error occurred while saving the budget. Please try again.',
        'error'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="budget-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Category</label>
        {mode === 'edit' ? (
          <div className="budget-form-locked-category">
            <span className="cat-icon">{lockedTile?.icon}</span>
            <span>{lockedTile?.label ?? category}</span>
          </div>
        ) : (
          <CategoryTilePicker options={pickerOptions} value={category} onChange={setCategory} />
        )}
      </div>

      <div className="form-group">
        <div className="budget-form-limit-header">
          <label htmlFor="budget-limit">Monthly limit</label>
          <button
            type="button"
            className="budget-suggest-btn"
            onClick={handleSuggest}
            disabled={suggesting || !category}
          >
            {suggesting ? 'Thinking…' : '✦ Suggest a limit'}
          </button>
        </div>
        <div className="amount-slip">
          <span className="amount-slip-currency">₹</span>
          <input
            type="number"
            id="budget-limit"
            className="amount-slip-input"
            placeholder="0.00"
            step="0.01"
            min="0.01"
            required
            value={amount}
            onChange={(e) => {
              setAmount(e.target.value);
              setRationale(null);
            }}
          />
        </div>
        {rationale && <p className="budget-suggest-rationale">{rationale}</p>}
      </div>

      <div className="form-actions budget-form-actions">
        <button type="submit" className="btn-submit" disabled={submitting}>
          {mode === 'create' ? 'Add Budget' : 'Save Changes'}
        </button>
        <button type="button" className="btn-cancel" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
