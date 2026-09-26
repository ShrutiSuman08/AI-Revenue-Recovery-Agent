import random

from models.agent_models import PaymentEvidence, RecoveryResult


ACTION_SUCCESS_PROBABILITIES = {
    "retry": 0.65,
    "request_alternate_payment": 0.45,
    "notify_and_retry_later": 0.35,
}


def execute_recovery(
    payment: PaymentEvidence,
    action: str,
    inject_failure: bool = False,
) -> RecoveryResult:
    """
    Simulate execution of an approved recovery action.

    inject_failure exists only to support deterministic testing of
    failure-handling and replanning behavior.
    """

    if action not in ACTION_SUCCESS_PROBABILITIES:
        return RecoveryResult(
            success=False,
            action=action,
            message="Unsupported recovery action.",
            recovered_amount=0.0,
            failure_type="unsupported_action",
        )

    if inject_failure:
        return RecoveryResult(
            success=False,
            action=action,
            message=(
                "Controlled recovery failure injected for "
                "failure-handling evaluation."
            ),
            recovered_amount=0.0,
            failure_type="injected_failure",
        )

    # Keep simulation reproducible for the same payment + action.
    rng = random.Random(
        f"{payment.payment_id}:{action}"
    )

    probability = ACTION_SUCCESS_PROBABILITIES[action]
    success = rng.random() < probability

    if success:
        return RecoveryResult(
            success=True,
            action=action,
            message=f"Payment successfully recovered using {action}.",
            recovered_amount=payment.amount,
            failure_type=None,
        )

    if action == "retry":
        message = "Retry failed. Payment remains unsuccessful."

    elif action == "request_alternate_payment":
        message = (
            "Customer did not complete the alternate payment method."
        )

    else:
        message = "Scheduled retry did not recover the payment."

    return RecoveryResult(
        success=False,
        action=action,
        message=message,
        recovered_amount=0.0,
        failure_type="recovery_failed",
    )