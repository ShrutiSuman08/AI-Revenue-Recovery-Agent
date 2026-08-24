from database.connection import SessionLocal
from database.models import Payment

from services.agent_service import process_payment


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

        result = process_payment(payment, db)

        print("\n===== FINAL AGENT RESULT =====")

        for key, value in result.items():

            print(
                f"{key}: {value}"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()