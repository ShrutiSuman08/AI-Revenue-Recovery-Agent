import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


load_dotenv()


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


def analyze_payment(payment):

    llm = create_llm()

    structured_llm = llm.with_structured_output(
        RecoveryDecision
    )

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

Previous attempts:
{payment.attempt_count}

Determine:

1. Why the payment likely failed.
2. The risk level.
3. The best recovery action.
4. Why that action is appropriate.
5. Your confidence from 0 to 1.

Possible recovery actions include:

- retry
- request_alternate_payment
- notify_and_retry_later
- manual_review
- no_action

Do NOT execute any payment action.
Only provide a recommendation.

Remember:
The final action will be decided by a separate deterministic policy engine.
"""

    return structured_llm.invoke(prompt)