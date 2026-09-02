import type { Payment } from './types';
import { Badge, formatAction, formatReason, formatCurrency } from './helpers';

interface Props {
  payments: Payment[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function PaymentsTable({ payments, selectedId, onSelect }: Props) {
  if (payments.length === 0) {
    return (
      <div className="card">
        <div className="empty">No failed payments found. Import a payment or generate synthetic data.</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Payment ID</th>
              <th>Source</th>
              <th>Amount</th>
              <th>Method</th>
              <th>Failure</th>
              <th>Attempts</th>
              <th>Risk</th>
              <th>Action</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => {
              const rec = p.recovery;
              const status = rec?.status ?? 'not_evaluated';
              const risk = rec?.risk_level ?? '';
              const action = rec?.recommended_action ?? '';
              const source = p.payment_id.startsWith('pay_') ? 'razorpay' : 'synthetic';

              return (
                <tr
                  key={p.payment_id}
                  className={selectedId === p.payment_id ? 'selected' : ''}
                  onClick={() => onSelect(p.payment_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{p.payment_id}</td>
                  <td><Badge status={source}>{source === 'razorpay' ? 'Razorpay' : 'Synthetic'}</Badge></td>
                  <td style={{ fontWeight: 600 }}>{formatCurrency(p.amount)}</td>
                  <td style={{ textTransform: 'uppercase' }}>{p.payment_method}</td>
                  <td>{formatReason(p.failure_reason)}</td>
                  <td style={{ textAlign: 'center' }}>{p.attempt_count}</td>
                  <td>{risk ? <Badge status={risk}>{risk.charAt(0).toUpperCase() + risk.slice(1)}</Badge> : '—'}</td>
                  <td>{action ? formatAction(action) : '—'}</td>
                  <td><Badge status={status}>{formatStatus(status)}</Badge></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatStatus(status: string): string {
  const map: Record<string, string> = {
    recovered: 'Recovered',
    blocked: 'Blocked',
    failed: 'Failed',
    manual_review: 'Manual Review',
    not_evaluated: 'Not Evaluated',
  };
  return map[status] ?? status;
}
