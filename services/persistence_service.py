from datetime import datetime

from database.models import (
    RecoveryCase,
    RecoveryAttempt,
    AuditLog
)


def save_recovery_case(
    db,
    payment,
    decision,
    policy_decision,
    recovery_result
):
    """
    Persist the complete recovery workflow
    into RecoveryCase, RecoveryAttempt and AuditLog.
    """

    # -----------------------------------------
    # 1. Determine final case status
    # -----------------------------------------

    if not policy_decision.allowed:
        case_status = "blocked"

    elif recovery_result.success:
        case_status = "recovered"

    else:
        case_status = "failed"

    # -----------------------------------------
    # 2. Create RecoveryCase
    # -----------------------------------------

    recovery_case = RecoveryCase(
        payment_id=payment.payment_id,
        risk_level=decision.risk_level,
        diagnosis=decision.diagnosis,
        recommended_action=decision.recommended_action,
        confidence=decision.confidence,
        status=case_status
    )

    db.add(recovery_case)

    # Generate case_id
    db.flush()

    # -----------------------------------------
    # 3. Create RecoveryAttempt
    # -----------------------------------------

    attempt_result = (
        "blocked"
        if not policy_decision.allowed
        else (
            "success"
            if recovery_result.success
            else "failed"
        )
    )

    recovery_attempt = RecoveryAttempt(
        case_id=recovery_case.case_id,
        action=decision.recommended_action,
        result=attempt_result,
        amount_recovered=recovery_result.recovered_amount,
        timestamp=datetime.utcnow()
    )

    db.add(recovery_attempt)

    # -----------------------------------------
    # 4. Create Audit Log
    # -----------------------------------------

    if not policy_decision.allowed:

        audit_event = "recovery_blocked"
        audit_reason = policy_decision.reason
        audit_result = "blocked"

    elif recovery_result.success:

        audit_event = "recovery_success"
        audit_reason = recovery_result.message
        audit_result = "success"

    else:

        audit_event = "recovery_failed"
        audit_reason = recovery_result.message
        audit_result = "failed"

    audit_log = AuditLog(
        case_id=recovery_case.case_id,
        event=audit_event,
        reason=audit_reason,
        action=decision.recommended_action,
        result=audit_result,
        timestamp=datetime.utcnow()
    )

    db.add(audit_log)

    # -----------------------------------------
    # 5. Commit everything together
    # -----------------------------------------

    db.commit()

    # Refresh generated case_id
    db.refresh(recovery_case)

    return recovery_case