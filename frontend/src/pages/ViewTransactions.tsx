import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api, ApiError } from '../api/client';
import { useToast } from '../context/ToastContext';
import type { TransactionsPage } from '../types';
import './ViewTransactions.css';

export function ViewTransactions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { showToast } = useToast();

  const fromDate = searchParams.get('from_date') ?? '';
  const toDate = searchParams.get('to_date') ?? '';
  const q = searchParams.get('q') ?? '';
  const page = Number(searchParams.get('page') ?? '1');

  const [qInput, setQInput] = useState(q);
  const [fromInput, setFromInput] = useState(fromDate);
  const [toInput, setToInput] = useState(toDate);
  const [data, setData] = useState<TransactionsPage | null>(null);

  useEffect(() => {
    setQInput(q);
    setFromInput(fromDate);
    setToInput(toDate);
  }, [q, fromDate, toDate]);

  const load = () => {
    const params = new URLSearchParams();
    if (fromDate) params.set('from_date', fromDate);
    if (toDate) params.set('to_date', toDate);
    if (q) params.set('q', q);
    params.set('page', String(page));
    api.get<TransactionsPage>(`/transactions?${params.toString()}`).then(setData);
  };

  useEffect(load, [fromDate, toDate, q, page]);

  const filterActive = Boolean(fromDate || toDate || q);

  const applyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, string> = {};
    if (fromInput) params.from_date = fromInput;
    if (toInput) params.to_date = toInput;
    if (qInput) params.q = qInput;
    setSearchParams(params);
  };

  const clearFilters = () => {
    setSearchParams({});
  };

  const goToPage = (newPage: number) => {
    const params: Record<string, string> = { page: String(newPage) };
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    if (q) params.q = q;
    setSearchParams(params);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this expense? This cannot be undone.')) return;
    try {
      await api.delete(`/expenses/${id}`);
      showToast('Expense deleted successfully!', 'success');
      load();
    } catch (err) {
      showToast(
        err instanceof ApiError ? err.message : 'An error occurred while deleting the expense. Please try again.',
        'error',
      );
    }
  };

  const activeChipText = [q ? `“${q}”` : null, fromDate && toDate ? `${fromDate} → ${toDate}` : fromDate ? `From ${fromDate}` : toDate ? `Up to ${toDate}` : null]
    .filter(Boolean)
    .join(' · ');

  return (
    <div className="txn-wrap">
      <div className="txn-header">
        <h1 className="txn-title">All Transactions</h1>
        <Link to="/expenses/add" className="txn-add-btn">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
            <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z" />
          </svg>
          Add Expense
        </Link>
      </div>

      <form className="txn-toolbar" onSubmit={applyFilters}>
        <div className="toolbar-search-row">
          <div className="search-wrap">
            <span className="search-icon">
              <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
                <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.099zm-5.242 1.156a5.5 5.5 0 1 1 0-11 5.5 5.5 0 0 1 0 11z" />
              </svg>
            </span>
            <input
              type="text"
              className="filter-input search-input"
              placeholder="Search by description…"
              autoComplete="off"
              value={qInput}
              onChange={(e) => setQInput(e.target.value)}
            />
          </div>
        </div>

        <div className="toolbar-top">
          <span className="toolbar-label">
            <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
              <path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z" />
            </svg>
            Date range
          </span>

          <div className="date-range">
            <div className="date-input-wrap">
              <input
                type="date"
                className="filter-input"
                value={fromInput}
                onChange={(e) => setFromInput(e.target.value)}
              />
            </div>
            <span className="range-arrow">→</span>
            <div className="date-input-wrap">
              <input
                type="date"
                className="filter-input"
                value={toInput}
                onChange={(e) => setToInput(e.target.value)}
              />
            </div>
          </div>

          <div className="toolbar-actions">
            <button type="submit" className="filter-btn">
              Apply
            </button>
          </div>
        </div>

        {filterActive && (
          <div className="toolbar-active-bar">
            <span className="active-chip">
              <span className="active-chip-dot" />
              <span className="active-chip-text">{activeChipText}</span>
              <span className="active-chip-count">{data?.total ?? 0}</span>
            </span>
            <button type="button" className="filter-clear" onClick={clearFilters}>
              × Clear filter
            </button>
          </div>
        )}
      </form>

      {data && data.invalid_range ? (
        <div className="txn-card">
          <div className="empty-state">
            <span className="empty-icon">📅</span>
            <p>'From' date must be on or before 'To' date. Adjust the range and try again.</p>
          </div>
        </div>
      ) : (
        data && (
          <>
            <div className="txn-card">
              {data.items.length > 0 ? (
                <table className="transactions-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Category</th>
                      <th>Description</th>
                      <th>Amount</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((txn) => (
                      <tr key={txn.id}>
                        <td>{txn.date}</td>
                        <td>
                          <span className={`category-tag ${txn.category.toLowerCase()}`}>{txn.category}</span>
                        </td>
                        <td>{txn.description || '—'}</td>
                        <td>
                          <strong>₹{txn.amount.toFixed(2)}</strong>
                        </td>
                        <td className="action-cell">
                          <Link to={`/expenses/${txn.id}/edit`} className="action-link">
                            Edit
                          </Link>
                          <button type="button" className="delete-btn" onClick={() => handleDelete(txn.id)}>
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">
                  <span className="empty-icon">📋</span>
                  <p>No transactions yet. Start tracking your spending!</p>
                  <Link to="/expenses/add" className="btn-primary">
                    Add your first expense
                  </Link>
                </div>
              )}
            </div>

            {data.total_pages > 1 && (
              <div className="txn-pagination">
                <span className="pg-summary">
                  Page {data.page} of {data.total_pages} · {data.total} result{data.total !== 1 ? 's' : ''}
                </span>
                <div className="pg-controls">
                  {data.page > 1 ? (
                    <button type="button" className="pg-btn" onClick={() => goToPage(data.page - 1)}>
                      ← Prev
                    </button>
                  ) : (
                    <span className="pg-btn disabled">← Prev</span>
                  )}
                  {data.page < data.total_pages ? (
                    <button type="button" className="pg-btn" onClick={() => goToPage(data.page + 1)}>
                      Next →
                    </button>
                  ) : (
                    <span className="pg-btn disabled">Next →</span>
                  )}
                </div>
              </div>
            )}
          </>
        )
      )}
    </div>
  );
}
