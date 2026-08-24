from flask import Blueprint, jsonify

from database.connection import SessionLocal
from database.models import (
    Payment,
    RecoveryCase,
    RecoveryAttempt
)

api = Blueprint("api", __name__)


@api.route("/api/summary", methods=["GET"])
def get_summary():

    db = SessionLocal()

    try:
        failed_payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .limit(5)
            .all()
        )

        revenue_at_risk = sum(
            payment.amount
            for payment in failed_payments
        )

        recovered_cases = (
            db.query(RecoveryCase)
            .filter(
                RecoveryCase.status == "recovered"
            )
            .all()
        )

        revenue_recovered = sum(
            attempt.amount_recovered
            for case in recovered_cases
            for attempt in case.attempts
        )

        recovery_rate = (
            revenue_recovered / revenue_at_risk * 100
            if revenue_at_risk > 0
            else 0
        )

        return jsonify({
            "payments_analyzed": len(failed_payments),
            "revenue_at_risk": round(revenue_at_risk, 2),
            "revenue_recovered": round(revenue_recovered, 2),
            "recovery_rate": round(recovery_rate, 2),
            "successful_recoveries": len(recovered_cases)
        })

    finally:
        db.close()


# -----------------------------------------
# GET FAILED PAYMENTS
# -----------------------------------------

@api.route("/api/payments", methods=["GET"])
def get_payments():

    db = SessionLocal()

    try:
        payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .limit(5)
            .all()
        )

        results = []

        for payment in payments:

            recovery_case = (
                db.query(RecoveryCase)
                .filter(
                    RecoveryCase.payment_id == payment.payment_id
                )
                .first()
            )

            payment_data = {
                "payment_id": payment.payment_id,
                "amount": round(payment.amount, 2),
                "payment_method": payment.payment_method,
                "failure_reason": payment.failure_reason,
                "attempt_count": payment.attempt_count,
                "status": payment.status
            }

            if recovery_case:

                payment_data["recovery"] = {
                    "case_id": recovery_case.case_id,
                    "risk_level": recovery_case.risk_level,
                    "diagnosis": recovery_case.diagnosis,
                    "recommended_action": (
                        recovery_case.recommended_action
                    ),
                    "confidence": recovery_case.confidence,
                    "status": recovery_case.status
                }

            else:

                payment_data["recovery"] = None

            results.append(payment_data)

        return jsonify(results)

    finally:
        db.close()

@api.route("/api/recovery-attempts", methods=["GET"])
def get_recovery_attempts():

    db = SessionLocal()

    try:
        attempts = (
            db.query(RecoveryAttempt)
            .all()
        )

        return jsonify([
            {
                "attempt_id": attempt.attempt_id,
                "case_id": attempt.case_id,
                "action": attempt.action,
                "result": attempt.result,
                "amount_recovered": round(
                    attempt.amount_recovered, 2
                ),
                "timestamp": attempt.timestamp.isoformat()
            }
            for attempt in attempts
        ])

    finally:
        db.close()        