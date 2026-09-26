from models.agent_models import (
    PolicyDecision,
    RecoveryDecision,
)

from graph.nodes import (
    load_payments_node,
    select_payment_node,
    execute_recovery_node,
    handle_failure_node,
    can_replan,
)

from graph.workflow import route_after_failure


def build_pay004_state():
    """
    Create a controlled PAY-004 state with the deliberate
    retry failure configured for the demo scenario.
    """

    state = {
        "execution_trace": [],
        "fault_injections": {
            "PAY-004": "retry",
        },
    }

    state.update(load_payments_node(state))

    state["current_payment_index"] = 3
    state.update(select_payment_node(state))

    return state


def test_injected_failure_becomes_agent_evidence():
    state = build_pay004_state()

    state["recovery_decision"] = RecoveryDecision(
        diagnosis="Temporary gateway failure",
        risk_level="low",
        recommended_action="retry",
        reason="Retry transient failure",
        confidence=0.9,
    )

    state["policy_decision"] = PolicyDecision(
        allowed=True,
        reason="Approved",
    )

    state.update(execute_recovery_node(state))

    assert state["recovery_result"].success is False
    assert state["recovery_result"].failure_type == "injected_failure"

    state.update(handle_failure_node(state))

    assert state["failure_count"] == 1
    assert len(state["current_payment"].recovery_history) == 1

    attempt = state["current_payment"].recovery_history[0]

    assert attempt.action == "retry"
    assert attempt.result == "injected_failure"

    assert can_replan(state) is True
    assert route_after_failure(state) == "analyze_payment"


def test_failure_budget_prevents_infinite_recovery_loop():
    state = build_pay004_state()

    # First failed strategy
    state["recovery_decision"] = RecoveryDecision(
        diagnosis="Temporary gateway failure",
        risk_level="low",
        recommended_action="retry",
        reason="Retry transient failure",
        confidence=0.9,
    )

    state["policy_decision"] = PolicyDecision(
        allowed=True,
        reason="Approved",
    )

    state.update(execute_recovery_node(state))
    state.update(handle_failure_node(state))

    assert state["failure_count"] == 1
    assert can_replan(state) is True

    # Simulate the agent's revised strategy.
    state["recovery_decision"] = RecoveryDecision(
        diagnosis="Retry failed",
        risk_level="medium",
        recommended_action="request_alternate_payment",
        reason="Use a different recovery strategy",
        confidence=0.8,
    )

    state["policy_decision"] = PolicyDecision(
        allowed=True,
        reason="Approved",
    )

    state.update(execute_recovery_node(state))

    # PAY-004's deterministic simulator naturally fails
    # this second strategy.
    assert state["recovery_result"].success is False

    state.update(handle_failure_node(state))

    assert state["failure_count"] == 2
    assert can_replan(state) is False
    assert route_after_failure(state) == "finalize_case"

    history = state["current_payment"].recovery_history

    assert len(history) == 2
    assert history[0].action == "retry"
    assert history[0].result == "injected_failure"
    assert history[1].action == "request_alternate_payment"