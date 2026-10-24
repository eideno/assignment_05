"""
payroll_report_app.py — the quarter at a glance, for someone who never opens a terminal.

Every Friday since September the office manager at Salt City Coffee has downloaded
a payroll export from the Assignment 04 app; before that she typed the same file
by hand. The owner now wants to know where the hours went this quarter, the
accountant wants pay by month and department, and the manager wants to see who
has been missing shifts. This page answers all three from the pile of exports.

Same shape as Assignment 04: the page *assembles* the pipeline — one call to
`build_history` does the cleaning — and then shows the reports, filtered by the
department and dates the user picks.

Run it:  Run and Debug -> "Streamlit Run: Current File"
Test it: pytest tests/test_pipeline.py -k app
"""
import streamlit as st

from payroll import (
    build_history,
    hours_grid,
    load_employees,
    load_export,
    missed_weeks,
    pay_by_month,
    summarize_employees,
)

st.title("Salt City Coffee — Quarterly Payroll Report")
st.write(
    "Upload the weekly payroll exports for the quarter, then filter by "
    "department and pay dates."
)

roster = load_employees()
uploads = st.file_uploader(
    "Weekly payroll exports",
    type=["csv"],
    accept_multiple_files=True,
    key="exports",
)

if uploads:
    history = build_history([load_export(u) for u in uploads], roster)

    unmatched = history[history["department"].isna()]
    if len(unmatched) > 0:
        ids = ", ".join(sorted(unmatched["employeeid"].unique()))
        st.warning(
            f"These employee IDs are not on the roster and are left out: {ids}"
        )
        history = history[history["department"].notna()]

    departments = sorted(history["department"].unique())
    department = st.selectbox("Department", ["All"] + departments, key="department")

    first = history["pay_date"].min().date()
    last = history["pay_date"].max().date()
    dates = st.date_input(
        "Pay dates",
        value=(first, last),
        min_value=first,
        max_value=last,
        key="dates",
    )
    start, end = dates if len(dates) == 2 else (dates[0], dates[0])

    pay_days = history["pay_date"].dt.date
    in_range = (pay_days >= start) & (pay_days <= end)
    if department == "All":
        selected = history[in_range]
    else:
        selected = history[in_range & (history["department"] == department)]

    st.subheader(f"{department} departments, {start} to {end}"
                 if department == "All"
                 else f"{department}, {start} to {end}")

    if selected.empty:
        st.info("No payroll rows match these filters.")
    else:
        weeks, people, hours, pay = st.columns(4)
        weeks.metric("Weeks", int(selected["week_ending"].nunique()))
        people.metric("Employees", int(selected["employee_id"].nunique()))
        hours.metric("Total hours", f"{selected['hours_worked'].sum():,.2f}")
        pay.metric("Total gross pay", f"${selected['gross_pay'].sum():,.2f}")

        monthly = pay_by_month(selected)
        st.bar_chart(monthly, x="month")

        st.dataframe(summarize_employees(selected))

        grid = hours_grid(selected)
        st.dataframe(grid)
        st.dataframe(missed_weeks(grid))

        st.download_button(
            "Download pay by month (CSV)",
            data=monthly.to_csv(index=False),
            file_name="pay_by_month.csv",
            mime="text/csv",
            key="download",
        )
