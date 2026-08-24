from database.models import Payment


HIGH_RECOVERY_FAILURES = {
    "network_error",
    "bank_timeout"
}

MEDIUM_RECOVERY_FAILURES = {
    "insufficient_funds",
    "card_declined"
}

NON_RECOVERABLE_FAILURES = {
    "card_blocked"
}


def get_revenue_at_risk(db):
    """
    Calculate total failed payment value.
    """

    failed_payments = (
        db.query(Payment)
        .filter(Payment.status == "failed")
        .all()
    )

    total = sum(
        payment.amount
        for payment in failed_payments
    )

    return round(total, 2)


def get_recoverable_payments(db):
    """
    Return payments that are currently eligible
    for automated recovery.
    """

    failed_payments = (
        db.query(Payment)
        .filter(Payment.status == "failed")
        .all()
    )

    recoverable = []

    for payment in failed_payments:

        # Stopping rule
        if payment.attempt_count >= 2:
            continue

        if payment.failure_reason in HIGH_RECOVERY_FAILURES:
            recoverable.append(payment)

        elif payment.failure_reason in MEDIUM_RECOVERY_FAILURES:
            recoverable.append(payment)

    return recoverable


def get_recoverable_revenue(db):
    """
    Calculate the total value of payments
    eligible for recovery.
    """

    payments = get_recoverable_payments(db)

    total = sum(
        payment.amount
        for payment in payments
    )

    return round(total, 2)


def get_recovery_action(payment):
    """
    Determine the initial recommended action
    based on deterministic business rules.
    """

    if payment.attempt_count >= 2:
        return "stop"

    if payment.failure_reason in HIGH_RECOVERY_FAILURES:
        return "retry"

    if payment.failure_reason == "insufficient_funds":
        return "notify_and_retry_later"

    if payment.failure_reason == "card_declined":
        return "request_alternate_payment"

    if payment.failure_reason == "card_blocked":
        return "escalate"

    return "unknown"