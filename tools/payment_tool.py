from sqlalchemy.orm import Session

from database.models import Payment, RecoveryCase, RecoveryAttempt
from models.agent_models import (
    PaymentEvidence,
    RecoveryAttemptEvidence,
)


def get_failed_payments(db: Session) -> list[PaymentEvidence]:
    """
    Retrieve all failed payments that may require investigation.

    This tool is read-only. It does not modify payment or recovery data.
    """
    payments = (
        db.query(Payment)
        .filter(Payment.status == "failed")
        .order_by(Payment.created_at.asc())
        .all()
    )

    return [
        _build_payment_evidence(db, payment)
        for payment in payments
    ]


def get_payment_evidence(
    db: Session,
    payment_id: str,
) -> PaymentEvidence | None:
    """
    Retrieve detailed evidence for one payment,
    including its previous recovery attempts.
    """
    payment = (
        db.query(Payment)
        .filter(Payment.payment_id == payment_id)
        .first()
    )

    if payment is None:
        return None

    return _build_payment_evidence(db, payment)


def _build_payment_evidence(
    db: Session,
    payment: Payment,
) -> PaymentEvidence:
    """
    Convert database records into the typed evidence
    contract consumed by the agent.
    """

    attempts = (
        db.query(RecoveryAttempt)
        .join(
            RecoveryCase,
            RecoveryAttempt.case_id == RecoveryCase.case_id,
        )
        .filter(
            RecoveryCase.payment_id == payment.payment_id
        )
        .order_by(RecoveryAttempt.timestamp.asc())
        .all()
    )

    recovery_history = [
        RecoveryAttemptEvidence(
            action=attempt.action,
            result=attempt.result,
            amount_recovered=attempt.amount_recovered or 0.0,
            timestamp=attempt.timestamp.isoformat(),
        )
        for attempt in attempts
    ]

    return PaymentEvidence(
        payment_id=payment.payment_id,
        customer_id=payment.customer_id,
        amount=payment.amount,
        status=payment.status,
        failure_reason=payment.failure_reason,
        payment_method=payment.payment_method,
        attempt_count=payment.attempt_count or 0,
        created_at=payment.created_at.isoformat(),
        recovery_history=recovery_history,
    )