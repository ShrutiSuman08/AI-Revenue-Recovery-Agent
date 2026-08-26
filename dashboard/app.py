import requests
import streamlit as st
import pandas as pd


API_URL = "http://127.0.0.1:5000"


# -----------------------------------------
# PAGE CONFIG
# -----------------------------------------

st.set_page_config(
    page_title="Revenue Recovery",
    layout="wide"
)


# -----------------------------------------
# CUSTOM STYLING
# -----------------------------------------

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .page-title {
        font-size: 30px;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .page-subtitle {
        color: #6b7280;
        font-size: 14px;
        margin-bottom: 30px;
    }

    .metric-label {
        color: #6b7280;
        font-size: 13px;
        margin-bottom: 6px;
    }

    .metric-value {
        font-size: 25px;
        font-weight: 600;
    }

    .section-title {
        font-size: 20px;
        font-weight: 600;
        margin-top: 35px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------------------
# HEADER
# -----------------------------------------

st.markdown(
    '<div class="page-title">Revenue Recovery</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-subtitle">'
    'Failed payment recovery operations'
    '</div>',
    unsafe_allow_html=True
)


# -----------------------------------------
# FETCH SUMMARY
# -----------------------------------------

try:

    response = requests.get(
        f"{API_URL}/api/summary",
        timeout=5
    )

    response.raise_for_status()

    summary = response.json()

except requests.exceptions.RequestException:

    st.error(
        "Unable to connect to the recovery service."
    )

    st.stop()


# -----------------------------------------
# KPI SECTION
# -----------------------------------------

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.markdown(
        '<div class="metric-label">Revenue at risk</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="metric-value">'
        f'₹{summary["revenue_at_risk"]:,.2f}'
        f'</div>',
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        '<div class="metric-label">Revenue recovered</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="metric-value">'
        f'₹{summary["revenue_recovered"]:,.2f}'
        f'</div>',
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        '<div class="metric-label">Recovery rate</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="metric-value">'
        f'{summary["recovery_rate"]:.2f}%'
        f'</div>',
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        '<div class="metric-label">Successful recoveries</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="metric-value">'
        f'{summary["successful_recoveries"]}'
        f'</div>',
        unsafe_allow_html=True
    )


# -----------------------------------------
# RECOVERY OVERVIEW
# -----------------------------------------

st.markdown(
    '<div class="section-title">Recovery overview</div>',
    unsafe_allow_html=True
)

st.write(
    f'{summary["payments_analyzed"]} failed payments '
    'currently under evaluation.'
)

# -----------------------------------------
# RUN RECOVERY
# -----------------------------------------

st.markdown(
    '<div class="section-title">Recovery control</div>',
    unsafe_allow_html=True
)

st.write(
    "Run the recovery workflow for the failed payments currently under evaluation."
)

run_recovery = st.button(
    "Run Batch recovery",
    type="primary"
)

if run_recovery:

    try:

        with st.spinner("Running recovery workflow..."):

            response = requests.post(
                f"{API_URL}/api/run-recovery",
                timeout=30
            )

        response.raise_for_status()

        result = response.json()

        if result.get("success"):

            recovery_result = result["result"]

            st.success(
                "Recovery workflow completed successfully."
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "Payments processed",
                    recovery_result["payments_analyzed"]
                )

            with col2:

                st.metric(
                    "Revenue recovered",
                    f'₹{recovery_result["revenue_recovered"]:,.2f}'
                )

            with col3:

                st.metric(
                    "Recovery rate",
                    f'{recovery_result["recovery_rate"]:.2f}%'
                )

            with col4:

                st.metric(
                    "Successful recoveries",
                    recovery_result["successful_recoveries"]
                )
            st.rerun()    

        else:

            st.error(
                result.get(
                    "error",
                    "Recovery workflow failed."
                )
            )

    except requests.exceptions.RequestException as e:

        st.error(
            f"Unable to connect to the recovery service: {e}"
        )
# -----------------------------------------
# RAZORPAY IMPORT
# -----------------------------------------

st.markdown(
    '<div class="section-title">Import Razorpay payment</div>',
    unsafe_allow_html=True
)

st.write(
    "Import a failed Razorpay Test Mode payment "
    "using its payment ID."
)

razorpay_payment_id = st.text_input(
    "Razorpay Payment ID",
    placeholder="pay_XXXXXXXXXXXX"
)

import_payment = st.button(
    "Import Razorpay payment"
)

if import_payment:

    if not razorpay_payment_id.strip():

        st.warning(
            "Enter a Razorpay payment ID."
        )

    else:

        try:

            response = requests.post(
                f"{API_URL}/api/import-razorpay-payment",
                json={
                    "payment_id": razorpay_payment_id.strip()
                },
                timeout=10
            )

            response.raise_for_status()

            result = response.json()

            if result.get("success"):

                payment = result["payment"]

                st.success(
                    "Razorpay payment imported successfully."
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Amount",
                        f'₹{payment["amount"]:,.2f}'
                    )

                with col2:
                    st.metric(
                        "Method",
                        payment["payment_method"].upper()
                    )

                with col3:
                    st.metric(
                        "Status",
                        payment["status"].title()
                    )

                st.info(
                    payment["failure_reason"]

                )
                st.rerun()

            else:

                st.error(
                    result.get(
                        "error",
                        "Unable to import payment."
                    )
                )

        except requests.exceptions.RequestException as e:

            st.error(
                f"Unable to connect to the recovery service: {e}"
            )

# -----------------------------------------
# FETCH FAILED PAYMENTS
# -----------------------------------------

try:

    response = requests.get(
        f"{API_URL}/api/payments",
        timeout=5
    )

    response.raise_for_status()

    payments = response.json()

except requests.exceptions.RequestException:

    st.error(
        "Unable to load failed payments."
    )

    st.stop()


# -----------------------------------------
# FAILED PAYMENTS
# -----------------------------------------

st.markdown(
    '<div class="section-title">Failed payments</div>',
    unsafe_allow_html=True
)


payment_rows = []

for payment in payments:

    recovery = payment.get("recovery")

    if recovery:

        recovery_status = recovery["status"]
        risk_level = recovery["risk_level"]
        action = recovery["recommended_action"]

    else:

        recovery_status = "not_evaluated"
        risk_level = "-"
        action = "-"

    payment_rows.append({
        "Payment": payment["payment_id"],

        "Source": (
            "Razorpay"
            if payment["payment_id"].startswith("pay_")
            else "Synthetic"
        ),

        "Amount": f'₹{payment["amount"]:,.2f}',

        "Method": payment["payment_method"].upper(),

        "Failure": payment["failure_reason"].replace(
            "_", " "
        ).title(),

        "Attempts": payment["attempt_count"],

        "Risk": risk_level.title(),

        "Action": action.replace(
            "_", " "
        ).title(),

        "Status": (
            "Recovered"
            if recovery_status == "recovered"
            else "Blocked"
            if recovery_status == "blocked"
            else "Manual Review"
            if recovery_status == "manual_review"
            else "Failed"
        )
    })


payment_df = pd.DataFrame(payment_rows)


def style_payment_cell(value):

    if value == "Recovered":
        return "color: #15803d; font-weight: 600;"

    elif value == "Blocked":
        return "color: #b45309; font-weight: 600;"

    elif value == "Failed":
        return "color: #b91c1c; font-weight: 600;"

    elif value == "Low":
        return "color: #15803d; font-weight: 600;"

    elif value == "Medium":
        return "color: #b45309; font-weight: 600;"

    elif value == "High":
        return "color: #b91c1c; font-weight: 600;"

    elif value == "Manual Review":
        return "color: #7c3aed; font-weight: 600;"
    elif value == "Razorpay":
     return "font-weight: 600;"

    elif value == "Synthetic":
      return "color: #6b7280;"

    return ""


styled_payment_df = payment_df.style.map(
    style_payment_cell,
    subset=["Status", "Risk","Source"]
)


st.dataframe(
    styled_payment_df,
    use_container_width=True,
    hide_index=True
)


# -----------------------------------------
# FETCH RECOVERY ATTEMPTS
# -----------------------------------------

try:

    response = requests.get(
        f"{API_URL}/api/recovery-attempts",
        timeout=5
    )

    response.raise_for_status()

    recovery_attempts = response.json()

except requests.exceptions.RequestException:

    st.error(
        "Unable to load recovery activity."
    )

    st.stop()


# -----------------------------------------
# RECOVERY ACTIVITY
# -----------------------------------------

st.markdown(
    '<div class="section-title">Recovery activity</div>',
    unsafe_allow_html=True
)


activity_rows = []

for attempt in recovery_attempts:

    activity_rows.append({
        "Case": f'#{attempt["case_id"]}',
        "Action": attempt["action"].replace(
            "_", " "
        ).title(),
        "Result": (
            "Recovered"
            if attempt["result"] == "success"
            else "Blocked"
            if attempt["result"] == "blocked"
            else "Failed"
        ),
        "Amount Recovered": (
            f'₹{attempt["amount_recovered"]:,.2f}'
        ),
        "Time": attempt["timestamp"].replace(
            "T", " "
        )[:19]
    })


activity_df = pd.DataFrame(activity_rows)


def style_result(value):

    if value == "Recovered":
        return "color: #15803d; font-weight: 600;"

    elif value == "Blocked":
        return "color: #b45309; font-weight: 600;"

    elif value == "Failed":
        return "color: #b91c1c; font-weight: 600;"

    elif value == "Manual Review":
        return "color: #7c3aed; font-weight: 600;"

    return ""


styled_activity_df = activity_df.style.map(
    style_result,
    subset=["Result"]
)


st.dataframe(
    styled_activity_df,
    use_container_width=True,
    hide_index=True
)


# -----------------------------------------
# RECOVERY PERFORMANCE
# -----------------------------------------

st.markdown(
    '<div class="section-title">Recovery performance</div>',
    unsafe_allow_html=True
)


successful_count = sum(
    1
    for attempt in recovery_attempts
    if attempt["result"] == "success"
)

failed_count = sum(
    1
    for attempt in recovery_attempts
    if attempt["result"] == "failed"
)

blocked_count = sum(
    1
    for attempt in recovery_attempts
    if attempt["result"] == "blocked"
)


performance_data = {
    "Result": [
        "Recovered",
        "Failed",
        "Blocked"
    ],
    "Payments": [
        successful_count,
        failed_count,
        blocked_count
    ]
}


st.bar_chart(
    performance_data,
    x="Result",
    y="Payments"
)


# -----------------------------------------
# PAYMENT DETAILS
# -----------------------------------------

st.markdown(
    '<div class="section-title">Payment details</div>',
    unsafe_allow_html=True
)


payment_ids = [
    payment["payment_id"]
    for payment in payments
]


selected_payment_id = st.selectbox(
    "Select payment",
    payment_ids
)
# -----------------------------------------
# RECOVER SELECTED PAYMENT
# -----------------------------------------

recover_selected = st.button(
    "Run AI Recovery",
    type="primary"
)

if recover_selected:

    try:

        with st.spinner(
            f"AI agent is analyzing {selected_payment_id}..."
        ):

            response = requests.post(
                f"{API_URL}/api/recover-payment",
                json={
                    "payment_id": selected_payment_id
                },
                timeout=30
            )

        result = response.json()

        if response.ok and result.get("success"):

            # Save result before refreshing
            st.session_state["last_recovery_result"] = (
                result["result"]
            )

            st.rerun()

        else:

            st.error(
                result.get(
                    "error",
                    "Recovery failed."
                )
            )

    except requests.exceptions.RequestException as e:

        st.error(
            f"Unable to connect to recovery service: {e}"
        )


# -----------------------------------------
# DISPLAY LAST RECOVERY RESULT
# -----------------------------------------

if "last_recovery_result" in st.session_state:

    recovery_result = st.session_state[
        "last_recovery_result"
    ]

    st.markdown("### Latest AI recovery result")

    status = recovery_result["status"]

    if status == "recovered":

        st.success(
            f'Payment recovered successfully — '
            f'₹{recovery_result["recovered_amount"]:,.2f}'
        )

    elif status == "blocked":

        st.warning(
            "Recovery was blocked by policy."
        )

    elif status == "manual_review":

        st.info(
            "Payment was escalated for manual review."
        )

    else:

        st.error(
            "Recovery attempt was unsuccessful."
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Action",
            recovery_result["action"]
            .replace("_", " ")
            .title()
        )

    with col2:
        st.metric(
            "Confidence",
            f'{recovery_result["confidence"] * 100:.0f}%'
        )

    with col3:
        st.metric(
            "Recovered",
            f'₹{recovery_result["recovered_amount"]:,.2f}'
        )

    st.markdown("**Diagnosis**")
    st.write(
        recovery_result["diagnosis"]
    )

    st.markdown("**Reason**")
    st.write(
        recovery_result["reason"]
    )


selected_payment = next(
    payment
    for payment in payments
    if payment["payment_id"] == selected_payment_id
)


recovery = selected_payment.get("recovery")


if recovery:

    st.markdown("### Payment information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("Payment ID")
        st.write(selected_payment["payment_id"])

    with col2:
        st.caption("Amount")
        st.write(
            f'₹{selected_payment["amount"]:,.2f}'
        )

    with col3:
        st.caption("Payment method")
        st.write(
            selected_payment["payment_method"].upper()
        )


    st.markdown("### Failure analysis")

    col1, col2 = st.columns(2)

    with col1:

        st.caption("Failure reason")

        st.write(
            selected_payment["failure_reason"]
            .replace("_", " ")
            .title()
        )

    with col2:

        st.caption("Previous attempts")

        st.write(
            selected_payment["attempt_count"]
        )


    st.markdown("### AI recovery decision")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.caption("Risk level")

        risk = recovery["risk_level"].title()

        if risk == "Low":
            st.success(risk)

        elif risk == "Medium":
            st.warning(risk)

        else:
            st.error(risk)

    with col2:

        st.caption("Confidence")

        st.write(
            f'{recovery["confidence"] * 100:.0f}%'
        )

    with col3:

        st.caption("Recommended action")

        st.write(
            recovery["recommended_action"]
            .replace("_", " ")
            .title()
        )


    st.markdown("### Diagnosis")

    st.info(
        recovery["diagnosis"]
    )


    st.markdown("### Recovery outcome")

    status = recovery["status"].lower()

    if status == "recovered":

        st.success(
            "Payment successfully recovered."
        )

    elif status == "blocked":

        st.warning(
            "Automatic recovery was blocked by policy."
        )
    elif status == "manual_review":
     st.info(
        "Automatic recovery has stopped. "
        "This payment requires manual review."
    )    

    else:

        st.error(
            "Recovery attempt was unsuccessful."
        )

else:

    st.info(
        "No recovery decision is available for this payment."
    )


# -----------------------------------------
# AGENT DECISION
# -----------------------------------------

st.markdown(
    '<div class="section-title">Agent decision</div>',
    unsafe_allow_html=True
)


if recovery:

    decision_col1, decision_col2 = st.columns([1, 2])

    with decision_col1:

        st.markdown("**Decision**")

        action = recovery["recommended_action"].replace(
            "_", " "
        ).title()

        if recovery["status"].lower() == "recovered":

            st.success(action)

        elif recovery["status"].lower() == "blocked":

            st.warning(action)

        else:

            st.error(action)


        st.markdown("**Risk**")

        risk = recovery["risk_level"].lower()

        if risk == "low":
            st.success("Low")

        elif risk == "medium":
            st.warning("Medium")

        else:
            st.error("High")


        st.markdown("**Confidence**")

        st.progress(
            recovery["confidence"],
            text=f'{recovery["confidence"] * 100:.0f}% confidence'
        )


    with decision_col2:

        st.markdown("**Why this decision was made**")

        st.write(
            recovery["diagnosis"]
        )

        st.markdown("**Recovery policy outcome**")

        status = recovery["status"].lower()

        if status == "recovered":

            st.success(
                "The recovery action was permitted and successfully recovered the payment."
            )

        elif status == "blocked":

            st.warning(
                "The AI recommended an action, but the policy engine prevented automatic recovery."
            )
        
        elif status == "manual_review":

         st.info(
        "Automatic recovery has stopped and the case was escalated for manual review."
    )
        else:

            st.error(
                "The recommended recovery action was attempted but did not recover the payment."
            )

else:

    st.info(
        "Agent decision is not available for this payment."
    )


# -----------------------------------------
# FETCH AUDIT LOGS
# -----------------------------------------

try:

    response = requests.get(
        f"{API_URL}/api/audit-logs",
        timeout=5
    )

    response.raise_for_status()

    audit_logs = response.json()

except requests.exceptions.RequestException:

    st.error(
        "Unable to load audit logs."
    )

    st.stop()


# -----------------------------------------
# AUDIT TRAIL
# -----------------------------------------

st.markdown(
    '<div class="section-title">Audit trail</div>',
    unsafe_allow_html=True
)


audit_rows = []

for log in audit_logs:

    audit_rows.append({
        "Case": f'#{log["case_id"]}',
        "Event": log["event"].replace(
            "_", " "
        ).title(),
        "Action": log["action"].replace(
            "_", " "
        ).title(),
        "Result": (
            "Recovered"
            if log["result"] == "success"
            else "Blocked"
            if log["result"] == "blocked"
            else "Failed"
        ),
        "Reason": log["reason"],
        "Time": log["timestamp"].replace(
            "T", " "
        )[:19]
    })


audit_df = pd.DataFrame(audit_rows)


styled_audit_df = audit_df.style.map(
    style_result,
    subset=["Result"]
)


st.dataframe(
    styled_audit_df,
    use_container_width=True,
    hide_index=True
)


