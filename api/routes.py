from flask import Blueprint, jsonify

from database.connection import SessionLocal
from database.models import (
    Payment,
    RecoveryCase
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