from database.connection import SessionLocal
from services.revenue_service import (
    get_revenue_at_risk,
    get_recoverable_payments,
    get_recoverable_revenue,
    get_recovery_action
)


db = SessionLocal()

try:

    revenue_at_risk = get_revenue_at_risk(db)

    recoverable_payments = get_recoverable_payments(db)

    recoverable_revenue = get_recoverable_revenue(db)

    print("\n===== REVENUE RECOVERY ANALYSIS =====")

    print(
        f"Revenue at risk: ₹{revenue_at_risk:,.2f}"
    )

    print(
        f"Recoverable payments: "
        f"{len(recoverable_payments)}"
    )

    print(
        f"Recoverable revenue: "
        f"₹{recoverable_revenue:,.2f}"
    )

    print("\n===== SAMPLE RECOVERY ACTIONS =====")

    for payment in recoverable_payments[:10]:

        action = get_recovery_action(payment)

        print(
            payment.payment_id,
            "|",
            f"₹{payment.amount:,.2f}",
            "|",
            payment.failure_reason,
            "|",
            "attempts:",
            payment.attempt_count,
            "|",
            "action:",
            action
        )

finally:

    db.close()