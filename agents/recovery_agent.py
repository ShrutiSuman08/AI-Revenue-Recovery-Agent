import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


load_dotenv()


# -----------------------------------------
# AI DECISION STRUCTURE
# -----------------------------------------

class RecoveryDecision(BaseModel):

    diagnosis: str = Field(
        description="Diagnosis of why the payment failed"
    )

    risk_level: str = Field(
        description="Risk level: low, medium, or high"
    )

    recommended_action: str = Field(
        description="Recommended recovery action"
    )

    reason: str = Field(
        description="Explanation for the recommendation"
    )

    confidence: float = Field(
        description="Confidence score between 0 and 1"
    )


# -----------------------------------------
# CREATE LLM
# -----------------------------------------

def create_llm():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:

        raise ValueError(
            "GROQ_API_KEY is not configured in .env"
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
        api_key=api_key
    )


# -----------------------------------------
# ANALYZE PAYMENT
# -----------------------------------------

def analyze_payment(
    payment,
    previous_actions=None,
    previous_results=None
):

    # -----------------------------------------
    # DEFAULT VALUES
    # -----------------------------------------

    if previous_actions is None:
        previous_actions = []

    if previous_results is None:
        previous_results = []


    # -----------------------------------------
    # FORMAT PREVIOUS ATTEMPTS
    # -----------------------------------------

    if previous_actions:

        previous_attempts_text = "\n".join(
            f"- Action: {action} | "
            f"Result: {result}"
            for action, result
            in zip(
                previous_actions,
                previous_results
            )
        )

    else:

        previous_attempts_text = (
            "No previous recovery attempts."
        )


    # -----------------------------------------
    # CREATE LLM
    # -----------------------------------------

    llm = create_llm()

    structured_llm = llm.with_structured_output(
        RecoveryDecision
    )


    # -----------------------------------------
    # AI PROMPT
    # -----------------------------------------

    prompt = f"""
You are an AI revenue recovery analyst.

Analyze the following failed payment.

Payment ID:
{payment.payment_id}

Amount:
₹{payment.amount}

Payment method:
{payment.payment_method}

Failure reason:
{payment.failure_reason}

Previous payment attempts:
{payment.attempt_count}


PREVIOUS RECOVERY ATTEMPTS:

{previous_attempts_text}


Your task:

1. Diagnose why the payment failed.
2. Determine the risk level.
3. Recommend the best recovery action.
4. Explain why the action is appropriate.
5. Provide a confidence score from 0 to 1.


Possible recovery actions:

- retry
- request_alternate_payment
- notify_and_retry_later
- manual_review
- no_action


IMPORTANT RECOVERY MEMORY RULES:

- Review the previous recovery attempts carefully.
- If an action previously failed, do NOT recommend the same
  action again unless there is a strong reason.
- Prefer a different recovery strategy after a failed attempt.
- If multiple recovery strategies have already failed,
  consider manual_review or no_action.
- Do not repeatedly recommend "retry".
- The recovery process should become more conservative
  after repeated failures.


IMPORTANT:

Do NOT execute any payment action.

Only provide a recommendation.

The final action will be decided by a separate
deterministic policy engine.
"""


    # -----------------------------------------
    # GET STRUCTURED AI DECISION
    # -----------------------------------------

    return structured_llm.invoke(prompt)