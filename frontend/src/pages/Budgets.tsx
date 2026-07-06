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

  return (
    <div className="budgets-wrap">
      <div className="budgets-header">
        <h1 className="budgets-title">Set Monthly Budgets</h1>
        {!adding && (
          <button type="button" className="budgets-add-btn" onClick={() => setAdding(true)}>
            + Add Budget
          </button>
        )}
      </div>

      {adding && (
        <div className="budget-card budget-card--form">
          <BudgetForm mode="create" excludedCategories={usedCategories} onSaved={handleSaved} onCancel={closeForms} />
        </div>
      )}

      {budgets.length === 0 && !adding ? (
        <div className="budget-card">
          <div className="empty-state">
            <span className="empty-icon">📔</span>
            <p>No budgets set — add one to start tracking a limit.</p>
            <button type="button" className="btn-primary" onClick={() => setAdding(true)}>
              + Add Budget
            </button>
          </div>
        </div>
      ) : (
        budgets.map((budget) => {
          const tile = tileFor(budget.category);
          return (
            <div key={budget.id} className={`budget-card budget-row ${budget.status === 'over' ? 'budget-row--over' : ''}`}>
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
                  <div className="budget-row-text">
                    <span className="budget-row-name">
                      <span className="budget-row-icon">{tile?.icon}</span>
                      {budget.category}
                    </span>
                    <span className="budget-row-figures">
                      ₹{budget.spent.toFixed(0)} of ₹{budget.monthly_limit.toFixed(0)} · {statusCaption(budget)}
                    </span>
                  </div>
                  <div className="budget-row-actions">
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
    </div>
  );
}
