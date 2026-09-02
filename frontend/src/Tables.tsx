import type { RecoveryAttempt, AuditLog } from './types';
import { Badge, formatAction, formatTime } from './helpers';

export function AttemptsTable({ attempts }: { attempts: RecoveryAttempt[] }) {
  if (attempts.length === 0) {
    return (
      <div className="card">
        <div className="empty">No recovery activity yet. Run a recovery to see attempts here.</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Action</th>
              <th>Result</th>
              <th>Amount Recovered</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {attempts.map((a) => (
              <tr key={a.attempt_id}>
                <td>#{a.case_id}</td>
                <td>{formatAction(a.action)}</td>
                <td><Badge status={a.result}>{resultLabel(a.result)}</Badge></td>
                <td style={{ fontWeight: 600 }}>
                  {a.amount_recovered > 0 ? `₹${a.amount_recovered.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{formatTime(a.timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function AuditTable({ logs }: { logs: AuditLog[] }) {
  if (logs.length === 0) {
    return (
      <div className="card">
        <div className="empty">No audit entries yet.</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Event</th>
              <th>Action</th>
              <th>Result</th>
              <th>Reason</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.log_id}>
                <td>#{l.case_id}</td>
                <td>{formatAction(l.event)}</td>
                <td>{l.action ? formatAction(l.action) : '—'}</td>
                <td>{l.result ? <Badge status={l.result}>{resultLabel(l.result)}</Badge> : '—'}</td>
                <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', color: 'var(--text-muted)' }}>
                  {l.reason || '—'}
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{formatTime(l.timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function resultLabel(result: string): string {
  const map: Record<string, string> = {
    success: 'Recovered',
    failed: 'Failed',
    blocked: 'Blocked',
    manual_review: 'Manual Review',
  };
  return map[result] ?? result;
}
