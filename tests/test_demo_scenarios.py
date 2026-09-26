from demo.scenarios import get_demo_payments
from tools.policy_tool import evaluate_recovery_policy
from tools.recovery_tool import execute_recovery


def get_payment(payment_id: str):
    payments = get_demo_payments()

    return next(
        payment
        for payment in payments
        if payment.payment_id == payment_id
    )


def test_demo_contains_six_distinct_payments():
    payments = get_demo_payments()

    assert len(payments) == 6

    payment_ids = {
        payment.payment_id
        for payment in payments
    }

    assert len(payment_ids) == 6


def test_total_demo_revenue_at_risk_is_30000():
    payments = get_demo_payments()

    total = sum(
        payment.amount
        for payment in payments
    )

    assert total == 30000.0


def test_high_value_payment_is_blocked_by_policy():
    payment = get_payment("PAY-003")

    decision = evaluate_recovery_policy(
        payment,
        "retry",
    )

    assert decision.allowed is False
    assert "amount" in decision.reason.lower()


def test_payment_with_exhausted_attempts_is_blocked():
    payment = get_payment("PAY-005")

    decision = evaluate_recovery_policy(
        payment,
        "request_alternate_payment",
    )

    assert decision.allowed is False
    assert "maximum" in decision.reason.lower()


def test_pay004_retry_failure_can_be_injected():
    payment = get_payment("PAY-004")

    result = execute_recovery(
        payment,
        "retry",
        inject_failure=True,
    )

    assert result.success is False
    assert result.failure_type == "injected_failure"
    assert result.recovered_amount == 0.0


def test_recovery_simulator_is_deterministic():
    payment = get_payment("PAY-001")

    first = execute_recovery(
        payment,
        "retry",
    )

    second = execute_recovery(
        payment,
        "retry",
    )

    assert first.success == second.success
    assert first.recovered_amount == second.recovered_amount
    assert first.failure_type == second.failure_type