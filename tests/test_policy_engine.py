from database.connection import SessionLocal
from database.models import Payment

from services.policy_engine import evaluate_recovery


def main():

    db = SessionLocal()

    try:

        payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .limit(5)
            .all()
        )

        print("\n===== POLICY GATE TEST =====")

        for payment in payments:

            recommendation = "retry"

            decision = evaluate_recovery(
                payment,
                recommendation
            )

            print(
                payment.payment_id,
                "|",
                f"₹{payment.amount:.2f}",
                "|",
                f"attempts={payment.attempt_count}",
                "|",
                f"allowed={decision.allowed}",
                "|",
                decision.reason
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()