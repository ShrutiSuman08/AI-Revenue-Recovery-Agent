from database.connection import SessionLocal
from database.models import (
    RecoveryCase,
    RecoveryAttempt,
    AuditLog
)


def reset_recovery_data():

    db = SessionLocal()

    try:
        db.query(AuditLog).delete()
        db.query(RecoveryAttempt).delete()
        db.query(RecoveryCase).delete()

        db.commit()

        print("Recovery data reset successfully.")
        print("Customers and payments were preserved.")

    finally:
        db.close()


if __name__ == "__main__":
    reset_recovery_data()