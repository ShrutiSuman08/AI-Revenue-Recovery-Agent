from database.connection import SessionLocal
from database.models import Payment

from agents.recovery_agent import analyze_payment


def main():

    db = SessionLocal()

    try:

        payment = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .first()
        )

        if not payment:
            print("No failed payment found.")
            return

        print("\n===== PAYMENT =====")

        print("Payment ID:", payment.payment_id)
        print("Amount:", payment.amount)
        print("Method:", payment.payment_method)
        print("Failure:", payment.failure_reason)
        print("Attempts:", payment.attempt_count)

        print("\n===== AI ANALYSIS =====")

        decision = analyze_payment(payment)

        print("Diagnosis:", decision.diagnosis)
        print("Risk:", decision.risk_level)
        print("Action:", decision.recommended_action)
        print("Reason:", decision.reason)
        print("Confidence:", decision.confidence)

    finally:

        db.close()


if __name__ == "__main__":
    main()