from database.connection import SessionLocal
from database.models import Payment
from services.agent_service import process_payment


def run_batch_recovery():
    db = SessionLocal()

    try:
        payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .limit(5)
            .all()
        )

        print("\n========================================")
        print("       AI REVENUE RECOVERY BATCH")
        print("========================================")

        print(f"Failed payments found: {len(payments)}")

        total_revenue_at_risk = sum(
            payment.amount for payment in payments
        )

        print(
            f"Revenue at risk: ₹{total_revenue_at_risk:,.2f}"
        )

        successful = 0
        failed = 0
        blocked = 0
        revenue_recovered = 0.0

        for index, payment in enumerate(payments, start=1):

            print(
                f"\n[{index}/{len(payments)}] "
                f"Processing {payment.payment_id}..."
            )

            try:
                result = process_payment(
                    payment,
                    db
                )

                status = result.get("status")

                recovered_amount = result.get(
                    "recovered_amount",
                    0.0
                )

                # Count actual successful recoveries
                # based on recovered revenue.
                if recovered_amount > 0:

                    successful += 1

                elif status == "blocked":

                    blocked += 1

                else:

                    failed += 1

                revenue_recovered += recovered_amount

            except Exception as e:

                print(
                    f"ERROR processing "
                    f"{payment.payment_id}: {e}"
                )

                failed += 1

        recovery_rate = (
            (
                revenue_recovered
                / total_revenue_at_risk
            ) * 100
            if total_revenue_at_risk > 0
            else 0
        )

        print("\n========================================")
        print("       BATCH RECOVERY RESULTS")
        print("========================================")

        print(
            f"Payments analyzed: {len(payments)}"
        )

        print(
            f"Revenue at risk: "
            f"₹{total_revenue_at_risk:,.2f}"
        )

        print(
            f"Successful recoveries: "
            f"{successful}"
        )

        print(
            f"Failed attempts: "
            f"{failed}"
        )

        print(
            f"Blocked cases: "
            f"{blocked}"
        )

        print(
            f"Revenue recovered: "
            f"₹{revenue_recovered:,.2f}"
        )

        print(
            f"Recovery rate: "
            f"{recovery_rate:.2f}%"
        )

        print("========================================")

        return {
            "payments_analyzed": len(payments),
            "revenue_at_risk": total_revenue_at_risk,
            "successful_recoveries": successful,
            "failed_attempts": failed,
            "blocked_cases": blocked,
            "revenue_recovered": revenue_recovered,
            "recovery_rate": recovery_rate,
        }

    finally:
        db.close()


if __name__ == "__main__":
    run_batch_recovery()