from dataclasses import dataclass


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str


MAX_AUTO_RECOVERY_AMOUNT = 10000
MAX_RECOVERY_ATTEMPTS = 2


def evaluate_recovery(payment, recommended_action):

    # -----------------------------------------
    # RULE 1: MANUAL REVIEW
    # -----------------------------------------
    # Manual review is an escalation, not an
    # automatic payment action.
    #
    # Therefore it is allowed even when the
    # payment has already reached the automatic
    # recovery attempt limit.

    if recommended_action == "manual_review":

        return PolicyDecision(
            allowed=True,
            reason=(
                "Payment requires human review. "
                "No automatic recovery action will be executed."
            )
        )

    # -----------------------------------------
    # RULE 2: NEVER AUTO-RECOVER HIGH-VALUE
    # PAYMENTS
    # -----------------------------------------

    if payment.amount > MAX_AUTO_RECOVERY_AMOUNT:

        return PolicyDecision(
            allowed=False,
            reason=(
                "Payment amount exceeds automatic "
                "recovery limit."
            )
        )

    # -----------------------------------------
    # RULE 3: STOP AFTER TOO MANY ATTEMPTS
    # -----------------------------------------

    if payment.attempt_count >= MAX_RECOVERY_ATTEMPTS:

        return PolicyDecision(
            allowed=False,
            reason=(
                "Maximum recovery attempts reached."
            )
        )

    # -----------------------------------------
    # RULE 4: ONLY ALLOW KNOWN AUTOMATIC ACTIONS
    # -----------------------------------------

    allowed_actions = {
        "retry",
        "request_alternate_payment",
        "notify_and_retry_later"
    }

    if recommended_action not in allowed_actions:

        return PolicyDecision(
            allowed=False,
            reason=(
                "AI recommended an unsupported "
                "recovery action."
            )
        )

    # -----------------------------------------
    # ALL POLICY CHECKS PASSED
    # -----------------------------------------

    return PolicyDecision(
        allowed=True,
        reason=(
            "Recovery action passed all "
            "policy checks."
        )
    )