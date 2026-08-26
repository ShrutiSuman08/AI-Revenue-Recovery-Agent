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
    recovery_result,
    existing_case=None
):
    """
    Persist the complete recovery workflow.

    Reuses an existing recovery case for retries
    and creates a new RecoveryAttempt and AuditLog
    for every recovery execution.
    """

    # -----------------------------------------
    # 1. DETERMINE FINAL CASE STATUS
    # -----------------------------------------

    if decision.recommended_action == "manual_review":

        case_status = "manual_review"

    elif not policy_decision.allowed:

        case_status = "blocked"

    elif recovery_result.success:

        case_status = "recovered"

    else:

        case_status = "failed"

    # -----------------------------------------
    # 2. CREATE OR REUSE RECOVERY CASE
    # -----------------------------------------

    if existing_case:

        recovery_case = existing_case

        recovery_case.risk_level = decision.risk_level
        recovery_case.diagnosis = decision.diagnosis
        recovery_case.recommended_action = (
            decision.recommended_action
        )
        recovery_case.confidence = decision.confidence
        recovery_case.status = case_status

    else:

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
    # 3. DETERMINE RECOVERY ATTEMPT RESULT
    # -----------------------------------------

    if decision.recommended_action == "manual_review":

        attempt_result = "manual_review"

    elif not policy_decision.allowed:

        attempt_result = "blocked"

    elif recovery_result.success:

        attempt_result = "success"

    else:

        attempt_result = "failed"

    # -----------------------------------------
    # 4. CREATE RECOVERY ATTEMPT
    # -----------------------------------------

    recovery_attempt = RecoveryAttempt(
        case_id=recovery_case.case_id,
        action=decision.recommended_action,
        result=attempt_result,
        amount_recovered=recovery_result.recovered_amount,
        timestamp=datetime.utcnow()
    )

    db.add(recovery_attempt)

    # -----------------------------------------
    # 5. CREATE AUDIT LOG
    # -----------------------------------------

    if decision.recommended_action == "manual_review":

        audit_event = "manual_review_required"
        audit_reason = recovery_result.message
        audit_result = "manual_review"

    elif not policy_decision.allowed:

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
    # 6. COMMIT
    # -----------------------------------------

    db.commit()

    db.refresh(recovery_case)

    return recovery_case