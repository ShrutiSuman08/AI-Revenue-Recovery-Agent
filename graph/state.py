from typing import TypedDict

from models.agent_models import (
    PaymentEvidence,
    PolicyDecision,
    RecoveryDecision,
    RecoveryPlan,
    RecoveryResult,
)


class AgentState(TypedDict, total=False):
    # Original user objective
    goal: str

    # High-level plan created before execution
    plan: RecoveryPlan

    # Payments currently being processed
    payments: list[PaymentEvidence]

    # Position in the batch
    current_payment_index: int
    current_payment: PaymentEvidence

    # Current reasoning / execution state
    recovery_decision: RecoveryDecision | None
    policy_decision: PolicyDecision | None
    recovery_result: RecoveryResult | None 

    # Failure recovery control
    failure_count: int

    # Completed case outputs
    case_results: list[dict]

    # Auditable chronological events
    execution_trace: list[dict]

    # Final structured batch report
    final_report: dict

    # Initial-plan repair control
    plan_repair_count: int

    # Initial plan validation
    plan_validation_errors: list[str]

    # Controlled failures used for deterministic evaluation.
    # Example: {"PAY-004": "retry"}
    fault_injections: dict[str, str]