# AI EXPENSE DASHBOARD (AUTO ANALYTICS – COMPANY READY)

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="AI Expense Dashboard", layout="wide")

# -------------------------------
# Load & Save Data
# -------------------------------
def load_data():
    try:
        df = pd.read_csv("expenses.csv", parse_dates=["Date"])
        return df
    except:
        return pd.DataFrame(columns=[
            "Date", "Category", "Amount",
            "Supervisor", "Site", "Summary"
        ])

def save_data(df):
    df.to_csv("expenses.csv", index=False)

expenses = load_data()

# -------------------------------
# Auto Column Mapping
# -------------------------------
def clean_uploaded_data(df):
    df_clean = pd.DataFrame()

    col_map = {c.lower(): c for c in df.columns}

    def find_col(names):
        for n in names:
            if n in col_map:
                return col_map[n]
        return None

    df_clean["Date"] = pd.to_datetime(
        df[find_col(["date", "day", "purchase date", "entry date"])],
        errors="coerce"
    )

    df_clean["Amount"] = pd.to_numeric(
        df[find_col(["amount", "price", "cost", "expense"])],
        errors="coerce"
    )

    df_clean["Category"] = df[find_col(["category", "type", "label"])] if find_col(["category", "type", "label"]) else "Other"
    df_clean["Supervisor"] = df[find_col(["supervisor", "manager", "incharge"])] if find_col(["supervisor", "manager", "incharge"]) else "Unknown"
    df_clean["Site"] = df[find_col(["site", "location", "project"])] if find_col(["site", "location", "project"]) else "Unknown"
    df_clean["Summary"] = df[find_col(["summary", "description", "details", "remark", "note"])] if find_col(["summary", "description", "details", "remark", "note"]) else ""

    return df_clean.dropna(subset=["Date", "Amount"])

# -------------------------------
# Sidebar Navigation
# -------------------------------
st.sidebar.title("📊 AI Expense Dashboard")
menu = st.sidebar.radio(
    "Navigation",
    ["Add Expense", "Upload Expense File", "View Dashboard", "Data Table"]
)

# -------------------------------
# ADD EXPENSE
# -------------------------------
if menu == "Add Expense":
    st.header("➕ Add New Expense")

    c1, c2, c3 = st.columns(3)

    with c1:
        date = st.date_input("Date", datetime.today())
        amount = st.number_input("Amount (₹)", min_value=0.0)

    with c2:
        category = st.selectbox("Category", ["Food", "Travel", "Fuel", "Shopping", "Bills", "Other"])
        supervisor = st.text_input("Supervisor")

    with c3:
        site = st.text_input("Site")
        summary = st.text_input("Summary")

    if st.button("Save Expense"):
        new_row = pd.DataFrame([{
            "Date": date,
            "Category": category,
            "Amount": amount,
            "Supervisor": supervisor,
            "Site": site,
            "Summary": summary
        }])
        expenses = pd.concat([expenses, new_row], ignore_index=True)
        save_data(expenses)
        st.success("Expense saved successfully ✅")
        st.rerun()

# -------------------------------
# UPLOAD FILE
# -------------------------------
if menu == "Upload Expense File":
    st.header("📤 Upload Expense File")

    uploaded_file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df_upload = pd.read_csv(uploaded_file)
        else:
            df_upload = pd.read_excel(uploaded_file)

        cleaned_df = clean_uploaded_data(df_upload)

        st.subheader("Cleaned Data Preview")
        st.dataframe(cleaned_df)

        if st.button("Add to Dashboard"):
            expenses = pd.concat([expenses, cleaned_df], ignore_index=True)
            save_data(expenses)
            st.success("File imported successfully 🎉")
            st.rerun()

# -------------------------------
# VIEW DASHBOARD (AUTO)
# -------------------------------
if menu == "View Dashboard":
    st.header("📈 Expense Analytics")

    if expenses.empty:
        st.warning("No data available")
        st.stop()

    # -------- FILTERS --------
    st.subheader("🔍 Filters")

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        start_date = st.date_input("Start Date", expenses["Date"].min())

    with f2:
        end_date = st.date_input("End Date", expenses["Date"].max())

    with f3:
        sites = st.multiselect("Site", expenses["Site"].unique(), expenses["Site"].unique())

    with f4:
        supervisors = st.multiselect("Supervisor", expenses["Supervisor"].unique(), expenses["Supervisor"].unique())

    filtered = expenses[
        (expenses["Date"] >= pd.to_datetime(start_date)) &
        (expenses["Date"] <= pd.to_datetime(end_date)) &
        (expenses["Site"].isin(sites)) &
        (expenses["Supervisor"].isin(supervisors))
    ]

    # -------- KPIs --------
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("💰 Total Spend", f"₹ {filtered['Amount'].sum():,.2f}")
    k2.metric("📄 Records", len(filtered))
    k3.metric("🏗 Sites", filtered["Site"].nunique())
    k4.metric("👨‍💼 Supervisors", filtered["Supervisor"].nunique())

    st.divider()

    # -------- TREND --------
    trend = filtered.groupby("Date")["Amount"].sum().reset_index()
    st.plotly_chart(
        px.line(trend, x="Date", y="Amount", title="Expense Trend", markers=True),
        use_container_width=True
    )

    c1, c2 = st.columns(2)

    with c1:
        st.plotly_chart(
            px.pie(filtered, names="Category", values="Amount", title="Category-wise Spend"),
            use_container_width=True
        )

    with c2:
        site_data = filtered.groupby("Site")["Amount"].sum().reset_index()
        st.plotly_chart(
            px.bar(site_data, x="Site", y="Amount", title="Site-wise Spend"),
            use_container_width=True
        )

    # -------- SPIKE DETECTION --------
    st.subheader("🚨 Expense Alerts")

    avg = filtered["Amount"].mean()
    spikes = filtered[filtered["Amount"] > avg * 2]

    if not spikes.empty:
        st.error("High expense entries detected")
        st.dataframe(spikes)
    else:
        st.success("No abnormal expenses detected")

    st.download_button(
        "⬇ Download Report",
        data=filtered.to_csv(index=False),
        file_name="expense_report.csv"
    )

# -------------------------------
# DATA TABLE
# -------------------------------
if menu == "Data Table":
    st.header("📄 Expense Records")

    if expenses.empty:
        st.warning("No records found")
    else:
        st.dataframe(expenses, use_container_width=True)

        if st.button("Clear All Data"):
            save_data(pd.DataFrame(columns=expenses.columns))
            st.success("All data cleared")
            st.rerun()
