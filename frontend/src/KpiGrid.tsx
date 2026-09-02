import {
  TrendingDown,
  TrendingUp,
  Percent,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import type { Summary } from './types';
import { formatCurrency } from './helpers';

export function KpiGrid({ summary }: { summary: Summary | null }) {
  if (!summary) {
    return (
      <div className="kpi-grid">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="kpi-card">
            <div className="kpi-label">
              <Loader2 size={14} className="animate-spin" />
              Loading...
            </div>
            <div className="kpi-value" style={{ color: 'var(--text-dim)' }}>—</div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: 'Revenue at Risk',
      value: formatCurrency(summary.revenue_at_risk),
      icon: <TrendingDown size={15} />,
      sub: `${summary.payments_analyzed} failed payments`,
      color: 'var(--danger)',
    },
    {
      label: 'Revenue Recovered',
      value: formatCurrency(summary.revenue_recovered),
      icon: <TrendingUp size={15} />,
      sub: 'Total recovered to date',
      color: 'var(--success)',
    },
    {
      label: 'Recovery Rate',
      value: `${summary.recovery_rate.toFixed(2)}%`,
      icon: <Percent size={15} />,
      sub: 'Recovered vs at risk',
      color: 'var(--primary)',
    },
    {
      label: 'Successful Recoveries',
      value: String(summary.successful_recoveries),
      icon: <CheckCircle2 size={15} />,
      sub: 'Payments fully recovered',
      color: 'var(--info)',
    },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((c) => (
        <div key={c.label} className="kpi-card">
          <div className="kpi-label">
            <span style={{ color: c.color }}>{c.icon}</span>
            {c.label}
          </div>
          <div className="kpi-value">{c.value}</div>
          <div className="kpi-sub">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="error-banner">
      <AlertCircle size={18} />
      {message}
    </div>
  );
}
