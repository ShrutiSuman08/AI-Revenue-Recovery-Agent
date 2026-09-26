import json
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from graph.nodes import (
    validate_plan_node,
    repair_plan_node,
)

from models.agent_models import (
    PlanStep,
    RecoveryPlan,
    StepStatus,
)


GOAL = (
    "Analyze failed payments, recover eligible revenue while "
    "respecting company recovery policies, and produce an "
    "auditable recovery report."
)


def build_invalid_plan():
    return RecoveryPlan(
        goal=GOAL,
        steps=[
            PlanStep(
                step_id="bad_step",
                objective="Recover failed payments",
                rationale="Attempt to recover revenue.",
                status=StepStatus.PENDING,
            )
        ],
    )


def build_repaired_plan():
    objectives = [
        (
            "Retrieve failed payments",
            "Evidence is required before recovery decisions.",
        ),
        (
            "Investigate payment evidence",
            "Failure context is required before selecting actions.",
        ),
        (
            "Recommend recovery actions",
            "Eligible payments need an appropriate recovery strategy.",
        ),
        (
            "Validate actions against policy",
            "Unsafe or prohibited actions must not execute.",
        ),
        (
            "Execute approved recovery actions",
            "Only policy-approved actions may attempt recovery.",
        ),
        (
            "Handle unsuccessful attempts",
            "Failures require adaptation or safe escalation.",
        ),
        (
            "Generate an auditable report",
            "Operations teams need traceable results.",
        ),
    ]

    return RecoveryPlan(
        goal=GOAL,
        steps=[
            PlanStep(
                step_id=f"step_{index}",
                objective=objective,
                rationale=rationale,
            )
            for index, (objective, rationale)
            in enumerate(objectives, start=1)
        ],
    )


def main():
    state = {
        "plan": build_invalid_plan(),
        "execution_trace": [],
        "plan_repair_count": 0,
    }

    original_plan = state["plan"].model_dump()

    # 1. Detect the deliberately invalid plan.
    state.update(
        validate_plan_node(state)
    )

    validation_errors = list(
        state["plan_validation_errors"]
    )

    # 2. Simulate a corrected response from the external LLM boundary.
    repaired_plan = build_repaired_plan()

    with patch(
        "graph.nodes.repair_recovery_plan",
        return_value=repaired_plan,
    ):
        state.update(
            repair_plan_node(state)
        )

    # 3. Revalidate the repaired plan using the real validator.
    state.update(
        validate_plan_node(state)
    )

    output = {
        "scenario": "planner_repair",
        "goal": GOAL,
        "deliberately_invalid_input": True,
        "external_llm_repair_mocked": True,
        "original_plan": original_plan,
        "initial_validation_errors": validation_errors,
        "repaired_plan": state["plan"].model_dump(),
        "final_validation_errors": state["plan_validation_errors"],
        "execution_trace": state["execution_trace"],
    }

    log_directory = PROJECT_ROOT / "evaluation" / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    output_path = log_directory / "plan_repair_demo.json"

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    print("=" * 60)
    print("Planner Recovery Evaluation")
    print("=" * 60)

    print("\nInitial validation errors:")
    for error in validation_errors:
        print(f"  - {error}")

    print("\nRecovery trace:")
    for event in state["execution_trace"]:
        print(f"  {event['event']}")

    print("\nFinal validation errors:")
    print(f"  {state['plan_validation_errors']}")

    print("\nResult:")
    if not state["plan_validation_errors"]:
        print("  Invalid plan successfully detected and repaired.")
    else:
        print("  Plan recovery failed.")

    print(f"\nLog saved to: {output_path}")


if __name__ == "__main__":
    main()