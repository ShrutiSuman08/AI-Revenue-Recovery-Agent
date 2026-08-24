import requests
import streamlit as st


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

        recovery_status = "Not evaluated"
        risk_level = "-"
        action = "-"

    payment_rows.append({
        "Payment": payment["payment_id"],
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
        else "Failed")

          })


st.dataframe(
    payment_rows,
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


st.dataframe(
    activity_rows,
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


selected_payment = next(
    payment
    for payment in payments
    if payment["payment_id"] == selected_payment_id
)


recovery = selected_payment.get("recovery")


if recovery:

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("**Payment**")

        st.write(
            f'Payment ID: '
            f'{selected_payment["payment_id"]}'
        )

        st.write(
            f'Amount: '
            f'₹{selected_payment["amount"]:,.2f}'
        )

        st.write(
            f'Method: '
            f'{selected_payment["payment_method"].upper()}'
        )

        st.write(
            f'Failure: '
            f'{selected_payment["failure_reason"].replace("_", " ").title()}'
        )

        st.write(
            f'Previous attempts: '
            f'{selected_payment["attempt_count"]}'
        )

    with col2:

        st.markdown("**Recovery decision**")

        st.write(
            f'Risk: '
            f'{recovery["risk_level"].title()}'
        )

        st.write(
            f'Confidence: '
            f'{recovery["confidence"] * 100:.0f}%'
        )

        st.write(
            f'Action: '
            f'{recovery["recommended_action"].replace("_", " ").title()}'
        )

        st.write(
            f'Status: '
            f'{recovery["status"].title()}'
        )

    st.markdown("**Diagnosis**")

    st.write(
        recovery["diagnosis"]
    )

else:

    st.info(
        "No recovery decision is available for this payment."
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


st.dataframe(
    audit_rows,
    use_container_width=True,
    hide_index=True
)