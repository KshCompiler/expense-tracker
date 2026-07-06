import { useEffect, useState } from 'react';
import { api, ApiError } from '../api/client';
import { useToast } from '../context/ToastContext';
import { BudgetStubGauge } from '../components/BudgetStubGauge';
import { BudgetForm } from '../components/BudgetForm';
import { EXPENSE_CATEGORY_TILES, OVERALL_BUDGET_TILE } from '../components/categoryTiles';
import type { BudgetStatus } from '../types';
import './Budgets.css';

const ALL_BUDGET_TILES = [...EXPENSE_CATEGORY_TILES, OVERALL_BUDGET_TILE];

function tileFor(category: string) {
  return ALL_BUDGET_TILES.find((t) => t.value === category);
}

function statusCaption(budget: BudgetStatus): string {
  if (budget.status === 'over') {
    return `₹${Math.abs(budget.remaining).toFixed(0)} over budget`;
  }
  return `${budget.percent_used.toFixed(0)}% used · ₹${Math.max(budget.remaining, 0).toFixed(0)} left`;
}

export function Budgets() {
  const { showToast } = useToast();
  const [budgets, setBudgets] = useState<BudgetStatus[] | null>(null);
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const load = () => {
    api.get<BudgetStatus[]>('/budgets').then(setBudgets);
  };

  useEffect(load, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this budget? This cannot be undone.')) return;
    try {
      await api.delete(`/budgets/${id}`);
      showToast('Budget deleted successfully!', 'success');
      load();
    } catch (err) {
      showToast(
        err instanceof ApiError ? err.message : 'An error occurred while deleting the budget. Please try again.',
        'error'
      );
    }
  };

  const closeForms = () => {
    setAdding(false);
    setEditingId(null);
  };

  const handleSaved = () => {
    closeForms();
    load();
  };

  if (!budgets) return null;

  const usedCategories = budgets.map((b) => b.category);
  const totalBudgeted = budgets.reduce((sum, b) => sum + b.monthly_limit, 0);
  const totalSpent = budgets.reduce((sum, b) => sum + b.spent, 0);
  const totalRemaining = totalBudgeted - totalSpent;
  const overCount = budgets.filter((b) => b.status === 'over').length;

  return (
    <div className="budgets-wrap">
      <div className="bl-folio">
        <div className="bl-cover">
          <div className="bl-cover-text">
            <h1>Monthly Budgets</h1>
            <p>Your limits, tracked live against what you've actually spent.</p>
          </div>
          {!adding && (
            <button type="button" className="bl-add-btn" onClick={() => setAdding(true)}>
              + Add Budget
            </button>
          )}
        </div>

        {budgets.length > 0 && (
          <>
            <div className="bl-seam">
              <span className="bl-seal" aria-hidden="true">
                ◈
              </span>
            </div>

            <div className="bl-summary">
              <div className="bl-summary-col">
                <span className="bl-summary-label">Budgeted</span>
                <span className="bl-summary-value">₹{totalBudgeted.toFixed(0)}</span>
              </div>
              <div className="bl-summary-col">
                <span className="bl-summary-label">Spent</span>
                <span className="bl-summary-value">₹{totalSpent.toFixed(0)}</span>
              </div>
              <div className="bl-summary-col">
                <span className="bl-summary-label">Remaining</span>
                <span className={`bl-summary-value ${totalRemaining < 0 ? 'neg' : 'pos'}`}>
                  ₹{totalRemaining.toFixed(0)}
                </span>
              </div>
              <div className="bl-summary-col">
                <span className="bl-summary-label">Over Budget</span>
                <span className={`bl-summary-value ${overCount > 0 ? 'neg' : ''}`}>{overCount}</span>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="bl-sheet">
        {adding && (
          <div className="bl-line bl-line--form">
            <BudgetForm mode="create" excludedCategories={usedCategories} onSaved={handleSaved} onCancel={closeForms} />
          </div>
        )}

        {budgets.length === 0 && !adding ? (
          <div className="empty-state">
            <span className="empty-icon">📔</span>
            <p>This ledger page is blank — write in your first budget to start tracking a limit.</p>
            <button type="button" className="btn-primary" onClick={() => setAdding(true)}>
              + Add Budget
            </button>
          </div>
        ) : (
          budgets.map((budget) => {
            const tile = tileFor(budget.category);
            return (
              <div
                key={budget.id}
                className={`bl-line ${budget.status === 'over' ? 'bl-line--over' : ''}`}
              >
                {editingId === budget.id ? (
                  <BudgetForm
                    mode="edit"
                    budgetId={budget.id}
                    initialCategory={budget.category}
                    initialLimit={budget.monthly_limit}
                    excludedCategories={usedCategories.filter((c) => c !== budget.category)}
                    onSaved={handleSaved}
                    onCancel={closeForms}
                  />
                ) : (
                  <>
                    <BudgetStubGauge percentUsed={budget.percent_used} status={budget.status} color={tile?.color ?? '#6b6b6b'} />
                    <div className="bl-line-text">
                      <span className="bl-line-name">
                        <span className="bl-line-icon">{tile?.icon}</span>
                        {budget.category}
                      </span>
                      <span className="bl-line-figures">
                        ₹{budget.spent.toFixed(0)} of ₹{budget.monthly_limit.toFixed(0)} · {statusCaption(budget)}
                      </span>
                    </div>
                    <div className="bl-line-actions">
                      <button type="button" className="action-link" onClick={() => setEditingId(budget.id)}>
                        Edit
                      </button>
                      <button type="button" className="delete-btn" onClick={() => handleDelete(budget.id)}>
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })
        )}

        {budgets.length > 0 && !adding && (
          <button type="button" className="bl-add-line" onClick={() => setAdding(true)}>
            + Write a new line
          </button>
        )}
      </div>
    </div>
  );
}
