import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis } from 'recharts';
import type { MonthlyTrendPoint } from '../types';

const REGULAR_FILL = '#1a472a';
const REGULAR_OPACITY = 0.4;
const CURRENT_FILL = '#c17f24';

function formatCurrencyShort(amount: number): string {
  if (amount >= 1000) {
    const value = amount / 1000;
    return `₹${value === Math.trunc(value) ? value.toFixed(0) : value.toFixed(1)}k`;
  }
  return `₹${amount.toFixed(0)}`;
}

interface TooltipPayloadItem {
  payload: MonthlyTrendPoint;
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div
      style={{
        background: 'var(--ink)',
        color: 'var(--paper)',
        padding: '0.5rem 0.75rem',
        borderRadius: 'var(--radius-sm)',
        fontSize: '0.8rem',
      }}
    >
      {point.label} · {formatCurrencyShort(point.total)}
    </div>
  );
}

export function TrendChart({ data }: { data: MonthlyTrendPoint[] }) {
  const hasData = data.some((point) => point.total > 0);
  const currentMonth = data[data.length - 1]?.year_month;

  if (!hasData) {
    return <div className="db-empty">Not enough spending history yet.</div>;
  }

  return (
    <div className="db-trend-chart-wrap">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 24, right: 8, bottom: 4, left: 8 }}>
          <XAxis
            dataKey="label"
            axisLine={{ stroke: 'var(--border)' }}
            tickLine={false}
            tick={{ fontSize: 11, fill: 'var(--ink-faint)' }}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--border-soft)' }} />
          <Bar dataKey="total" radius={[4, 4, 0, 0]} maxBarSize={48} label={renderValueLabel}>
            {data.map((point) => (
              <Cell
                key={point.year_month}
                fill={point.year_month === currentMonth ? CURRENT_FILL : REGULAR_FILL}
                fillOpacity={point.year_month === currentMonth ? 1 : REGULAR_OPACITY}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function renderValueLabel(props: unknown) {
  const { x, y, width, value } = props as { x: number; y: number; width: number; value: number };
  if (!value) return <g />;
  return (
    <text
      x={x + width / 2}
      y={y - 8}
      textAnchor="middle"
      fontSize={10}
      fill="var(--ink-faint)"
      style={{ fontVariantNumeric: 'tabular-nums' }}
    >
      {formatCurrencyShort(value)}
    </text>
  );
}
