from agents.recovery_agent import analyze_payment
from services.policy_engine import evaluate_recovery
from services.recovery_tool import execute_recovery
from services.persistence_service import save_recovery_case
from datetime import datetime

from database.models import (
    RecoveryCase,
    RecoveryAttempt,
    AuditLog
)


def process_payment(payment, db):

    # -----------------------------------------
    # STEP 0: CHECK EXISTING CASE
    # -----------------------------------------

    existing_case = (
        db.query(RecoveryCase)
        .filter(
            RecoveryCase.payment_id == payment.payment_id
        )
        .order_by(
            RecoveryCase.case_id.desc()
        )
        .first()
    )

    if existing_case:

        if existing_case.status in [
            "recovered",
            "blocked",
            "manual_review"
        ]:

            print(
                f"\nPayment {payment.payment_id} "
                f"is already {existing_case.status} "
                f"in case {existing_case.case_id}. "
                f"Skipping."
            )

            return {
                "status": existing_case.status,
                "payment_id": payment.payment_id,
                "case_id": existing_case.case_id,
                "action": existing_case.recommended_action,
                "reason": "Payment already finalized.",
                "diagnosis": existing_case.diagnosis,
                "confidence": existing_case.confidence,
                "recovered_amount": 0.0,
            }

        if existing_case.status == "failed":

            print(
                f"\nPayment {payment.payment_id} "
                f"had failed case "
                f"{existing_case.case_id}. "
                f"Retrying recovery."
            )

        # -----------------------------------------
    # STEP 1: GET PREVIOUS RECOVERY ATTEMPTS
    # -----------------------------------------

    previous_attempts = (
        db.query(RecoveryAttempt)
        .join(
            RecoveryCase,
            RecoveryAttempt.case_id == RecoveryCase.case_id
        )
        .filter(
            RecoveryCase.payment_id == payment.payment_id
        )
        .order_by(
            RecoveryAttempt.attempt_id.asc()
        )
        .all()
    )

        # -----------------------------------------
    # STEP 1.5: CHECK RECOVERY ATTEMPT LIMIT
    # -----------------------------------------

    MAX_AGENT_RECOVERY_ATTEMPTS = 3

    if len(previous_attempts) >= MAX_AGENT_RECOVERY_ATTEMPTS:

        print(
            f"\nPayment {payment.payment_id} "
            f"has reached the maximum "
            f"agent recovery attempts."
        )

        if existing_case:

            existing_case.status = "manual_review"
            existing_case.recommended_action = "manual_review"

            audit_log = AuditLog(
                case_id=existing_case.case_id,
                event="manual_review_required",
                reason=(
                    "Maximum agent recovery attempts reached."
                ),
                action="manual_review",
                result="manual_review",
                timestamp=datetime.utcnow()
            )

            db.add(audit_log)
            db.commit()

        return {
            "status": "manual_review",
            "payment_id": payment.payment_id,
            "case_id": (
                existing_case.case_id
                if existing_case
                else None
            ),
            "action": "manual_review",
            "reason": (
                "Maximum agent recovery attempts reached."
            ),
            "diagnosis": (
                existing_case.diagnosis
                if existing_case
                else None
            ),
            "confidence": (
                existing_case.confidence
                if existing_case
                else 0.0
            ),
            "recovered_amount": 0.0
        }    

    previous_actions = [
        attempt.action
        for attempt in previous_attempts
    ]

    previous_results = [
        attempt.result
        for attempt in previous_attempts
    ]

    print("\n===== PREVIOUS RECOVERY ATTEMPTS =====")

    if previous_attempts:

        for attempt in previous_attempts:

            print(
                f"Attempt {attempt.attempt_id}: "
                f"{attempt.action} -> "
                f"{attempt.result}"
            )

    else:

        print("No previous recovery attempts.")
    # -----------------------------------------
    # STEP 2: AI ANALYSIS
    # -----------------------------------------

    decision = analyze_payment(
        payment,
        previous_actions=previous_actions,
        previous_results=previous_results
    )

    print("\n===== AI DECISION =====")

    print(
        "Payment:",
        payment.payment_id
    )

    print(
        "Diagnosis:",
        decision.diagnosis
    )

    print(
        "Risk:",
        decision.risk_level
    )

    print(
        "Recommended action:",
        decision.recommended_action
    )

    print(
        "Confidence:",
        decision.confidence
    )

    # -----------------------------------------
    # STEP 3: POLICY GATE
    # -----------------------------------------

    policy_decision = evaluate_recovery(
        payment,
        decision.recommended_action
    )

    print("\n===== POLICY DECISION =====")

    print(
        "Allowed:",
        policy_decision.allowed
    )

    print(
        "Reason:",
        policy_decision.reason
    )

    # -----------------------------------------
    # STEP 4: RECOVERY EXECUTION
    # -----------------------------------------

    if decision.recommended_action == "manual_review":

        # -------------------------------------
        # MANUAL REVIEW IS NOT AN AUTO ACTION
        # -------------------------------------

        recovery_result = type(
            "RecoveryResult",
            (),
            {
                "success": False,
                "action": "manual_review",
                "message": (
                    "Payment escalated for manual review. "
                    "No automatic recovery action executed."
                ),
                "recovered_amount": 0.0
            }
        )()

    elif policy_decision.allowed:

        # -------------------------------------
        # NORMAL AUTOMATIC RECOVERY
        # -------------------------------------

        recovery_result = execute_recovery(
            payment,
            decision.recommended_action
        )

    else:

        # -------------------------------------
        # POLICY BLOCK
        # -------------------------------------

        recovery_result = type(
            "RecoveryResult",
            (),
            {
                "success": False,
                "action": decision.recommended_action,
                "message": policy_decision.reason,
                "recovered_amount": 0.0
            }
        )()

    # -----------------------------------------
    # STEP 5: PRINT EXECUTION
    # -----------------------------------------

    print("\n===== RECOVERY EXECUTION =====")

    print(
        "Success:",
        recovery_result.success
    )

    print(
        "Action:",
        recovery_result.action
    )

    print(
        "Message:",
        recovery_result.message
    )

    print(
        "Recovered amount:",
        recovery_result.recovered_amount
    )

    # -----------------------------------------
    # STEP 6: SAVE RESULT
    # -----------------------------------------

    recovery_case = save_recovery_case(
        db=db,
        payment=payment,
        decision=decision,
        policy_decision=policy_decision,
        recovery_result=recovery_result,
        existing_case=existing_case
    )

    # -----------------------------------------
    # STEP 7: UPDATE PAYMENT STATUS
    # -----------------------------------------

    if recovery_case.status == "recovered":

        payment.status = "recovered"
        db.commit()

        print(
            f"Payment {payment.payment_id} "
            f"successfully marked as recovered."
        )

    elif recovery_case.status == "failed":

        print(
            f"Payment {payment.payment_id} "
            f"recovery attempt failed."
        )

    elif recovery_case.status == "blocked":

        print(
            f"Payment {payment.payment_id} "
            f"was blocked by recovery policy."
        )

    elif recovery_case.status == "manual_review":

        print(
            f"Payment {payment.payment_id} "
            f"was escalated for manual review."
        )

    # -----------------------------------------
    # STEP 8: FINAL RESULT
    # -----------------------------------------

    return {
        "status": recovery_case.status,
        "payment_id": payment.payment_id,
        "case_id": recovery_case.case_id,
        "action": decision.recommended_action,
        "reason": recovery_result.message,
        "diagnosis": decision.diagnosis,
        "confidence": decision.confidence,
        "recovered_amount": recovery_result.recovered_amount
    } 