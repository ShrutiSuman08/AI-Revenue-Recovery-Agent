import type { ReactNode } from 'react';
import { clsx } from 'clsx';

export function Badge({ status, children }: { status: string; children: ReactNode }) {
  const cls = badgeClass(status);
  return <span className={cls}>{children}</span>;
}

export function badgeClass(status: string): string {
  const map: Record<string, string> = {
    recovered: 'badge-success',
    success: 'badge-success',
    low: 'badge-success',
    blocked: 'badge-warning',
    failed: 'badge-danger',
    high: 'badge-danger',
    medium: 'badge-warning',
    manual_review: 'badge-purple',
    not_evaluated: 'badge-neutral',
    razorpay: 'badge-info',
    synthetic: 'badge-neutral',
  };
  return clsx('badge', map[status.toLowerCase()] ?? 'badge-neutral');
}

export function formatAction(action: string): string {
  return action.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatReason(reason: string): string {
  return reason.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatTime(ts: string): string {
  return ts.replace('T', ' ').slice(0, 19);
}

export function formatCurrency(amount: number): string {
  return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
