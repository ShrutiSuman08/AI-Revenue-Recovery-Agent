from models.agent_models import (
    PaymentEvidence,
    RecoveryAttemptEvidence,
)


def get_demo_payments() -> list[PaymentEvidence]:
    """
    Return deterministic payment cases used for evaluating
    the RevenueOps Agent workflow.
    """

    return [
        PaymentEvidence(
            payment_id="PAY-001",
            customer_id="CUST-001",
            amount=2500.0,
            status="failed",
            failure_reason="bank_timeout",
            payment_method="card",
            attempt_count=0,
            created_at="2026-09-26T01:00:00",
        ),

        PaymentEvidence(
            payment_id="PAY-002",
            customer_id="CUST-002",
            amount=1800.0,
            status="failed",
            failure_reason="insufficient_funds",
            payment_method="card",
            attempt_count=1,
            created_at="2026-09-26T01:05:00",
        ),

        PaymentEvidence(
            payment_id="PAY-003",
            customer_id="CUST-003",
            amount=15000.0,
            status="failed",
            failure_reason="gateway_error",
            payment_method="card",
            attempt_count=0,
            created_at="2026-09-26T01:10:00",
        ),

        PaymentEvidence(
            payment_id="PAY-004",
            customer_id="CUST-004",
            amount=4500.0,
            status="failed",
            failure_reason="gateway_error",
            payment_method="card",
            attempt_count=0,
            created_at="2026-09-26T01:15:00",
        ),

        PaymentEvidence(
            payment_id="PAY-005",
            customer_id="CUST-005",
            amount=3000.0,
            status="failed",
            failure_reason="gateway_error",
            payment_method="card",
            attempt_count=0,
            created_at="2026-09-26T01:20:00",
            recovery_history=[
                RecoveryAttemptEvidence(
                    action="retry",
                    result="failed",
                    amount_recovered=0.0,
                    timestamp="2026-09-26T01:21:00",
                ),
                RecoveryAttemptEvidence(
                    action="notify_and_retry_later",
                    result="failed",
                    amount_recovered=0.0,
                    timestamp="2026-09-26T01:22:00",
                ),
            ],
        ),

        PaymentEvidence(
            payment_id="PAY-006",
            customer_id="CUST-006",
            amount=3200.0,
            status="failed",
            failure_reason="bank_timeout",
            payment_method="netbanking",
            attempt_count=0,
            created_at="2026-09-26T01:25:00",
        ),
    ]