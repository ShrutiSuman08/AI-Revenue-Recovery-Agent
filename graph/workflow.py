from langgraph.graph import StateGraph, START, END

from graph.state import AgentState
from graph.nodes import (
    create_plan_node,
    validate_plan_node,
    repair_plan_node,
    plan_failure_node,
    load_payments_node,
    select_payment_node,
    analyze_payment_node,
    check_policy_node,
    execute_recovery_node,
    handle_failure_node,
    finalize_case_node,
    generate_report_node,
    can_replan,
)


# ============================================================
# ROUTING FUNCTIONS
# ============================================================

def route_after_plan_validation(state: AgentState) -> str:
    """
    Decide whether the initial plan can proceed,
    needs one repair attempt, or must stop safely.
    """

    errors = state.get("plan_validation_errors", [])

    # Valid plan: continue with payment loading.
    if not errors:
        return "load_payments"

    # Allow exactly one automatic plan repair.
    if state.get("plan_repair_count", 0) < 1:
        return "repair_plan"

    # Still invalid after one repair attempt:
    # stop explicitly and produce an auditable failure result.
    return "plan_failure"


def route_after_policy(state: AgentState) -> str:
    """
    Decide whether the proposed recovery action may execute.

    Manual-review decisions and policy-blocked actions
    never reach the recovery execution tool.
    """

    decision = state["recovery_decision"]
    policy = state["policy_decision"]

    # Manual review is a terminal case decision,
    # not an executable recovery action.
    if decision.recommended_action == "manual_review":
        return "finalize_case"

    # Deterministic policy engine has final authority.
    if not policy.allowed:
        return "finalize_case"

    return "execute_recovery"


def route_after_execution(state: AgentState) -> str:
    """
    Successful recovery finalizes the case.

    Failed recovery enters failure handling so the
    failure becomes evidence for the next decision.
    """

    result = state["recovery_result"]

    if result.success:
        return "finalize_case"

    return "handle_failure"


def route_after_failure(state: AgentState) -> str:
    """
    Re-analyze the payment while autonomous recovery
    budget remains.

    Once the failure limit is reached, stop automatic
    recovery and finalize/escalate the case.
    """

    if can_replan(state):
        return "analyze_payment"

    return "finalize_case"


def route_after_case(state: AgentState) -> str:
    """
    Continue processing the batch until every payment
    has been finalized.

    Once the batch is complete, generate the structured
    final recovery report.
    """

    if state["current_payment_index"] < len(state["payments"]):
        return "select_payment"

    return "generate_report"


# ============================================================
# WORKFLOW
# ============================================================

def build_workflow():
    workflow = StateGraph(AgentState)

    # ========================================================
    # PLANNING NODES
    # ========================================================

    workflow.add_node(
        "create_plan",
        create_plan_node,
    )

    workflow.add_node(
        "validate_plan",
        validate_plan_node,
    )

    workflow.add_node(
        "repair_plan",
        repair_plan_node,
    )

    workflow.add_node(
        "plan_failure",
        plan_failure_node,
    )

    # ========================================================
    # BATCH / CASE-PROCESSING NODES
    # ========================================================

    workflow.add_node(
        "load_payments",
        load_payments_node,
    )

    workflow.add_node(
        "select_payment",
        select_payment_node,
    )

    workflow.add_node(
        "analyze_payment",
        analyze_payment_node,
    )

    workflow.add_node(
        "check_policy",
        check_policy_node,
    )

    workflow.add_node(
        "execute_recovery",
        execute_recovery_node,
    )

    workflow.add_node(
        "handle_failure",
        handle_failure_node,
    )

    workflow.add_node(
        "finalize_case",
        finalize_case_node,
    )

    # ========================================================
    # REPORTING NODE
    # ========================================================

    workflow.add_node(
        "generate_report",
        generate_report_node,
    )

    # ========================================================
    # PLANNING FLOW
    # ========================================================

    workflow.add_edge(
        START,
        "create_plan",
    )

    workflow.add_edge(
        "create_plan",
        "validate_plan",
    )

    workflow.add_conditional_edges(
        "validate_plan",
        route_after_plan_validation,
        {
            "load_payments": "load_payments",
            "repair_plan": "repair_plan",
            "plan_failure": "plan_failure",
        },
    )

    # A repaired plan must always be validated again.
    workflow.add_edge(
        "repair_plan",
        "validate_plan",
    )

    # A plan that remains invalid after repair stops safely.
    workflow.add_edge(
        "plan_failure",
        END,
    )

    # ========================================================
    # BATCH PROCESSING FLOW
    # ========================================================

    workflow.add_edge(
        "load_payments",
        "select_payment",
    )

    workflow.add_edge(
        "select_payment",
        "analyze_payment",
    )

    workflow.add_edge(
        "analyze_payment",
        "check_policy",
    )

    # ========================================================
    # POLICY ROUTING
    # ========================================================

    workflow.add_conditional_edges(
        "check_policy",
        route_after_policy,
        {
            "execute_recovery": "execute_recovery",
            "finalize_case": "finalize_case",
        },
    )

    # ========================================================
    # EXECUTION ROUTING
    # ========================================================

    workflow.add_conditional_edges(
        "execute_recovery",
        route_after_execution,
        {
            "finalize_case": "finalize_case",
            "handle_failure": "handle_failure",
        },
    )

    # ========================================================
    # FAILURE / REPLANNING LOOP
    # ========================================================

    workflow.add_conditional_edges(
        "handle_failure",
        route_after_failure,
        {
            "analyze_payment": "analyze_payment",
            "finalize_case": "finalize_case",
        },
    )

    # ========================================================
    # NEXT CASE OR FINAL REPORT
    # ========================================================

    workflow.add_conditional_edges(
        "finalize_case",
        route_after_case,
        {
            "select_payment": "select_payment",
            "generate_report": "generate_report",
        },
    )

    # ========================================================
    # WORKFLOW COMPLETION
    # ========================================================

    workflow.add_edge(
        "generate_report",
        END,
    )

    return workflow.compile()


# Compile once so other modules can import and invoke the agent.
revenue_ops_graph = build_workflow()