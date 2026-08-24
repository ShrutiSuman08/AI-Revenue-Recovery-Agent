from dataclasses import dataclass
import random


@dataclass
class RecoveryResult:
    success: bool
    action: str
    message: str
    recovered_amount: float


def execute_recovery(payment, action):

    # ------------------------------------------------
    # Deterministic randomness
    # ------------------------------------------------
    # Same payment always gets the same simulated
    # outcome across repeated evaluations.
    rng = random.Random(payment.payment_id)

    probability = 0.0

    # ------------------------------------------------
    # Recovery success probabilities
    # ------------------------------------------------

    if action == "retry":

        probability = 0.65

    elif action == "request_alternate_payment":

        probability = 0.45

    elif action == "notify_and_retry_later":

        probability = 0.35

    else:

        return RecoveryResult(
            success=False,
            action=action,
            message="Unsupported recovery action.",
            recovered_amount=0.0
        )

    # ------------------------------------------------
    # Simulate recovery
    # ------------------------------------------------

    success = rng.random() < probability

    if success:

        return RecoveryResult(
            success=True,
            action=action,
            message=(
                f"Payment successfully recovered using "
                f"{action}."
            ),
            recovered_amount=payment.amount
        )

    # ------------------------------------------------
    # Failed recovery
    # ------------------------------------------------

    if action == "retry":

        message = (
            "Retry failed. Payment remains unsuccessful."
        )

    elif action == "request_alternate_payment":

        message = (
            "Customer did not complete the alternate "
            "payment method."
        )

    else:

        message = (
            "Scheduled retry did not recover the payment."
        )

    return RecoveryResult(
        success=False,
        action=action,
        message=message,
        recovered_amount=0.0
    )