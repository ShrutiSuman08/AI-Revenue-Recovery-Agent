from database.connection import SessionLocal
from database.models import (
    RecoveryAttempt,
    AuditLog,
    RecoveryCase
)


db = SessionLocal()

try:

    db.query(RecoveryAttempt).delete()
    db.query(AuditLog).delete()
    db.query(RecoveryCase).delete()

    db.commit()

    print("Recovery data reset successfully.")
    print("Customers and payments were preserved.")

finally:

    db.close()
