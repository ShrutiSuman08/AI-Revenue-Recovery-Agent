import { useState } from 'react';
import { Zap, Download, Loader2 } from 'lucide-react';

interface Props {
  onRunBatch: () => Promise<void>;
  onImport: (id: string) => Promise<void>;
}

export function Controls({ onRunBatch, onImport }: Props) {
  const [batchLoading, setBatchLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [paymentId, setPaymentId] = useState('');

  const handleBatch = async () => {
    setBatchLoading(true);
    try {
      await onRunBatch();
    } finally {
      setBatchLoading(false);
    }
  };

  const handleImport = async () => {
    if (!paymentId.trim()) return;
    setImportLoading(true);
    try {
      await onImport(paymentId.trim());
      setPaymentId('');
    } finally {
      setImportLoading(false);
    }
  };

  return (
    <div className="controls">
      <div className="control-card">
        <h3>Batch Recovery</h3>
        <p>Run the AI recovery workflow for all eligible failed payments. Processes up to 5 payments per batch.</p>
        <button className="btn btn-primary" onClick={handleBatch} disabled={batchLoading}>
          {batchLoading ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
          {batchLoading ? 'Running...' : 'Run Batch Recovery'}
        </button>
      </div>

      <div className="control-card">
        <h3>Import Razorpay Payment</h3>
        <p>Import a failed Razorpay Test Mode payment by its payment ID.</p>
        <input
          className="input"
          placeholder="pay_XXXXXXXXXXXX"
          value={paymentId}
          onChange={(e) => setPaymentId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleImport()}
        />
        <button className="btn btn-secondary" onClick={handleImport} disabled={importLoading || !paymentId.trim()}>
          {importLoading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
          {importLoading ? 'Importing...' : 'Import Payment'}
        </button>
      </div>
    </div>
  );
}
