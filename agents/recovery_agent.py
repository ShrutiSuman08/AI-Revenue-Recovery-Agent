import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from models.agent_models import (
    PaymentEvidence,
    RecoveryDecision,
)


load_dotenv()


AVAILABLE_ACTIONS = [
    "retry",
    "request_alternate_payment",
    "notify_and_retry_later",
    "manual_review",
]


def create_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured in .env"
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
        api_key=api_key,
    )


def analyze_payment(
    payment: PaymentEvidence,
) -> RecoveryDecision:
    """
    Analyze payment evidence and recommend a recovery strategy.

    This function only recommends an action.
    It does not authorize or execute recovery.
    """

    if payment.recovery_history:
        previous_attempts_text = "\n".join(
            (
                f"- Action: {attempt.action} | "
                f"Result: {attempt.result}"
            )
            for attempt in payment.recovery_history
        )
    else:
        previous_attempts_text = (
            "No previous recovery attempts."
        )

    available_actions_text = "\n".join(
        f"- {action}"
        for action in AVAILABLE_ACTIONS
    )

    llm = create_llm()

    structured_llm = llm.with_structured_output(
        RecoveryDecision
    )

    prompt = f"""
You are the reasoning component of an autonomous revenue
recovery system.

Analyze the following failed payment evidence.

Payment ID:
{payment.payment_id}

Amount:
₹{payment.amount}

Payment method:
{payment.payment_method}

Failure reason:
{payment.failure_reason}

Payment-provider attempt count:
{payment.attempt_count}

PREVIOUS RECOVERY ATTEMPTS:

{previous_attempts_text}

AVAILABLE RECOVERY ACTIONS:

{available_actions_text}

Your task:

1. Diagnose the likely reason for the payment failure.
2. Determine the risk level as low, medium, or high.
3. Recommend one recovery action.
4. Explain why that action is appropriate.
5. Provide a confidence score from 0 to 1.

RECOVERY MEMORY RULES:

- Review previous recovery attempts carefully.
- If an action previously failed, avoid recommending the same
  action again unless there is a strong reason.
- Prefer a different strategy after an unsuccessful attempt.
- Become more conservative after repeated failures.
- Use manual_review when automatic recovery is no longer
  appropriate.

IMPORTANT:

- Do not claim that a recovery action has succeeded before it
  has actually been executed.
- Do not execute any payment action.
- Only recommend an action.
- A separate deterministic policy tool has final authority over
  whether the recommendation may execute.
"""

    return structured_llm.invoke(prompt)
