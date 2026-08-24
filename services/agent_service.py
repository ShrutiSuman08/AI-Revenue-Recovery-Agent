from agents.recovery_agent import analyze_payment
from services.policy_engine import evaluate_recovery
from services.recovery_tool import execute_recovery
from services.persistence_service import save_recovery_case
from database.models import RecoveryCase


def process_payment(payment, db):

    # ---------------------------------
    # STEP 0: IDEMPOTENCY CHECK
    # ---------------------------------

    existing_case = (
        db.query(RecoveryCase)
        .filter(
            RecoveryCase.payment_id == payment.payment_id
        )
        .first()
    )

    if existing_case:
        print(
            f"\nPayment {payment.payment_id} "
            f"already has recovery case "
            f"{existing_case.case_id}. "
            f"Skipping duplicate processing."
        )

        return {
            "status": existing_case.status,
            "payment_id": payment.payment_id,
            "case_id": existing_case.case_id,
            "action": existing_case.recommended_action,
            "reason": "Payment already processed.",
            "diagnosis": existing_case.diagnosis,
            "confidence": existing_case.confidence,
            "recovered_amount": 0.0,
        }

    # ---------------------------------
    # STEP 1: AI ANALYSIS
    # ---------------------------------

    decision = analyze_payment(payment)

    print("\n===== AI DECISION =====")

    print("Payment:", payment.payment_id)
    print("Diagnosis:", decision.diagnosis)
    print("Risk:", decision.risk_level)
    print(
        "Recommended action:",
        decision.recommended_action
    )
    print("Confidence:", decision.confidence)

    # ---------------------------------
    # STEP 2: POLICY GATE
    # ---------------------------------

    policy_decision = evaluate_recovery(
        payment,
        decision.recommended_action
    )

    print("\n===== POLICY DECISION =====")

    print("Allowed:", policy_decision.allowed)
    print("Reason:", policy_decision.reason)

    # ---------------------------------
    # STEP 3: RECOVERY EXECUTION
    # ---------------------------------

    if policy_decision.allowed:

        recovery_result = execute_recovery(
            payment,
            decision.recommended_action
        )

    else:

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

    # ---------------------------------
    # STEP 4: PRINT EXECUTION
    # ---------------------------------

    print("\n===== RECOVERY EXECUTION =====")

    print("Success:", recovery_result.success)
    print("Action:", recovery_result.action)
    print("Message:", recovery_result.message)
    print(
        "Recovered amount:",
        recovery_result.recovered_amount
    )

    # ---------------------------------
    # STEP 5: SAVE TO DATABASE
    # ---------------------------------

    recovery_case = save_recovery_case(
        db=db,
        payment=payment,
        decision=decision,
        policy_decision=policy_decision,
        recovery_result=recovery_result
    )

    # ---------------------------------
    # STEP 6: FINAL RESULT
    # ---------------------------------

    return {
        "status": recovery_case.status,
        "payment_id": payment.payment_id,
        "case_id": recovery_case.case_id,
        "action": decision.recommended_action,
        "reason": recovery_result.message,
        "diagnosis": decision.diagnosis,
        "confidence": decision.confidence,
        "recovered_amount": (
            recovery_result.recovered_amount
        )
    }