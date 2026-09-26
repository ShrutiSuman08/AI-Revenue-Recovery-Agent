from models.agent_models import (
    PolicyDecision,
    RecoveryDecision,
    RecoveryResult,
)

from graph.workflow import (
    route_after_policy,
    route_after_execution,
    route_after_failure,
)


def test_policy_block_prevents_execution():
    state = {
        "recovery_decision": RecoveryDecision(
            diagnosis="High-value failed payment",
            risk_level="high",
            recommended_action="retry",
            reason="Retry may recover payment",
            confidence=0.8,
        ),
        "policy_decision": PolicyDecision(
            allowed=False,
            reason="Payment amount exceeds automatic recovery limit.",
        ),
    }

    assert route_after_policy(state) == "finalize_case"


def test_manual_review_never_reaches_execution_tool():
    state = {
        "recovery_decision": RecoveryDecision(
            diagnosis="Repeated recovery failures",
            risk_level="high",
            recommended_action="manual_review",
            reason="Human review required",
            confidence=0.9,
        ),
        "policy_decision": PolicyDecision(
            allowed=True,
            reason="Manual review is permitted.",
        ),
    }

    assert route_after_policy(state) == "finalize_case"


def test_approved_action_reaches_execution():
    state = {
        "recovery_decision": RecoveryDecision(
            diagnosis="Transient gateway failure",
            risk_level="low",
            recommended_action="retry",
            reason="Safe retry",
            confidence=0.9,
        ),
        "policy_decision": PolicyDecision(
            allowed=True,
            reason="Recovery action passed all policy checks.",
        ),
    }

    assert route_after_policy(state) == "execute_recovery"


def test_successful_execution_finalizes_case():
    state = {
        "recovery_result": RecoveryResult(
            success=True,
            action="retry",
            message="Recovered",
            recovered_amount=2500.0,
            failure_type=None,
        )
    }

    assert route_after_execution(state) == "finalize_case"


def test_failed_execution_enters_failure_handler():
    state = {
        "recovery_result": RecoveryResult(
            success=False,
            action="retry",
            message="Recovery failed",
            recovered_amount=0.0,
            failure_type="recovery_failed",
        )
    }

    assert route_after_execution(state) == "handle_failure"


def test_first_failure_allows_replanning():
    state = {
        "failure_count": 1,
    }

    assert route_after_failure(state) == "analyze_payment"


def test_failure_limit_stops_replanning():
    state = {
        "failure_count": 2,
    }

    assert route_after_failure(state) == "finalize_case"