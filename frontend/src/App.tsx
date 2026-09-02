import { useState, useEffect, useCallback } from 'react';
import { Activity, ShieldCheck, ScrollText, CreditCard, BarChart3, RefreshCw, AlertTriangle } from 'lucide-react';
import { useAppData } from './useAppData';
import { KpiGrid, ErrorBanner } from './KpiGrid';
import { Controls } from './Controls';
import { PaymentsTable } from './PaymentsTable';
import { PaymentDetail } from './PaymentDetail';
import { PerformanceChart } from './PerformanceChart';
import { AttemptsTable, AuditTable } from './Tables';

type ToastType = 'success' | 'error' | 'info' | 'warning';
interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

export default function App() {
  const data = useAppData();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  // Auto-select first payment when data loads
  useEffect(() => {
    if (data.payments.length > 0 && !selectedId) {
      setSelectedId(data.payments[0].payment_id);
    }
  }, [data.payments, selectedId]);

  const handleRefresh = async () => {
    try {
      await data.refresh();
      addToast('success', 'Data refreshed successfully.');
    } catch {
      addToast('error', 'Failed to refresh data.');
    }
  };

  const handleRunBatch = async () => {
    try {
      await data.runBatch();
      addToast('success', 'Batch recovery completed.');
    } catch (e) {
      addToast('error', e instanceof Error ? e.message : 'Batch recovery failed.');
    }
  };

  const handleImport = async (id: string) => {
    try {
      await data.importPayment(id);
      addToast('success', `Payment ${id} imported successfully.`);
    } catch (e) {
      addToast('error', e instanceof Error ? e.message : 'Import failed.');
    }
  };

  const handleRecover = async (id: string) => {
    try {
      await data.recoverPayment(id);
      addToast('success', `AI recovery completed for ${id}.`);
    } catch (e) {
      addToast('error', e instanceof Error ? e.message : 'Recovery failed.');
    }
  };

  return (
    <div className="app">
      {/* Toasts */}
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          {t.message}
        </div>
      ))}

      {/* Header */}
      <div className="header">
        <div className="header-left">
          <h1>
            <Activity size={26} style={{ color: 'var(--primary)' }} />
            Revenue Recovery
          </h1>
          <p>AI-powered failed payment recovery operations</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className="header-badge">
            <span className="pulse-dot" />
            {data.loading ? 'Syncing...' : 'Live'}
          </span>
          <button className="btn btn-secondary" onClick={handleRefresh} disabled={data.loading}>
            <RefreshCw size={15} className={data.loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {data.error && <ErrorBanner message={`Unable to connect to the recovery service. Make sure the Flask backend is running on port 5000. (${data.error})`} />}

      {/* KPIs */}
      <KpiGrid summary={data.summary} />

      {/* Controls */}
      <Controls onRunBatch={handleRunBatch} onImport={handleImport} />

      {/* Failed Payments */}
      <div className="section">
        <div className="section-header">
          <div className="section-title">
            <CreditCard size={18} style={{ color: 'var(--primary)' }} />
            Failed Payments
          </div>
        </div>
        <PaymentsTable payments={data.payments} selectedId={selectedId} onSelect={setSelectedId} />
      </div>

      {/* Payment Detail + Performance Chart */}
      <div className="section">
        <div className="two-col">
          <div>
            <div className="section-header">
              <div className="section-title">
                <ShieldCheck size={18} style={{ color: 'var(--info)' }} />
                Payment Analysis
              </div>
            </div>
            <PaymentDetail
              payments={data.payments}
              selectedId={selectedId}
              lastResult={data.lastResult}
              onRecover={handleRecover}
              onClearResult={data.clearResult}
            />
          </div>
          <div>
            <div className="section-header">
              <div className="section-title">
                <BarChart3 size={18} style={{ color: 'var(--success)' }} />
                Recovery Performance
              </div>
            </div>
            <PerformanceChart attempts={data.attempts} />
          </div>
        </div>
      </div>

      {/* Recovery Activity */}
      <div className="section">
        <div className="section-header">
          <div className="section-title">
            <Activity size={18} style={{ color: 'var(--warning)' }} />
            Recovery Activity
          </div>
        </div>
        <AttemptsTable attempts={data.attempts} />
      </div>

      {/* Audit Trail */}
      <div className="section">
        <div className="section-header">
          <div className="section-title">
            <ScrollText size={18} style={{ color: 'var(--purple)' }} />
            Audit Trail
          </div>
        </div>
        <AuditTable logs={data.auditLogs} />
      </div>

      {/* Footer */}
      <div style={{ textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.8rem', marginTop: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
        <AlertTriangle size={13} />
        Razorpay Test Mode is used for payment integration. Recovery execution is simulated.
      </div>
    </div>
  );
}
