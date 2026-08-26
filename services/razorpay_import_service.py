from datetime import datetime

from database.connection import SessionLocal
from database.models import (
    Customer,
    Payment
)

from services.razorpay_service import fetch_payment


RAZORPAY_TEST_CUSTOMER_ID = "CUST_RAZORPAY_TEST"


def get_or_create_razorpay_test_customer(db):

    customer = (
        db.query(Customer)
        .filter(
            Customer.customer_id == RAZORPAY_TEST_CUSTOMER_ID
        )
        .first()
    )

    if customer:
        return customer

    customer = Customer(
        customer_id=RAZORPAY_TEST_CUSTOMER_ID,
        name="Razorpay Test Customer",
        email="razorpay-test@example.com"
    )

    db.add(customer)
    db.flush()

    return customer


def import_razorpay_payment(payment_id):

    db = SessionLocal()

    try:

        # -----------------------------------------
        # FETCH PAYMENT FROM RAZORPAY
        # -----------------------------------------

        razorpay_payment = fetch_payment(payment_id)

        # -----------------------------------------
        # IDEMPOTENCY CHECK
        # -----------------------------------------

        existing_payment = (
            db.query(Payment)
            .filter(
                Payment.payment_id == payment_id
            )
            .first()
        )

        if existing_payment:

            print(
                f"Payment {payment_id} already exists."
            )

            return existing_payment

        # -----------------------------------------
        # CREATE TEST CUSTOMER IF NEEDED
        # -----------------------------------------

        customer = get_or_create_razorpay_test_customer(
            db
        )

        # -----------------------------------------
        # MAP RAZORPAY FAILURE
        # -----------------------------------------

        error_description = (
            razorpay_payment.get("error_description")
            or "razorpay_payment_failed"
        )

        payment = Payment(
            payment_id=razorpay_payment["id"],
            customer_id=customer.customer_id,
            amount=razorpay_payment["amount"] / 100,
            status=razorpay_payment["status"],
            failure_reason=error_description,
            payment_method=(
                razorpay_payment.get("method")
                or "unknown"
            ),
            attempt_count=0,
            created_at=datetime.utcnow()
        )

        # -----------------------------------------
        # SAVE PAYMENT
        # -----------------------------------------

        db.add(payment)

        db.commit()

        db.refresh(payment)

        print("\n===== RAZORPAY PAYMENT IMPORTED =====")

        print(
            "Payment ID:",
            payment.payment_id
        )

        print(
            "Amount:",
            f"₹{payment.amount:,.2f}"
        )

        print(
            "Status:",
            payment.status
        )

        print(
            "Method:",
            payment.payment_method
        )

        print(
            "Failure reason:",
            payment.failure_reason
        )

        return payment

    finally:

        db.close()