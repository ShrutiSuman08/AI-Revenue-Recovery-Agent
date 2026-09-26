import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from graph.workflow import revenue_ops_graph


GOAL = (
    "Analyze todays failed payments, recover eligible revenue while "
    "respecting company recovery policies, handle unsuccessful recovery "
    "attempts safely, and produce an auditable recovery report."
)


def main():
    initial_state = {
        "goal": GOAL,
        "execution_trace": [],
        "fault_injections": {
            "PAY-004": "retry",
        },
    }

    result = revenue_ops_graph.invoke(initial_state)

    output = {
        "goal": GOAL,
        "plan": result["plan"].model_dump(),
        "execution_trace": result["execution_trace"],
        "final_report": result["final_report"],
    }

    output_dir = Path("evaluation/logs")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "demo_run.json"

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
    print("RevenueOps Agent Evaluation Run")
    print("=" * 60)

    print(f"\nGoal:\n{GOAL}")

    print("\nPlan:")
    for step in result["plan"].steps:
        print(
            f"  {step.step_id}. "
            f"{step.objective}"
        )

    print("\nFinal Summary:")
    summary = result["final_report"]["summary"]

    print(
        f"  Payments processed: "
        f"{summary['total_payments']}"
    )
    print(
        f"  Revenue at risk: "
        f"₹{summary['total_revenue_at_risk']:.2f}"
    )
    print(
        f"  Revenue recovered: "
        f"₹{summary['recovered_revenue']:.2f}"
    )
    print(
        f"  Policy blocked: "
        f"{summary['policy_blocked_payments']}"
    )
    print(
        f"  Manual review: "
        f"{summary['manual_review_payments']}"
    )
    print(
        f"  Failed recovery attempts: "
        f"{summary['failed_recovery_attempts']}"
    )

    print(
        f"\nExecution events: "
        f"{len(result['execution_trace'])}"
    )

    print(
        f"Log saved to: {output_path}"
    )


if __name__ == "__main__":
    main()