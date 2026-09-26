from models.agent_models import PaymentEvidence, PolicyDecision


MAX_AUTO_RECOVERY_AMOUNT = 10000
MAX_RECOVERY_ATTEMPTS = 2

ALLOWED_AUTOMATIC_ACTIONS = {
    "retry",
    "request_alternate_payment",
    "notify_and_retry_later",
}


def evaluate_recovery_policy(
    payment: PaymentEvidence,
    proposed_action: str,
) -> PolicyDecision:
    """
    Determine whether a proposed recovery action is permitted.

    This tool is deterministic and has final authority over whether
    an automatic recovery action may proceed.
    """

    # Manual review is an escalation, not an automatic recovery action.
    if proposed_action == "manual_review":
        return PolicyDecision(
            allowed=True,
            reason=(
                "Payment requires human review. "
                "No automatic recovery action will be executed."
            ),
        )

    # High-value payments require human review.
    if payment.amount > MAX_AUTO_RECOVERY_AMOUNT:
        return PolicyDecision(
            allowed=False,
            reason="Payment amount exceeds automatic recovery limit.",
        )

    # Count actual autonomous recovery attempts.
    recovery_attempt_count = len(
        [
            attempt
            for attempt in payment.recovery_history
            if attempt.result not in {"blocked", "manual_review"}
        ]
    )

    if recovery_attempt_count >= MAX_RECOVERY_ATTEMPTS:
        return PolicyDecision(
            allowed=False,
            reason="Maximum automatic recovery attempts reached.",
        )

    if proposed_action not in ALLOWED_AUTOMATIC_ACTIONS:
        return PolicyDecision(
            allowed=False,
            reason="Proposed action is not supported by recovery policy.",
        )

    return PolicyDecision(
        allowed=True,
        reason="Recovery action passed all policy checks.",
    )