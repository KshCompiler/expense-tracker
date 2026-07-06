import type { BudgetHealthStatus } from '../types';

interface BudgetStubGaugeProps {
  percentUsed: number;
  status: BudgetHealthStatus;
  color: string;
  size?: 'sm' | 'md';
}

export function BudgetStubGauge({ percentUsed, status, color, size = 'md' }: BudgetStubGaugeProps) {
  const fillPct = Math.max(0, Math.min(100, percentUsed));

  return (
    <div className={`budget-stub budget-stub--${size}`}>
      <span className="budget-stub-dot" style={{ background: color }} aria-hidden="true" />
      <div className="budget-stub-track">
        <div className={`budget-stub-fill budget-stub-fill--${status}`} style={{ height: `${fillPct}%` }} />
      </div>
      {status === 'over' && (
        <span className="budget-stamp-over" aria-label="Over budget">
          OVER
        </span>
      )}
    </div>
  );
}
