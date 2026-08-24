import random
from datetime import datetime, timedelta

from faker import Faker

from database.connection import SessionLocal
from database.models import Customer, Payment


fake = Faker()


# -----------------------------
# Configuration
# -----------------------------

NUM_CUSTOMERS = 150
NUM_PAYMENTS = 500


PAYMENT_METHODS = [
    "upi",
    "card",
    "netbanking",
    "wallet"
]


FAILURE_REASONS = [
    "network_error",
    "bank_timeout",
    "insufficient_funds",
    "card_declined",
    "card_blocked"
]


# -----------------------------
# Generate customers
# -----------------------------

def generate_customers(db):
    customers = []

    for i in range(1, NUM_CUSTOMERS + 1):

        customer = Customer(
            customer_id=f"CUST_{i:04d}",
            name=fake.name(),
            email=fake.email()
        )

        customers.append(customer)
        db.add(customer)

    db.commit()

    print(f"Created {len(customers)} customers.")

    return customers


# -----------------------------
# Generate payments
# -----------------------------

def generate_payments(db, customers):

    payments = []

    for i in range(1, NUM_PAYMENTS + 1):

        customer = random.choice(customers)

        amount = round(
            random.uniform(200, 15000),
            2
        )

        payment_method = random.choice(
            PAYMENT_METHODS
        )

        # 65% successful
        # 35% failed
        is_success = random.random() < 0.65

        if is_success:

            status = "success"
            failure_reason = None
            attempt_count = 1

        else:

            status = "failed"

            failure_reason = random.choice(
                FAILURE_REASONS
            )

            # Failed payments can have 0, 1 or 2 attempts
            attempt_count = random.randint(0, 2)

        created_at = datetime.now() - timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        payment = Payment(
            payment_id=f"PAY_{i:06d}",
            customer_id=customer.customer_id,
            amount=amount,
            status=status,
            failure_reason=failure_reason,
            payment_method=payment_method,
            attempt_count=attempt_count,
            created_at=created_at
        )

        payments.append(payment)
        db.add(payment)

    db.commit()

    print(f"Created {len(payments)} payments.")

    return payments


# -----------------------------
# Main
# -----------------------------

def main():

    db = SessionLocal()

    try:

        customers = generate_customers(db)

        generate_payments(
            db,
            customers
        )

        print("\nSynthetic data generation complete!")

    finally:

        db.close()


if __name__ == "__main__":
    main()