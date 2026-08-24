import random
import uuid
from datetime import datetime

from database.models import (
    Payment,
    RecoveryCase,
    RecoveryAttempt,
    AuditLog
)

from services.revenue_service import get_recovery_action


# ---------------------------------------
# Configuration
# ---------------------------------------

MAX_ATTEMPTS = 2
HIGH_VALUE_THRESHOLD = 10000


# These are synthetic evaluation assumptions.
# They are NOT real Razorpay success rates.

SUCCESS_PROBABILITIES = {
    "retry": 0.75,
    "notify_and_retry_later": 0.50,
    "request_alternate_payment": 0.60
}


# ---------------------------------------
# Risk classification
# ---------------------------------------

def get_risk_level(payment):

    if payment.amount > HIGH_VALUE_THRESHOLD:
        return "high"

    if payment.failure_reason in {
        "network_error",
        "bank_timeout"
    }:
        return "medium"

    return "low"


# ---------------------------------------
# Policy gate
# ---------------------------------------

def policy_check(payment):

    # Rule 1: Stop after maximum attempts
    if payment.attempt_count >= MAX_ATTEMPTS:

        return {
            "allowed": False,
            "reason": "Maximum recovery attempts reached"
        }

    # Rule 2: High-value transactions need approval
    if payment.amount > HIGH_VALUE_THRESHOLD:

        return {
            "allowed": False,
            "reason": "High-value payment requires approval"
        }

    # Rule 3: Card blocked should not be automatically recovered
    if payment.failure_reason == "card_blocked":

        return {
            "allowed": False,
            "reason": "Card blocked - manual intervention required"
        }

    return {
        "allowed": True,
        "reason": "Payment passed recovery policy"
    }


# ---------------------------------------
# Simulate recovery
# ---------------------------------------

def simulate_recovery(payment, action):

    success_probability = SUCCESS_PROBABILITIES.get(
        action,
        0
    )

    success = random.random() < success_probability

    if success:

        return {
            "result": "success",
            "amount_recovered": payment.amount
        }

    return {
        "result": "failed",
        "amount_recovered": 0.0
    }


# ---------------------------------------
# Create recovery case
# ---------------------------------------

def create_recovery_case(db, payment):

    action = get_recovery_action(payment)

    risk_level = get_risk_level(payment)

    case = RecoveryCase(
        case_id=str(uuid.uuid4()),
        payment_id=payment.payment_id,
        risk_level=risk_level,
        diagnosis=payment.failure_reason,
        recommended_action=action,
        confidence=0.90,
        status="open"
    )

    db.add(case)

    db.commit()

    return case


# ---------------------------------------
# Execute recovery
# ---------------------------------------

def execute_recovery(db, payment):

    # Create a recovery case
    case = create_recovery_case(
        db,
        payment
    )

    # Check policy
    policy = policy_check(payment)

    # -----------------------------------
    # BLOCKED ACTION
    # -----------------------------------

    if not policy["allowed"]:

        case.status = "blocked"

        audit = AuditLog(
            log_id=str(uuid.uuid4()),
            case_id=case.case_id,
            event="recovery_blocked",
            reason=policy["reason"],
            action=case.recommended_action,
            result="blocked",
            timestamp=datetime.now()
        )

        db.add(audit)

        db.commit()

        return {
            "status": "blocked",
            "amount_recovered": 0.0,
            "reason": policy["reason"]
        }

    # -----------------------------------
    # EXECUTE ACTION
    # -----------------------------------

    result = simulate_recovery(
        payment,
        case.recommended_action
    )

    recovery_attempt = RecoveryAttempt(
        attempt_id=str(uuid.uuid4()),
        case_id=case.case_id,
        action=case.recommended_action,
        result=result["result"],
        amount_recovered=result["amount_recovered"],
        timestamp=datetime.now()
    )

    db.add(recovery_attempt)

    # -----------------------------------
    # UPDATE PAYMENT
    # -----------------------------------

    if result["result"] == "success":

        payment.status = "recovered"

        case.status = "recovered"

    else:

        payment.attempt_count += 1

        case.status = "failed"

    # -----------------------------------
    # AUDIT LOG
    # -----------------------------------

    audit = AuditLog(
        log_id=str(uuid.uuid4()),
        case_id=case.case_id,
        event="recovery_attempt",
        reason=payment.failure_reason,
        action=case.recommended_action,
        result=result["result"],
        timestamp=datetime.now()
    )

    db.add(audit)

    db.commit()

    return {
        "status": result["result"],
        "amount_recovered": result["amount_recovered"],
        "reason": payment.failure_reason
    }