import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from models.agent_models import RecoveryPlan


load_dotenv()


# --------------------------------------------------
# PLANNER INSTRUCTIONS
# --------------------------------------------------

SYSTEM_PROMPT = """
You are the planning component of an autonomous revenue recovery system.

Your job is to convert a high-level revenue recovery goal into a concise,
high-level execution plan.

Important planning rules:

1. Create a high-level plan, not payment-specific actions.
2. Do not invent payment IDs, amounts, failures, or outcomes.
3. Do not assume which recovery actions will succeed.
4. Every automatic recovery action must be validated against deterministic
   policy before execution.
5. Include handling of unsuccessful recovery attempts.
6. Include escalation to manual review when automatic recovery is unsafe
   or no longer appropriate.
7. Include generation of an auditable final report.
8. Produce between 5 and 8 plan steps.
9. Stay strictly within the capabilities provided below.
10. Do not invent external systems, policies, evidence, or actions.
"""


# --------------------------------------------------
# ACTUAL SYSTEM CAPABILITIES
# --------------------------------------------------

SYSTEM_CAPABILITIES = """
The system has exactly these capabilities.

AVAILABLE PAYMENT EVIDENCE:
- payment ID
- payment amount
- payment status
- payment method
- failure reason
- payment-provider attempt count
- previous recovery attempts and their outcomes

AVAILABLE RECOVERY ACTIONS:
- retry
- request_alternate_payment
- notify_and_retry_later
- manual_review

DETERMINISTIC POLICY CHECKS:
- maximum amount allowed for automatic recovery
- maximum number of automatic recovery attempts
- whether the proposed recovery action is supported

THE SYSTEM CAN:
- retrieve failed payment evidence
- investigate payment and recovery history
- analyze payment failures
- recommend recovery strategies
- validate recommendations against deterministic policies
- simulate approved recovery actions
- observe unsuccessful recovery attempts
- adapt the recovery strategy after failure
- escalate cases to manual review
- produce an auditable recovery report

THE SYSTEM CANNOT:
- evaluate credit risk
- evaluate dispute status
- send real customer communications
- send cases to collections
- write off debt
- mark payments as uncollectible
- execute real bank transactions
- execute real payment-provider transactions
- use evidence that is not listed above
- enforce policies that are not listed above

Do not invent capabilities, evidence, recovery actions, policies,
or external systems that are not explicitly listed here.
"""


# --------------------------------------------------
# CREATE RECOVERY PLAN
# --------------------------------------------------

def create_recovery_plan(goal: str) -> RecoveryPlan:
    """
    Convert a high-level revenue recovery goal into a structured
    RecoveryPlan.

    This function performs planning only. It does not retrieve payments,
    authorize recovery actions, or execute recovery.
    """

    if not goal or not goal.strip():
        raise ValueError("Recovery goal cannot be empty.")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured in .env"
        )

    model = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key,
    )

    structured_model = model.with_structured_output(
        RecoveryPlan
    )

    plan = structured_model.invoke(
        [
            (
                "system",
                f"{SYSTEM_PROMPT}\n\n{SYSTEM_CAPABILITIES}",
            ),
            (
                "human",
                f"""
Create a high-level execution plan for this goal:

{goal}

Remember:
- Stay within the provided system capabilities.
- Do not invent payment-specific information.
- Do not predict recovery outcomes.
""",
            ),
        ]
    )

    return plan

def repair_recovery_plan(
    plan: RecoveryPlan,
    validation_errors: list[str],
) -> RecoveryPlan:
    """
    Repair an invalid recovery plan using the validation errors.

    The repair is limited to the existing system capabilities.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured in .env"
        )

    model = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=api_key,
    )

    structured_model = model.with_structured_output(
        RecoveryPlan
    )

    errors_text = "\n".join(
        f"- {error}"
        for error in validation_errors
    )

    current_plan = plan.model_dump_json(indent=2)

    repaired_plan = structured_model.invoke(
        [
            (
                "system",
                f"""
{SYSTEM_PROMPT}

{SYSTEM_CAPABILITIES}

You are repairing an existing recovery plan.

Repair only what is necessary to satisfy the validation errors.

Do not invent new system capabilities, payment information,
policies, actions, or execution outcomes.

Preserve the original high-level goal.
""",
            ),
            (
                "human",
                f"""
CURRENT PLAN:

{current_plan}

VALIDATION ERRORS:

{errors_text}

Return a corrected RecoveryPlan.
""",
            ),
        ]
    )

    return repaired_plan