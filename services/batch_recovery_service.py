from database.connection import SessionLocal
from database.models import Payment, RecoveryCase
from services.agent_service import process_payment


def run_batch_recovery():

    db = SessionLocal()

    try:

        # -----------------------------------------
        # FIND FAILED PAYMENTS
        # -----------------------------------------

        failed_payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .all()
        )

        # -----------------------------------------
        # DETERMINE ELIGIBLE PAYMENTS
        # -----------------------------------------

        eligible_payments = []

        for payment in failed_payments:

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

            # No recovery case yet
            if not existing_case:

                eligible_payments.append(payment)

            # Already recovered
            elif existing_case.status == "recovered":

                print(
                    f"Skipping {payment.payment_id} - "
                    f"case already recovered."
                )

            # Permanently blocked
            elif existing_case.status == "blocked":

                print(
                    f"Skipping {payment.payment_id} - "
                    f"case is blocked."
                )

            # Waiting for human review
            elif existing_case.status == "manual_review":

                print(
                    f"Skipping {payment.payment_id} - "
                    f"awaiting manual review."
                )

            # Previous automatic recovery failed
            elif existing_case.status == "failed":

                print(
                    f"Retry eligible: "
                    f"{payment.payment_id} - "
                    f"previous attempt failed."
                )

                eligible_payments.append(payment)

        # -----------------------------------------
        # SMALL DEVELOPMENT BATCH
        # -----------------------------------------

        payments = eligible_payments[:5]

        # -----------------------------------------
        # BATCH HEADER
        # -----------------------------------------

        print("\n========================================")
        print("       AI REVENUE RECOVERY BATCH")
        print("========================================")

        print(
            f"Eligible failed payments: {len(payments)}"
        )

        # -----------------------------------------
        # REVENUE AT RISK
        # -----------------------------------------

        total_revenue_at_risk = sum(
            payment.amount
            for payment in payments
        )

        print(
            f"Revenue at risk: "
            f"₹{total_revenue_at_risk:,.2f}"
        )

        # -----------------------------------------
        # COUNTERS
        # -----------------------------------------

        successful = 0
        failed = 0
        blocked = 0
        manual_review = 0
        revenue_recovered = 0.0

        # -----------------------------------------
        # PROCESS PAYMENTS
        # -----------------------------------------

        for index, payment in enumerate(
            payments,
            start=1
        ):

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

                # ---------------------------------
                # CLASSIFY RESULT
                # ---------------------------------

                if recovered_amount > 0:

                    successful += 1

                elif status == "blocked":

                    blocked += 1

                elif status == "manual_review":

                    manual_review += 1

                else:

                    failed += 1

                revenue_recovered += recovered_amount

            except Exception as e:

                print(
                    f"ERROR processing "
                    f"{payment.payment_id}: {e}"
                )

                failed += 1

        # -----------------------------------------
        # RECOVERY RATE
        # -----------------------------------------

        recovery_rate = (
            (
                revenue_recovered
                / total_revenue_at_risk
            ) * 100
            if total_revenue_at_risk > 0
            else 0
        )

        # -----------------------------------------
        # RESULTS
        # -----------------------------------------

        print("\n========================================")
        print("       BATCH RECOVERY RESULTS")
        print("========================================")

        print(
            f"Payments analyzed: "
            f"{len(payments)}"
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
            f"Manual review cases: "
            f"{manual_review}"
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
            "manual_review_cases": manual_review,
            "revenue_recovered": revenue_recovered,
            "recovery_rate": recovery_rate,
        }

    finally:

        db.close()


if __name__ == "__main__":

    run_batch_recovery()