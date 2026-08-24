from database.connection import SessionLocal
from database.models import Payment

from services.revenue_service import get_recoverable_payments
from services.recovery_simulator import execute_recovery


def main():

    db = SessionLocal()

    try:

        payments = get_recoverable_payments(db)

        print("\n===== RECOVERY SIMULATION =====")

        print(
            f"Eligible payments: {len(payments)}"
        )

        total_recovered = 0.0

        successful = 0
        failed = 0
        blocked = 0

        for payment in payments:

            result = execute_recovery(
                db,
                payment
            )

            total_recovered += (
                result["amount_recovered"]
            )

            if result["status"] == "success":
                successful += 1

            elif result["status"] == "failed":
                failed += 1

            elif result["status"] == "blocked":
                blocked += 1

        print("\n===== RESULTS =====")

        print(
            f"Successful recoveries: {successful}"
        )

        print(
            f"Failed attempts: {failed}"
        )

        print(
            f"Blocked cases: {blocked}"
        )

        print(
            f"Revenue recovered: "
            f"₹{total_recovered:,.2f}"
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()