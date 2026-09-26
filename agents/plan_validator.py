from models.agent_models import RecoveryPlan


MIN_PLAN_STEPS = 5
MAX_PLAN_STEPS = 8


def validate_plan(plan: RecoveryPlan) -> list[str]:
    """
    Validate deterministic requirements for a generated recovery plan.

    Returns an empty list when the plan is valid.
    Otherwise returns human-readable validation errors.
    """
    errors = []

    if not plan.goal.strip():
        errors.append("Plan goal cannot be empty.")

    if not MIN_PLAN_STEPS <= len(plan.steps) <= MAX_PLAN_STEPS:
        errors.append(
            f"Plan must contain between {MIN_PLAN_STEPS} "
            f"and {MAX_PLAN_STEPS} steps."
        )

    step_ids = [step.step_id for step in plan.steps]

    if len(step_ids) != len(set(step_ids)):
        errors.append("Plan step IDs must be unique.")

    for step in plan.steps:
        if not step.objective.strip():
            errors.append(
                f"Step {step.step_id} has an empty objective."
            )

        if not step.rationale.strip():
            errors.append(
                f"Step {step.step_id} has an empty rationale."
            )

    return errors