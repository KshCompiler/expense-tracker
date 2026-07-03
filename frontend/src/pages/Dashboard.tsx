import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { DashboardData } from '../types';
import { TrendChart } from '../components/TrendChart';
import './Dashboard.css';

const CATEGORY_COLORS: Record<string, string> = {
  Food: '#c17f24',
  Transport: '#1565c0',
  Shopping: '#7b1fa2',
  Bills: '#e65100',
  Entertainment: '#c2185b',
  Health: '#1a472a',
  Other: '#6b6b6b',
};

function categoryColor(category: string): string {
  return CATEGORY_COLORS[category] ?? '#6b6b6b';
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    api.get<DashboardData>('/dashboard').then(setData);
  }, []);

  if (!data) return null;

  const firstName = data.user.full_name.split(' ')[0];
  const trend = data.monthly_trend;
  const currentTotal = trend[trend.length - 1]?.total ?? 0;
  const previousTotal = trend.length >= 2 ? trend[trend.length - 2].total : null;
  let deltaPct: number | null = null;
  let trendDirection: 'up' | 'down' | 'flat' = 'flat';
  if (previousTotal !== null) {
    if (previousTotal > 0) {
      deltaPct = Math.abs(((currentTotal - previousTotal) / previousTotal) * 100);
      trendDirection = currentTotal > previousTotal ? 'up' : currentTotal < previousTotal ? 'down' : 'flat';
    } else if (currentTotal > 0) {
      deltaPct = 100;
      trendDirection = 'up';
    } else {
      deltaPct = 0;
    }
  }

  return (
    <div className="db-wrap">
      <div className="db-folio">
        <div className="db-folio-cover">
          <div className="db-folio-greeting">
            <h1>Hi, {firstName}</h1>
            <p>
              {data.today_date} · {data.current_time}
            </p>
          </div>
          <div className="db-action-group">
            <Link to="/income/add" className="db-add-btn db-add-income-btn">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z" />
              </svg>
              Add Income
            </Link>
            <Link to="/expenses/add" className="db-add-btn">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z" />
              </svg>
              Add Expense
            </Link>
          </div>
        </div>

        <div className="db-folio-seam">
          <span className="db-folio-seal" aria-hidden="true">
            ◈
          </span>
        </div>

        <div className="db-folio-ledger">
          <div className="db-ledger-col">
            <span className="db-ledger-label">Expenses</span>
            <span className="db-ledger-value neg">₹{data.total_expenses.toFixed(0)}</span>
            <span className="db-ledger-sub">This month</span>
          </div>
          <div className="db-ledger-col">
            <span className="db-ledger-label">Income</span>
            <span className="db-ledger-value pos">₹{data.total_income.toFixed(0)}</span>
            <span className="db-ledger-sub">This month</span>
          </div>
          <div className="db-ledger-col">
            <span className="db-ledger-label">Balance</span>
            <span className={`db-ledger-value ${data.remaining_balance >= 0 ? 'pos' : 'neg'}`}>
              ₹{data.remaining_balance.toFixed(0)}
            </span>
            <span className="db-ledger-sub">Income minus expenses</span>
          </div>
          <div className="db-ledger-col">
            <span className="db-ledger-label">Transactions</span>
            <span className="db-ledger-value">{data.transaction_count}</span>
            <span className="db-ledger-sub">This month</span>
          </div>
        </div>
      </div>

      <div className="db-main">
        <div className="db-chart-card">
          <div className="db-chart-header">
            <span className="db-section-title">Spending by Category</span>
            <span className="db-chart-total">₹{data.total_expenses.toFixed(0)}</span>
          </div>
          {data.categories.length > 0 ? (
            <>
              <div className="db-tally-bar">
                {data.categories.map((cat) => {
                  const width = data.total_expenses > 0 ? Math.round((cat.total / data.total_expenses) * 100) : 0;
                  return (
                    <div
                      key={cat.category}
                      className="db-tally-seg"
                      style={{ flex: `0 0 ${width}%`, background: categoryColor(cat.category) }}
                    />
                  );
                })}
              </div>
              <div className="db-legend">
                {data.categories.map((cat) => {
                  const width = data.total_expenses > 0 ? Math.round((cat.total / data.total_expenses) * 100) : 0;
                  return (
                    <div key={cat.category} className="db-legend-row">
                      <span className="db-legend-dot" style={{ background: categoryColor(cat.category) }} />
                      <span className="db-legend-name">{cat.category}</span>
                      <span className="db-legend-leader" />
                      <span className="db-legend-pct">{width}%</span>
                      <span className="db-legend-amt">₹{cat.total.toFixed(0)}</span>
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <div className="db-empty">No expenses this month yet.</div>
          )}
        </div>

        <div className="db-txn-card">
          <div className="db-chart-header">
            <span className="db-section-title">Recent Transactions</span>
            <Link to="/transactions" style={{ fontSize: '0.8rem', color: 'var(--accent)', fontWeight: 500 }}>
              View all
            </Link>
          </div>
          {data.has_transactions ? (
            <div className="db-txn-list">
              {data.recent_transactions.map((txn) => (
                <div className="db-txn-row" key={txn.id}>
                  <div className="db-txn-left">
                    <div className="db-txn-swatch" style={{ background: categoryColor(txn.category) }} />
                    <div className="db-txn-text">
                      <span className="db-txn-desc">{txn.description || txn.category}</span>
                      <div className="db-txn-meta">
                        <span>{txn.date}</span>
                        <span className={`db-txn-badge ${txn.category.toLowerCase()}`}>{txn.category}</span>
                      </div>
                    </div>
                  </div>
                  <span className="db-txn-amount">−₹{txn.amount.toFixed(0)}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="db-empty">No transactions yet.</div>
          )}
        </div>
      </div>

      <div className="db-trend-card">
        <div className="db-chart-header db-trend-header">
          <div>
            <span className="db-section-title">Spending Trend</span>
            <p className="db-trend-subtitle">Total expenses per month, last 6 months</p>
          </div>
          {currentTotal > 0 && (
            <div className="db-trend-header-right">
              <span className="db-chart-total">₹{currentTotal.toFixed(0)}</span>
              {deltaPct !== null && (
                <span className={`db-trend-delta ${trendDirection}`}>
                  {trendDirection === 'up' ? '▲' : trendDirection === 'down' ? '▼' : '—'} {deltaPct.toFixed(0)}%
                  vs last month
                </span>
              )}
            </div>
          )}
        </div>
        <TrendChart data={trend} />
      </div>

      <div className="ai-fab-wrap">
        <div className="ai-fab-tooltip">
          <span className="ai-fab-tooltip-title">Chat with Sage</span>
          <span className="ai-fab-tooltip-desc">Your AI finance assistant</span>
        </div>
        <Link to="/suggestions" className="ai-fab" aria-label="Chat with Sage">
          ✦
        </Link>
      </div>
    </div>
  );
}
