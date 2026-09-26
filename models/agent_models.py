from enum import Enum

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    step_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    status: StepStatus = StepStatus.PENDING


class RecoveryPlan(BaseModel):
    goal: str = Field(min_length=1)
    steps: list[PlanStep] = Field(min_length=1)

class RecoveryAttemptEvidence(BaseModel):
    action: str
    result: str
    amount_recovered: float
    timestamp: str


class PaymentEvidence(BaseModel):
    payment_id: str
    customer_id: str
    amount: float
    status: str
    failure_reason: str | None
    payment_method: str
    attempt_count: int
    created_at: str
    recovery_history: list[RecoveryAttemptEvidence] = Field(
    default_factory=list
)  

class PolicyDecision(BaseModel):
    allowed: bool
    reason: str    

class RecoveryResult(BaseModel):
    success: bool
    action: str
    message: str
    recovered_amount: float
    failure_type: str | None = None    

class RecoveryDecision(BaseModel):
    diagnosis: str
    risk_level: str
    recommended_action: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)    

class ReportSummary(BaseModel):
    total_payments: int
    total_revenue_at_risk: float
    recovered_payments: int
    recovered_revenue: float
    policy_blocked_payments: int
    manual_review_payments: int
    failed_recovery_attempts: int


class RecoveryReport(BaseModel):
    goal: str
    summary: ReportSummary
    cases: list[dict]    