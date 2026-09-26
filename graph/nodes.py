from datetime import datetime, timezone

from agents.planner import (
    create_recovery_plan,
    repair_recovery_plan,
)

from agents.plan_validator import validate_plan
from agents.recovery_agent import analyze_payment

from demo.scenarios import get_demo_payments

from graph.state import AgentState

from tools.policy_tool import evaluate_recovery_policy
from tools.recovery_tool import execute_recovery

from models.agent_models import (
    RecoveryAttemptEvidence,
    RecoveryReport,
    ReportSummary,
    StepStatus,
)


MAX_FAILURES_PER_CASE = 2


# ============================================================
# PLAN PROGRESS HELPER
# ============================================================

def update_plan_step_status_by_index(
    state: AgentState,
    step_index: int,
    status: StepStatus,
) -> None:
    """
    Update a generated plan step using its ordered position.

    We intentionally do not depend on LLM-generated step IDs because
    the planner may produce IDs such as "step1", "step_1", or another
    valid representation.
    """

    plan = state.get("plan")

    if plan is None:
        return

    if 0 <= step_index < len(plan.steps):
        plan.steps[step_index].status = status


# ============================================================
# PLANNING
# ============================================================

def create_plan_node(state: AgentState) -> dict:
    """
    Generate the high-level recovery plan before any payment
    recovery action is executed.
    """

    goal = state["goal"]
    plan = create_recovery_plan(goal)

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "plan_created",
        "details": {
            "goal": goal,
            "step_count": len(plan.steps),
        },
    }

    return {
        "plan": plan,
        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }


def validate_plan_node(state: AgentState) -> dict:
    """
    Validate the structure of the generated recovery plan.

    This node does not repair the plan. It only records whether
    validation succeeded and what errors were found.
    """

    plan = state["plan"]
    errors = validate_plan(plan)
    is_valid = len(errors) == 0

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": (
            "plan_validated"
            if is_valid
            else "plan_validation_failed"
        ),
        "details": {
            "valid": is_valid,
            "errors": errors,
        },
    }

    return {
        "plan_validation_errors": errors,
        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }


def repair_plan_node(state: AgentState) -> dict:
    """
    Attempt to repair an invalid initial recovery plan.

    Only one repair attempt is permitted by the workflow.
    """

    plan = state["plan"]
    errors = state["plan_validation_errors"]

    repaired_plan = repair_recovery_plan(
        plan=plan,
        validation_errors=errors,
    )

    repair_count = (
        state.get(
            "plan_repair_count",
            0,
        )
        + 1
    )

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "plan_repaired",
        "details": {
            "repair_attempt": repair_count,
            "previous_errors": errors,
            "step_count": len(repaired_plan.steps),
        },
    }

    return {
        "plan": repaired_plan,
        "plan_repair_count": repair_count,
        "plan_validation_errors": [],
        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }


def plan_failure_node(state: AgentState) -> dict:
    """
    Safely stop the workflow when the recovery plan remains
    invalid after the single permitted repair attempt.

    No payment data is loaded and no recovery action executes.
    Instead, the workflow returns an explicit and auditable
    planning-stage failure result.
    """

    errors = state.get(
        "plan_validation_errors",
        [],
    )

    failure_report = {
        "status": "aborted",
        "stage": "planning",
        "reason": (
            "Plan remained invalid after one repair attempt."
        ),
        "validation_errors": errors,
        "payments_processed": 0,
    }

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "workflow_aborted",
        "details": {
            "stage": "planning",
            "reason": (
                "Plan remained invalid after one repair attempt."
            ),
            "validation_errors": errors,
            "payments_processed": 0,
        },
    }

    return {
        "final_report": failure_report,
        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }


# ============================================================
# PAYMENT LOADING
# ============================================================

def load_payments_node(state: AgentState) -> dict:
    """
    Load the deterministic evaluation payment batch.

    The demo fixture is used so important workflow branches
    can be reproduced consistently during evaluation.

    Plan progress is updated when a plan exists, but this node
    can also operate independently in unit tests.
    """

    payments = get_demo_payments()

    update_plan_step_status_by_index(
        state=state,
        step_index=0,
        status=StepStatus.COMPLETED,
    )

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "payments_loaded",
        "details": {
            "source": "demo_fixture",
            "payment_count": len(payments),
            "payment_ids": [
                payment.payment_id
                for payment in payments
            ],
        },
    }

    result = {
        "payments": payments,
        "current_payment_index": 0,
        "case_results": [],
        "failure_count": 0,
        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }

    # A plan exists during the complete graph workflow, but unit
    # tests are also allowed to execute this node independently.
    if state.get("plan") is not None:
        result["plan"] = state["plan"]

    return result


# ============================================================
# PAYMENT SELECTION
# ============================================================

def select_payment_node(state: AgentState) -> dict:
    """
    Select the next payment in the batch for processing.

    The node can run as part of the full workflow or independently
    in focused unit tests that do not construct a planner state.
    """

    payments = state["payments"]
    current_index = state["current_payment_index"]

    if current_index >= len(payments):
        return {}

    payment = payments[current_index]
    plan = state.get("plan")

    # Once the first payment is selected, batch processing has begun.
    # Remaining plan objectives are therefore actively executing.
    #
    # We use plan position rather than an LLM-generated step ID.
    if current_index == 0 and plan is not None:
        for step_index, step in enumerate(plan.steps):
            if step_index > 0:
                step.status = StepStatus.RUNNING

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "payment_selected",
        "details": {
            "payment_id": payment.payment_id,
            "batch_index": current_index,
        },
    }

    result = {
        "current_payment": payment,

        # Each payment receives its own autonomous failure budget.
        "failure_count": 0,

        # Remove state belonging to the previously processed case.
        "recovery_decision": None,
        "policy_decision": None,
        "recovery_result": None,

        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }

    if plan is not None:
        result["plan"] = plan

    return result


# ============================================================
# PAYMENT ANALYSIS
# ============================================================

def analyze_payment_node(state: AgentState) -> dict:
    """
    Analyze the currently selected payment and recommend
    a recovery strategy.

    This node performs reasoning only. It does not authorize
    or execute the recommended action.
    """

    payment = state["current_payment"]
    decision = analyze_payment(payment)

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "recovery_recommended",
        "details": {
            "payment_id": payment.payment_id,
            "recommended_action": decision.recommended_action,
            "risk_level": decision.risk_level,
            "confidence": decision.confidence,
            "failure_count": state.get(
                "failure_count",
                0,
            ),
        },
    }

    return {
        "recovery_decision": decision,
        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }


# ============================================================
# POLICY VALIDATION
# ============================================================

def check_policy_node(state: AgentState) -> dict:
    """
    Validate the LLM-recommended recovery action against
    deterministic business policies.

    The LLM recommendation has no execution authority.
    """

    payment = state["current_payment"]
    decision = state["recovery_decision"]

    policy_decision = evaluate_recovery_policy(
        payment=payment,
        proposed_action=decision.recommended_action,
    )

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": (
            "policy_approved"
            if policy_decision.allowed
            else "policy_blocked"
        ),
        "details": {
            "payment_id": payment.payment_id,
            "proposed_action": decision.recommended_action,
            "allowed": policy_decision.allowed,
            "reason": policy_decision.reason,
        },
    }

    return {
        "policy_decision": policy_decision,
        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }


# ============================================================
# RECOVERY EXECUTION
# ============================================================

def execute_recovery_node(state: AgentState) -> dict:
    """
    Execute a policy-approved recovery action.

    Controlled failure injection is configured through graph state
    so evaluation behavior remains explicit and reproducible.
    """

    payment = state["current_payment"]
    decision = state["recovery_decision"]
    policy_decision = state["policy_decision"]

    if not policy_decision.allowed:
        raise ValueError(
            "Recovery execution attempted without policy approval."
        )

    action = decision.recommended_action

    fault_injections = state.get(
        "fault_injections",
        {},
    )

    # Inject the configured failure only once for the matching
    # payment/action pair.
    inject_failure = (
        fault_injections.get(payment.payment_id) == action
        and not any(
            attempt.action == action
            and attempt.result == "injected_failure"
            for attempt in payment.recovery_history
        )
    )

    result = execute_recovery(
        payment=payment,
        action=action,
        inject_failure=inject_failure,
    )

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": (
            "recovery_succeeded"
            if result.success
            else "recovery_failed"
        ),
        "details": {
            "payment_id": payment.payment_id,
            "action": action,
            "success": result.success,
            "recovered_amount": result.recovered_amount,
            "failure_type": result.failure_type,
            "failure_injected": inject_failure,
        },
    }

    return {
        "recovery_result": result,
        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }


# ============================================================
# FAILURE HANDLING / REPLANNING
# ============================================================

def handle_failure_node(state: AgentState) -> dict:
    """
    Record an unsuccessful recovery attempt so the agent can
    reason over the new evidence and choose a different strategy.
    """

    payment = state["current_payment"]
    result = state["recovery_result"]

    if result is None or result.success:
        raise ValueError(
            "Failure handling requires an unsuccessful recovery result."
        )

    attempt = RecoveryAttemptEvidence(
        action=result.action,
        result=result.failure_type or "failed",
        amount_recovered=result.recovered_amount,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # This becomes new evidence for the next reasoning pass.
    payment.recovery_history.append(attempt)

    failure_count = (
        state.get(
            "failure_count",
            0,
        )
        + 1
    )

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "recovery_failure_recorded",
        "details": {
            "payment_id": payment.payment_id,
            "failed_action": result.action,
            "failure_type": result.failure_type,
            "failure_count": failure_count,
        },
    }

    return {
        "current_payment": payment,
        "failure_count": failure_count,

        # Force a fresh reasoning/policy cycle over updated evidence.
        "recovery_decision": None,
        "policy_decision": None,

        "execution_trace": [
            *state.get("execution_trace", []),
            trace_event,
        ],
    }


def can_replan(state: AgentState) -> bool:
    """
    Return whether the current case may attempt another
    autonomous recovery strategy after a failure.
    """

    return (
        state.get(
            "failure_count",
            0,
        )
        < MAX_FAILURES_PER_CASE
    )


# ============================================================
# CASE FINALIZATION
# ============================================================

def finalize_case_node(state: AgentState) -> dict:
    """
    Finalize the current payment case and advance the batch.

    A case may finish because:
    - recovery succeeded,
    - policy blocked automatic recovery,
    - manual review was selected,
    - or the autonomous failure limit was reached.
    """

    payment = state["current_payment"]
    decision = state.get("recovery_decision")
    policy_decision = state.get("policy_decision")
    recovery_result = state.get("recovery_result")
    failure_count = state.get(
        "failure_count",
        0,
    )

    # --------------------------------------------------------
    # Successful autonomous recovery
    # --------------------------------------------------------

    if (
        recovery_result is not None
        and recovery_result.success
    ):
        status = "recovered"
        recovered_amount = recovery_result.recovered_amount
        final_action = recovery_result.action
        reason = recovery_result.message

        success_attempt = RecoveryAttemptEvidence(
            action=recovery_result.action,
            result="success",
            amount_recovered=recovery_result.recovered_amount,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        payment.recovery_history.append(
            success_attempt
        )

    # --------------------------------------------------------
    # Agent requested human review
    # --------------------------------------------------------

    elif (
        decision is not None
        and decision.recommended_action == "manual_review"
    ):
        status = "manual_review"
        recovered_amount = 0.0
        final_action = "manual_review"
        reason = decision.reason

    # --------------------------------------------------------
    # Deterministic policy blocked automatic execution
    # --------------------------------------------------------

    elif (
        policy_decision is not None
        and not policy_decision.allowed
    ):
        status = "policy_blocked"
        recovered_amount = 0.0

        final_action = (
            decision.recommended_action
            if decision is not None
            else None
        )

        reason = policy_decision.reason

    # --------------------------------------------------------
    # Autonomous recovery failure budget exhausted
    # --------------------------------------------------------

    elif failure_count >= MAX_FAILURES_PER_CASE:
        status = "manual_review"
        recovered_amount = 0.0
        final_action = "manual_review"

        reason = (
            "Autonomous recovery stopped after reaching "
            "the maximum failure limit."
        )

    else:
        raise ValueError(
            "Current payment does not have a valid final state."
        )

    case_result = {
        "payment_id": payment.payment_id,
        "amount": payment.amount,
        "status": status,
        "final_action": final_action,
        "recovered_amount": recovered_amount,
        "failure_count": failure_count,
        "reason": reason,
    }

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "case_finalized",
        "details": case_result,
    }

    return {
        "case_results": [
            *state.get(
                "case_results",
                [],
            ),
            case_result,
        ],
        "current_payment_index": (
            state["current_payment_index"]
            + 1
        ),
        "execution_trace": [
            *state.get(
                "execution_trace",
                [],
            ),
            trace_event,
        ],
    }


# ============================================================
# FINAL REPORT
# ============================================================

def generate_report_node(state: AgentState) -> dict:
    """
    Generate the final deterministic recovery report from
    completed case results and execution evidence.
    """

    case_results = state.get(
        "case_results",
        [],
    )

    total_revenue_at_risk = sum(
        case["amount"]
        for case in case_results
    )

    recovered_cases = [
        case
        for case in case_results
        if case["status"] == "recovered"
    ]

    policy_blocked_cases = [
        case
        for case in case_results
        if case["status"] == "policy_blocked"
    ]

    manual_review_cases = [
        case
        for case in case_results
        if case["status"] == "manual_review"
    ]

    # Counts failures encountered during this workflow run.
    failed_recovery_attempts = sum(
        case["failure_count"]
        for case in case_results
    )

    summary = ReportSummary(
        total_payments=len(
            case_results
        ),
        total_revenue_at_risk=total_revenue_at_risk,
        recovered_payments=len(
            recovered_cases
        ),
        recovered_revenue=sum(
            case["recovered_amount"]
            for case in recovered_cases
        ),
        policy_blocked_payments=len(
            policy_blocked_cases
        ),
        manual_review_payments=len(
            manual_review_cases
        ),
        failed_recovery_attempts=failed_recovery_attempts,
    )

    report = RecoveryReport(
        goal=state["goal"],
        summary=summary,
        cases=case_results,
    )

    # The report is produced only after every case reaches a
    # terminal state, so the complete high-level plan can now
    # be marked complete.
    plan = state.get("plan")

    if plan is not None:
        for step in plan.steps:
            step.status = StepStatus.COMPLETED

    trace_event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "report_generated",
        "details": {
            "total_payments": summary.total_payments,
            "recovered_revenue": summary.recovered_revenue,
        },
    }

    result = {
        "final_report": report.model_dump(),
        "execution_trace": [
            *state.get(
                "execution_trace",
                [],
            ),
            trace_event,
        ],
    }

    if plan is not None:
        result["plan"] = plan

    return result