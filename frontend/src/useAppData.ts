import { useEffect, useCallback } from 'react';
import { api } from './api';
import type {
  Summary,
  Payment,
  RecoveryAttempt,
  AuditLog,
  RecoveryResult,
} from './types';

export interface AppData {
  summary: Summary | null;
  payments: Payment[];
  attempts: RecoveryAttempt[];
  auditLogs: AuditLog[];
  loading: boolean;
  error: string | null;
  lastResult: RecoveryResult | null;
  refresh: () => Promise<void>;
  runBatch: () => Promise<void>;
  importPayment: (id: string) => Promise<void>;
  recoverPayment: (id: string) => Promise<void>;
  clearResult: () => void;
}

export function useAppData(): AppData {
  const {
    summary,
    payments,
    attempts,
    auditLogs,
    loading,
    error,
    lastResult,
    setState,
    refresh,
  } = useFetchAll();

  const refreshFn = useCallback(refresh, [refresh]);

  const runBatch = useCallback(async () => {
    await api.runBatchRecovery();
    await refreshFn();
  }, [refreshFn]);

  const importPayment = useCallback(
    async (id: string) => {
      await api.importRazorpayPayment(id);
      await refreshFn();
    },
    [refreshFn],
  );

  const recoverPayment = useCallback(
    async (id: string) => {
      const res = await api.recoverPayment(id);
      if (res.success && res.result) {
        setState((prev) => ({ ...prev, lastResult: res.result }));
      }
      await refreshFn();
    },
    [refreshFn, setState],
  );

  const clearResult = useCallback(() => {
    setState((prev) => ({ ...prev, lastResult: null }));
  }, [setState]);

  return {
    summary,
    payments,
    attempts,
    auditLogs,
    loading,
    error,
    lastResult,
    refresh: refreshFn,
    runBatch,
    importPayment,
    recoverPayment,
    clearResult,
  };
}

interface State {
  summary: Summary | null;
  payments: Payment[];
  attempts: RecoveryAttempt[];
  auditLogs: AuditLog[];
  loading: boolean;
  error: string | null;
  lastResult: RecoveryResult | null;
}

function useFetchAll() {
  const [state, setState] = useReactState<State>({
    summary: null,
    payments: [],
    attempts: [],
    auditLogs: [],
    loading: true,
    error: null,
    lastResult: null,
  });

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const [summary, payments, attempts, auditLogs] = await Promise.all([
        api.getSummary(),
        api.getPayments(),
        api.getRecoveryAttempts(),
        api.getAuditLogs(),
      ]);
      setState((prev) => ({
        ...prev,
        summary,
        payments,
        attempts,
        auditLogs,
        loading: false,
      }));
    } catch (e) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: e instanceof Error ? e.message : 'Failed to load data',
      }));
    }
  }, [setState]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { ...state, setState, refresh };
}

// Minimal useState wrapper to avoid importing from react twice
import { useState } from 'react';
function useReactState<T>(initial: T) {
  return useState<T>(initial);
}
