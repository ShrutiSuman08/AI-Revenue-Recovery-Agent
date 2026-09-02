import type {
  Summary,
  Payment,
  RecoveryAttempt,
  AuditLog,
  RecoveryResult,
  BatchResult,
} from './types';

const configuredBase = import.meta.env.VITE_API_URL?.trim();
const BASE = configuredBase ? configuredBase.replace(/\/$/, '') : '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.error) message = body.error;
    } catch {
      // not JSON
    }
    throw new Error(message);
  }
  return res.json();
}

export const api = {
  getSummary: () => request<Summary>('/summary'),
  getPayments: () => request<Payment[]>('/payments'),
  getRecoveryAttempts: () => request<RecoveryAttempt[]>('/recovery-attempts'),
  getAuditLogs: () => request<AuditLog[]>('/audit-logs'),
  runBatchRecovery: () =>
    request<{ success: boolean; result: BatchResult }>('/run-recovery', {
      method: 'POST',
    }),
  importRazorpayPayment: (payment_id: string) =>
    request<{ success: boolean; payment: Payment }>(
      '/import-razorpay-payment',
      { method: 'POST', body: JSON.stringify({ payment_id }) },
    ),
  recoverPayment: (payment_id: string) =>
    request<{ success: boolean; result: RecoveryResult }>(
      '/recover-payment',
      { method: 'POST', body: JSON.stringify({ payment_id }) },
    ),
};
