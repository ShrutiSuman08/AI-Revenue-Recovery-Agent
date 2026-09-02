import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { RecoveryAttempt } from './types';

export function PerformanceChart({ attempts }: { attempts: RecoveryAttempt[] }) {
  const success = attempts.filter((a) => a.result === 'success').length;
  const failed = attempts.filter((a) => a.result === 'failed').length;
  const blocked = attempts.filter((a) => a.result === 'blocked').length;

  const data = [
    { name: 'Recovered', value: success, color: '#22c55e' },
    { name: 'Failed', value: failed, color: '#ef4444' },
    { name: 'Blocked', value: blocked, color: '#f59e0b' },
  ];

  return (
    <div className="card">
      <div className="card-body" style={{ paddingBottom: '0.5rem' }}>
        <div className="section-title">Recovery Performance</div>
        <p className="section-desc">Distribution of recovery attempt outcomes</p>
      </div>
      <div style={{ height: 220, padding: '0 1rem 1rem' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                fontSize: '0.85rem',
              }}
              labelStyle={{ color: '#f1f5f9' }}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={80}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
