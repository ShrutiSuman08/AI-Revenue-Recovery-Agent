import { useState } from 'react';
import { Bot, Loader2, ShieldCheck, ShieldAlert, ShieldQuestion, Info } from 'lucide-react';
import type { Payment, RecoveryResult } from './types';
import { Badge, formatAction, formatReason, formatCurrency } from './helpers';

interface Props {
  payments: Payment[];
  selectedId: string | null;
  lastResult: RecoveryResult | null;
  onRecover: (id: string) => Promise<void>;
  onClearResult: () => void;
}

export function PaymentDetail({ payments, selectedId, lastResult, onRecover, onClearResult }: Props) {
  const [loading, setLoading] = useState(false);

  const payment = payments.find((p) => p.payment_id === selectedId);

  if (!payment) {
    return (
      <div className="card">
        <div className="empty">Select a payment from the table above to view details.</div>
      </div>
    );
  }

  const recovery = payment.recovery;

  const handleRecover = async () => {
    if (!selectedId) return;
    setLoading(true);
    try {
      await onRecover(selectedId);
    } finally {
      setLoading(false);
    }
  };

  const statusIcon = (status: string) => {
    if (status === 'recovered') return <ShieldCheck size={18} style={{ color: 'var(--success)' }} />;
    if (status === 'blocked') return <ShieldAlert size={18} style={{ color: 'var(--warning)' }} />;
    if (status === 'manual_review') return <ShieldQuestion size={18} style={{ color: 'var(--purple)' }} />;
    return <ShieldAlert size={18} style={{ color: 'var(--danger)' }} />;
  };

  return (
    <div className="card">
      <div className="card-body">
        {/* Last recovery result banner */}
        {lastResult && lastResult.payment_id === payment.payment_id && (
          <div className="result-panel" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Info size={16} style={{ color: 'var(--info)' }} />
                Latest AI Recovery Result
              </h3>
              <button onClick={onClearResult} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.8rem' }}>
                Dismiss
              </button>
            </div>

            {lastResult.status === 'recovered' && (
              <div style={{ color: 'var(--success)', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                Payment recovered successfully — {formatCurrency(lastResult.recovered_amount)}
              </div>
            )}
            {lastResult.status === 'blocked' && (
              <div style={{ color: 'var(--warning)', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                Recovery was blocked by policy.
              </div>
            )}
            {lastResult.status === 'manual_review' && (
              <div style={{ color: 'var(--purple)', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                Payment was escalated for manual review.
              </div>
            )}
            {lastResult.status === 'failed' && (
              <div style={{ color: 'var(--danger)', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                Recovery attempt was unsuccessful.
              </div>
            )}

            <div className="result-grid">
              <div className="result-metric">
                <div className="label">Action</div>
                <div className="value">{formatAction(lastResult.action)}</div>
              </div>
              <div className="result-metric">
                <div className="label">Confidence</div>
                <div className="value">{(lastResult.confidence * 100).toFixed(0)}%</div>
              </div>
              <div className="result-metric">
                <div className="label">Recovered</div>
                <div className="value">{formatCurrency(lastResult.recovered_amount)}</div>
              </div>
            </div>

            <div className="result-section">
              <h4>Diagnosis</h4>
              <p style={{ color: 'var(--text-muted)' }}>{lastResult.diagnosis}</p>
            </div>
            <div className="result-section">
              <h4>Reason</h4>
              <p style={{ color: 'var(--text-muted)' }}>{lastResult.reason}</p>
            </div>
          </div>
        )}

        {/* Payment info */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Payment Details</h3>
          <button className="btn btn-primary" onClick={handleRecover} disabled={loading || payment.status !== 'failed'}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Bot size={16} />}
            {loading ? 'Analyzing...' : 'Run AI Recovery'}
          </button>
        </div>

        <div className="detail-grid">
          <div className="detail-item">
            <div className="label">Payment ID</div>
            <div className="value" style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{payment.payment_id}</div>
          </div>
          <div className="detail-item">
            <div className="label">Amount</div>
            <div className="value">{formatCurrency(payment.amount)}</div>
          </div>
          <div className="detail-item">
            <div className="label">Method</div>
            <div className="value" style={{ textTransform: 'uppercase' }}>{payment.payment_method}</div>
          </div>
          <div className="detail-item">
            <div className="label">Failure Reason</div>
            <div className="value">{formatReason(payment.failure_reason)}</div>
          </div>
          <div className="detail-item">
            <div className="label">Previous Attempts</div>
            <div className="value">{payment.attempt_count}</div>
          </div>
          <div className="detail-item">
            <div className="label">Status</div>
            <div className="value">
              <Badge status={payment.status}>{payment.status.charAt(0).toUpperCase() + payment.status.slice(1)}</Badge>
            </div>
          </div>
        </div>

        {/* AI decision */}
        {recovery ? (
          <>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '1rem', marginTop: '1.5rem' }}>AI Recovery Decision</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <div className="label">Risk Level</div>
                <div className="value"><Badge status={recovery.risk_level}>{recovery.risk_level.charAt(0).toUpperCase() + recovery.risk_level.slice(1)}</Badge></div>
              </div>
              <div className="detail-item">
                <div className="label">Confidence</div>
                <div className="value">
                  {(recovery.confidence * 100).toFixed(0)}%
                  <div className="progress-wrap" style={{ marginTop: '0.4rem' }}>
                    <div
                      className="progress-bar"
                      style={{
                        width: `${recovery.confidence * 100}%`,
                        background: recovery.confidence > 0.7 ? 'var(--success)' : recovery.confidence > 0.4 ? 'var(--warning)' : 'var(--danger)',
                      }}
                    />
                  </div>
                </div>
              </div>
              <div className="detail-item">
                <div className="label">Recommended Action</div>
                <div className="value">{formatAction(recovery.recommended_action)}</div>
              </div>
            </div>

            <div className="result-section" style={{ marginTop: '1.25rem' }}>
              <h4>Diagnosis</h4>
              <p style={{ color: 'var(--text-muted)', background: 'var(--info-bg)', border: '1px solid var(--info-border)', borderRadius: 'var(--radius-sm)', padding: '0.75rem 1rem' }}>
                {recovery.diagnosis}
              </p>
            </div>

            <div className="result-section" style={{ marginTop: '1rem' }}>
              <h4>Recovery Outcome</h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.3rem' }}>
                {statusIcon(recovery.status)}
                <span style={{ fontSize: '0.9rem' }}>{outcomeText(recovery.status)}</span>
              </div>
            </div>
          </>
        ) : (
          <div className="empty" style={{ marginTop: '1rem' }}>
            No recovery decision is available for this payment yet. Click "Run AI Recovery" to analyze it.
          </div>
        )}
      </div>
    </div>
  );
}

function outcomeText(status: string): string {
  const map: Record<string, string> = {
    recovered: 'Payment successfully recovered.',
    blocked: 'Automatic recovery was blocked by policy.',
    failed: 'Recovery attempt was unsuccessful.',
    manual_review: 'Automatic recovery stopped — manual review required.',
  };
  return map[status] ?? status;
}
