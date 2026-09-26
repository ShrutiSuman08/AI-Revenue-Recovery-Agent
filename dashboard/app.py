from pathlib import Path
import sys

import streamlit as st


# --------------------------------------------------
# PROJECT IMPORTS
# --------------------------------------------------

# Allows:
#   streamlit run dashboard/app.py
# from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from graph.workflow import revenue_ops_graph


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="RevenueOps Agent",
    page_icon="⚙️",
    layout="wide",
)


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

DEFAULT_GOAL = (
    "Analyze today's failed payments, recover eligible revenue while "
    "respecting company recovery policies, handle unsuccessful recovery "
    "attempts safely, and produce an auditable recovery report."
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("RevenueOps Agent")

st.caption(
    "Autonomous Revenue Recovery Operations Agent"
)

st.info(
    "Evaluation Mode — Uses synthetic payment scenarios with "
    "deterministic fault injection."
)


# --------------------------------------------------
# GOAL INPUT
# --------------------------------------------------

st.subheader("Recovery Goal")

goal = st.text_area(
    "Describe the revenue recovery objective",
    value=DEFAULT_GOAL,
    height=120,
)


# --------------------------------------------------
# RUN AGENT
# --------------------------------------------------

run_agent = st.button(
    "Run Autonomous Recovery",
    type="primary",
)


if run_agent:

    if not goal.strip():
        st.warning("Enter a recovery goal before running the agent.")
        st.stop()

    initial_state = {
        "goal": goal.strip(),
        "execution_trace": [],

        # Explicit deterministic fault injection used only
        # for the evaluation scenario.
        "fault_injections": {
            "PAY-004": "retry"
        },
    }

    try:

        with st.spinner(
            "RevenueOps Agent is planning and executing the recovery workflow..."
        ):
            result = revenue_ops_graph.invoke(initial_state)

        st.session_state["agent_result"] = result

        st.success(
            "Autonomous recovery workflow completed."
        )

    except Exception as exc:

        st.error(
            f"Agent execution failed: {exc}"
        )


# --------------------------------------------------
# TEMPORARY VERIFICATION
# --------------------------------------------------

if "agent_result" in st.session_state:

    result = st.session_state["agent_result"]

    st.divider()

    st.subheader("Execution Complete")

    st.write(
        "The LangGraph workflow returned successfully."
    )

    st.write(
        "Execution events:",
        len(result.get("execution_trace", [])),
    )

    if result.get("final_report"):
        st.write("Final report generated successfully.")

# --------------------------------------------------
# GENERATED PLAN
# --------------------------------------------------

if "agent_result" in st.session_state:

    result = st.session_state["agent_result"]
    plan = result.get("plan")

    if plan:

        st.divider()
        st.subheader("1. Generated Plan")

        st.caption(
            "The plan was generated before recovery actions were executed."
        )

        for index, step in enumerate(plan.steps, start=1):

            status = step.status.value

            if status == "completed":
                icon = "✅"
            elif status == "running":
                icon = "🔄"
            elif status == "failed":
                icon = "❌"
            elif status == "skipped":
                icon = "⏭️"
            else:
                icon = "⏳"

            st.markdown(
                f"**{icon} {index}. {step.objective}**"
            )

            st.caption(step.rationale)      


# --------------------------------------------------
# RECOVERY SUMMARY
# --------------------------------------------------

if "agent_result" in st.session_state:

    result = st.session_state["agent_result"]
    final_report = result.get("final_report")

    if final_report:

        summary = final_report.get("summary", {})

        st.divider()
        st.subheader("2. Recovery Summary")

        st.caption(
            "Aggregate outcome of the autonomous recovery workflow."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Payments Processed",
                summary.get("total_payments", 0),
            )

        with col2:
            st.metric(
                "Revenue at Risk",
                f'₹{summary.get("total_revenue_at_risk", 0):,.2f}',
            )

        with col3:
            st.metric(
                "Revenue Recovered",
                f'₹{summary.get("recovered_revenue", 0):,.2f}',
            )

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric(
                "Recovered Payments",
                summary.get("recovered_payments", 0),
            )

        with col5:
            st.metric(
                "Policy Blocked",
                summary.get("policy_blocked_payments", 0),
            )

        with col6:
            st.metric(
                "Failed Recovery Attempts",
                summary.get("failed_recovery_attempts", 0),
            )

        st.metric(
            "Manual Review",
            summary.get("manual_review_payments", 0),
        )   


# --------------------------------------------------
# CASE RESULTS
# --------------------------------------------------

if "agent_result" in st.session_state:

    result = st.session_state["agent_result"]
    final_report = result.get("final_report")

    if final_report:

        cases = final_report.get("cases", [])

        if cases:

            st.divider()
            st.subheader("3. Payment Case Results")

            st.caption(
                "Final outcome for each payment processed by the agent."
            )

            case_rows = []

            for case in cases:

                status = case.get("status", "unknown")

                status_label = {
                    "recovered": "Recovered",
                    "policy_blocked": "Policy Blocked",
                    "manual_review": "Manual Review",
                    "failed": "Failed",
                }.get(
                    status,
                    status.replace("_", " ").title(),
                )

                action = case.get("final_action")

                action_label = (
                    action.replace("_", " ").title()
                    if action
                    else "-"
                )

                case_rows.append(
                    {
                        "Payment": case.get("payment_id", "-"),
                        "Amount": f'₹{case.get("amount", 0):,.2f}',
                        "Status": status_label,
                        "Final Action": action_label,
                        "Recovered": (
                            f'₹{case.get("recovered_amount", 0):,.2f}'
                        ),
                        "Failures": case.get("failure_count", 0),
                    }
                )

            st.dataframe(
                case_rows,
                use_container_width=True,
                hide_index=True,
            )           

# --------------------------------------------------
# EXECUTION TRACE
# --------------------------------------------------

if "agent_result" in st.session_state:

    result = st.session_state["agent_result"]
    execution_trace = result.get("execution_trace", [])

    if execution_trace:

        st.divider()
        st.subheader("4. Agent Execution Trace")

        st.caption(
            "Chronological evidence of planning, policy validation, "
            "tool execution, failure detection, and recovery."
        )

        # ------------------------------------------
        # PAY-004 FAILURE RECOVERY STORY
        # ------------------------------------------

        pay004_events = [
            event
            for event in execution_trace
            if event.get("details", {}).get("payment_id") == "PAY-004"
        ]

        if pay004_events:

            st.markdown("### PAY-004 — Deliberate Failure & Recovery")

            st.info(
                "Evaluation mode deliberately fails the first retry for "
                "PAY-004. The agent must observe that failure, update its "
                "evidence, and choose a safe next step."
            )

            step_number = 1

            for trace_event in pay004_events:

                event_name = trace_event.get(
                    "event",
                    "unknown_event",
                )

                details = trace_event.get("details", {})

                # ----------------------------------
                # PAYMENT SELECTED
                # ----------------------------------

                if event_name == "payment_selected":

                    st.markdown(
                        f"**{step_number}. Payment selected for investigation**"
                    )

                    step_number += 1

                # ----------------------------------
                # AGENT RECOMMENDATION
                # ----------------------------------

                elif event_name == "recovery_recommended":

                    action = details.get(
                        "recommended_action",
                        "unknown",
                    )

                    failure_count = details.get(
                        "failure_count",
                        0,
                    )

                    if failure_count == 0:

                        st.markdown(
                            f"**{step_number}. Agent recommended "
                            f"`{action}`**"
                        )

                    else:

                        st.markdown(
                            f"**{step_number}. 🔄 Agent replanned and "
                            f"recommended `{action}`**"
                        )

                    st.caption(
                        f'Risk: {details.get("risk_level", "-")} | '
                        f'Confidence: '
                        f'{details.get("confidence", 0) * 100:.0f}% | '
                        f'Previous failures: {failure_count}'
                    )

                    step_number += 1

                # ----------------------------------
                # POLICY APPROVAL
                # ----------------------------------

                elif event_name == "policy_approved":

                    action = details.get(
                        "proposed_action",
                        "unknown",
                    )

                    st.success(
                        f"{step_number}. Policy approved `{action}`"
                    )

                    st.caption(
                        details.get(
                            "reason",
                            "Recovery action passed policy validation.",
                        )
                    )

                    step_number += 1

                # ----------------------------------
                # POLICY BLOCK
                # ----------------------------------

                elif event_name == "policy_blocked":

                    st.warning(
                        f"{step_number}. Policy blocked automatic recovery"
                    )

                    st.caption(
                        details.get(
                            "reason",
                            "Policy restriction.",
                        )
                    )

                    step_number += 1

                # ----------------------------------
                # RECOVERY FAILURE
                # ----------------------------------

                elif event_name == "recovery_failed":

                    action = details.get(
                        "action",
                        "unknown",
                    )

                    failure_type = details.get(
                        "failure_type",
                        "unknown",
                    )

                    if details.get("failure_injected"):

                        st.error(
                            f"{step_number}. Recovery tool failed — "
                            f"`{action}`"
                        )

                        st.caption(
                            "Deliberately injected evaluation failure "
                            f"({failure_type})."
                        )

                    else:

                        st.error(
                            f"{step_number}. Recovery tool failed — "
                            f"`{action}`"
                        )

                        st.caption(
                            f"Observed tool result: {failure_type}."
                        )

                    step_number += 1

                # ----------------------------------
                # FAILURE BECOMES EVIDENCE
                # ----------------------------------

                elif event_name == "recovery_failure_recorded":

                    st.markdown(
                        f"**{step_number}. Failure recorded as new evidence**"
                    )

                    st.caption(
                        f'Failed action: '
                        f'{details.get("failed_action", "-")} | '
                        f'Failure count: '
                        f'{details.get("failure_count", 0)}'
                    )

                    step_number += 1

                # ----------------------------------
                # RECOVERY SUCCESS
                # ----------------------------------

                elif event_name == "recovery_succeeded":

                    st.success(
                        f"{step_number}. Recovery succeeded — "
                        f'₹{details.get("recovered_amount", 0):,.2f}'
                    )

                    st.caption(
                        f'Action: {details.get("action", "-")}'
                    )

                    step_number += 1

                # ----------------------------------
                # FINAL CASE OUTCOME
                # ----------------------------------

                elif event_name == "case_finalized":

                    status = details.get(
                        "status",
                        "unknown",
                    )

                    if status == "recovered":

                        st.success(
                            f"{step_number}. Final outcome — Recovered"
                        )

                    elif status == "manual_review":

                        st.warning(
                            f"{step_number}. Final outcome — Manual Review"
                        )

                    elif status == "policy_blocked":

                        st.warning(
                            f"{step_number}. Final outcome — Policy Blocked"
                        )

                    else:

                        st.write(
                            f"**{step_number}. Final outcome — "
                            f"{status.replace('_', ' ').title()}**"
                        )

                    st.caption(
                        details.get(
                            "reason",
                            "Case finalized.",
                        )
                    )

                    step_number += 1

        else:

            st.warning(
                "PAY-004 trace was not found in this execution."
            )

        # ------------------------------------------
        # RAW TECHNICAL TRACE
        # ------------------------------------------

        with st.expander(
            "View full technical execution trace"
        ):

            st.json(execution_trace)

# --------------------------------------------------
# STRUCTURED FINAL REPORT
# --------------------------------------------------

if "agent_result" in st.session_state:

    result = st.session_state["agent_result"]
    final_report = result.get("final_report")

    if final_report:

        st.divider()
        st.subheader("5. Structured Final Report")

        st.caption(
            "Machine-readable final output generated after the "
            "autonomous workflow completes."
        )

        with st.expander(
            "View final recovery report",
            expanded=False,
        ):
            st.json(final_report)            