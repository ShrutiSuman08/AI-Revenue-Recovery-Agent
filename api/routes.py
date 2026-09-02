from flask import Blueprint, jsonify, request
from database.connection import SessionLocal
from database.models import (
    Payment,
    RecoveryCase,
    RecoveryAttempt,
    AuditLog
)

api = Blueprint("api", __name__)


@api.route("/api/summary", methods=["GET"])
def get_summary():

    db = SessionLocal()

    try:
        failed_payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .all()
        )

        # -----------------------------------------
        # CALCULATE REVENUE STILL AT RISK
        # -----------------------------------------

        revenue_at_risk = 0.0

        for payment in failed_payments:

            latest_case = (
                db.query(RecoveryCase)
                .filter(
                    RecoveryCase.payment_id == payment.payment_id
                )
                .order_by(
                    RecoveryCase.case_id.desc()
                )
                .first()
            )

            # Don't count successfully recovered payments
            if not latest_case or latest_case.status != "recovered":
                revenue_at_risk += payment.amount

        # -----------------------------------------
        # CALCULATE REVENUE RECOVERED
        # -----------------------------------------

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

        # -----------------------------------------
        # RECOVERY RATE
        # -----------------------------------------

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
            
            .all()
        )

        results = []

        for payment in payments:

            recovery_case = (
    db.query(RecoveryCase)
    .filter(
        RecoveryCase.payment_id == payment.payment_id
    )
    .order_by(
        RecoveryCase.case_id.desc()
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


@api.route("/api/audit-logs", methods=["GET"])
def get_audit_logs():

    db = SessionLocal()

    try:

        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

        return jsonify([
            {
                "log_id": log.log_id,
                "case_id": log.case_id,
                "event": log.event,
                "reason": log.reason,
                "action": log.action,
                "result": log.result,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ])

    finally:

        db.close()        


@api.route("/api/run-recovery", methods=["POST"])
def run_recovery():

    from services.batch_recovery_service import run_batch_recovery

    try:

        result = run_batch_recovery()

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500        


@api.route("/api/import-razorpay-payment", methods=["POST"])
def import_razorpay_payment_route():

    from services.razorpay_import_service import import_razorpay_payment

    try:

        data = request.get_json()

        payment_id = data.get("payment_id")

        if not payment_id:

            return jsonify({
                "success": False,
                "error": "payment_id is required."
            }), 400

        payment = import_razorpay_payment(
            payment_id
        )

        return jsonify({
            "success": True,
            "payment": {
                "payment_id": payment.payment_id,
                "amount": round(payment.amount, 2),
                "status": payment.status,
                "payment_method": payment.payment_method,
                "failure_reason": payment.failure_reason
            }
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500    

@api.route("/api/recover-payment", methods=["POST"])
def recover_payment():

    db = SessionLocal()

    try:

        data = request.get_json()

        payment_id = data.get("payment_id")

        if not payment_id:

            return jsonify({
                "success": False,
                "error": "payment_id is required."
            }), 400

        payment = (
            db.query(Payment)
            .filter(
                Payment.payment_id == payment_id
            )
            .first()
        )

        if not payment:

            return jsonify({
                "success": False,
                "error": "Payment not found."
            }), 404

        if payment.status != "failed":

            return jsonify({
                "success": False,
                "error": (
                    f"Payment is already "
                    f"{payment.status}."
                )
            }), 400

        from services.agent_service import process_payment
        result = process_payment(
            payment,
            db
        )

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:

        db.close()
    