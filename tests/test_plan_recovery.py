from unittest.mock import patch

from graph.nodes import (
    validate_plan_node,
    repair_plan_node,
    plan_failure_node,
)

from graph.workflow import (
    route_after_plan_validation,
)

from models.agent_models import (
    PlanStep,
    RecoveryPlan,
    StepStatus,
)


def build_invalid_plan() -> RecoveryPlan:
    """
    Construct a deliberately incomplete plan.

    It is valid Pydantic data, but it violates our
    application-level requirement of 5-8 plan steps.
    """

    return RecoveryPlan(
        goal=(
            "Analyze failed payments and recover eligible revenue "
            "while respecting company recovery policies."
        ),
        steps=[
            PlanStep(
                step_id="bad_step",
                objective="Recover failed payments",
                rationale="Attempt to recover revenue.",
                status=StepStatus.PENDING,
            )
        ],
    )


def build_repaired_plan() -> RecoveryPlan:
    """
    Construct a valid repaired plan.

    The external LLM response is mocked during testing
    so planner-recovery tests remain deterministic.
    """

    return RecoveryPlan(
        goal=(
            "Analyze failed payments and recover eligible revenue "
            "while respecting company recovery policies."
        ),
        steps=[
            PlanStep(
                step_id="step_1",
                objective="Retrieve failed payments",
                rationale=(
                    "Evidence is required before decisions are made."
                ),
            ),
            PlanStep(
                step_id="step_2",
                objective="Investigate payment evidence",
                rationale=(
                    "Recovery decisions require failure context."
                ),
            ),
            PlanStep(
                step_id="step_3",
                objective="Recommend recovery actions",
                rationale=(
                    "Eligible payments need a recovery strategy."
                ),
            ),
            PlanStep(
                step_id="step_4",
                objective="Validate actions against policy",
                rationale=(
                    "Unsafe actions must not execute."
                ),
            ),
            PlanStep(
                step_id="step_5",
                objective="Execute approved recovery actions",
                rationale=(
                    "Approved actions can attempt revenue recovery."
                ),
            ),
            PlanStep(
                step_id="step_6",
                objective="Handle unsuccessful attempts",
                rationale=(
                    "Failures require adaptation or escalation."
                ),
            ),
            PlanStep(
                step_id="step_7",
                objective="Generate an auditable report",
                rationale=(
                    "Operations teams need traceable results."
                ),
            ),
        ],
    )


def test_invalid_plan_is_detected():
    """
    An incomplete plan must fail validation before
    payment execution begins.
    """

    state = {
        "plan": build_invalid_plan(),
        "execution_trace": [],
    }

    result = validate_plan_node(state)

    assert result["plan_validation_errors"]

    events = [
        event["event"]
        for event in result["execution_trace"]
    ]

    assert "plan_validation_failed" in events


def test_invalid_plan_can_be_repaired_and_revalidated():
    """
    Verify:

    invalid plan
        -> validation failure
        -> repair
        -> validation success
    """

    state = {
        "plan": build_invalid_plan(),
        "execution_trace": [],
        "plan_repair_count": 0,
    }

    # --------------------------------------------------------
    # 1. Validate deliberately invalid plan
    # --------------------------------------------------------

    validation_result = validate_plan_node(state)

    state.update(
        validation_result
    )

    assert state["plan_validation_errors"]

    # --------------------------------------------------------
    # 2. Repair it
    # --------------------------------------------------------

    repaired_plan = build_repaired_plan()

    with patch(
        "graph.nodes.repair_recovery_plan",
        return_value=repaired_plan,
    ):
        repair_result = repair_plan_node(state)

    state.update(
        repair_result
    )

    assert state["plan_repair_count"] == 1
    assert len(state["plan"].steps) == 7

    # --------------------------------------------------------
    # 3. Revalidate repaired plan
    # --------------------------------------------------------

    second_validation_result = validate_plan_node(
        state
    )

    state.update(
        second_validation_result
    )

    assert state["plan_validation_errors"] == []

    # --------------------------------------------------------
    # 4. Verify audit sequence
    # --------------------------------------------------------

    events = [
        event["event"]
        for event in state["execution_trace"]
    ]

    assert events == [
        "plan_validation_failed",
        "plan_repaired",
        "plan_validated",
    ]


def test_invalid_plan_after_repair_aborts_safely():
    """
    If the plan remains invalid after the single repair
    attempt, the workflow must create an explicit safe-stop
    result without processing payments.
    """

    state = {
        "plan": build_invalid_plan(),
        "plan_repair_count": 1,
        "plan_validation_errors": [
            "Plan must contain between 5 and 8 steps."
        ],
        "execution_trace": [],
    }

    result = plan_failure_node(state)

    report = result["final_report"]

    assert report["status"] == "aborted"
    assert report["stage"] == "planning"

    assert report["reason"] == (
        "Plan remained invalid after one repair attempt."
    )

    assert report["validation_errors"] == [
        "Plan must contain between 5 and 8 steps."
    ]

    assert report["payments_processed"] == 0

    events = [
        event["event"]
        for event in result["execution_trace"]
    ]

    assert events[-1] == "workflow_aborted"


def test_plan_routes_to_safe_stop_after_repair_failure():
    """
    The graph must route a repeatedly invalid plan
    to plan_failure rather than directly to END.
    """

    state = {
        "plan_validation_errors": [
            "Plan must contain between 5 and 8 steps."
        ],
        "plan_repair_count": 1,
    }

    route = route_after_plan_validation(
        state
    )

    assert route == "plan_failure"