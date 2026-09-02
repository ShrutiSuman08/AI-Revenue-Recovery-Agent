export interface Summary {
  payments_analyzed: number;
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  successful_recoveries: number;
}

export interface RecoveryInfo {
  case_id: number;
  risk_level: string;
  diagnosis: string;
  recommended_action: string;
  confidence: number;
  status: string;
}

export interface Payment {
  payment_id: string;
  amount: number;
  payment_method: string;
  failure_reason: string;
  attempt_count: number;
  status: string;
  recovery: RecoveryInfo | null;
}

export interface RecoveryAttempt {
  attempt_id: number;
  case_id: number;
  action: string;
  result: string;
  amount_recovered: number;
  timestamp: string;
}

export interface AuditLog {
  log_id: number;
  case_id: number;
  event: string;
  reason: string;
  action: string;
  result: string;
  timestamp: string;
}

export interface RecoveryResult {
  status: string;
  payment_id: string;
  case_id: number;
  action: string;
  reason: string;
  diagnosis: string;
  confidence: number;
  recovered_amount: number;
}

export interface BatchResult {
  payments_analyzed: number;
  revenue_at_risk: number;
  successful_recoveries: number;
  failed_attempts: number;
  blocked_cases: number;
  manual_review_cases: number;
  revenue_recovered: number;
  recovery_rate: number;
}
