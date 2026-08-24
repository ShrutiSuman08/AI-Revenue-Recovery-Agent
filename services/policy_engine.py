from dataclasses import dataclass


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str


MAX_AUTO_RECOVERY_AMOUNT = 10000
MAX_RECOVERY_ATTEMPTS = 2


def evaluate_recovery(payment, recommended_action):

    # Rule 1: Never automatically recover extremely high-value payments
    if payment.amount > MAX_AUTO_RECOVERY_AMOUNT:
        return PolicyDecision(
            allowed=False,
            reason="Payment amount exceeds automatic recovery limit."
        )

    # Rule 2: Stop after too many attempts
    if payment.attempt_count >= MAX_RECOVERY_ATTEMPTS:
        return PolicyDecision(
            allowed=False,
            reason="Maximum recovery attempts reached."
        )

    # Rule 3: Only allow known recovery actions
    allowed_actions = {
        "retry",
        "request_alternate_payment",
        "notify_and_retry_later"
    }

    if recommended_action not in allowed_actions:
        return PolicyDecision(
            allowed=False,
            reason="AI recommended an unsupported recovery action."
        )

    # If all rules pass
    return PolicyDecision(
        allowed=True,
        reason="Recovery action passed all policy checks."
    )