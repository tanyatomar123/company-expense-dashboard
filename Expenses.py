# AI EXPENSE DASHBOARD (WITH SUPERVISOR, SITE & ADVANCED ANALYTICS)
import streamlit as st
import streamlit_authenticator as stauth

st.set_page_config(page_title="AI Expense Dashboard", layout="wide")

credentials = {
    "usernames": {
        "admin": {
            "name": "Admin",
            "password": "$2b$12$KIX1n4E9CkP8p8G9wJ6dRe2Zl3dR0kQZ0PpZg9n0p5bZ0zKZy"
        },
        "manager": {
            "name": "Manager",
            "password": "$2b$12$KIX1n4E9CkP8p8G9wJ6dRe2Zl3dR0kQZ0PpZg9n0p5bZ0zKZy"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "expense_dashboard",
    "auth_key",
    cookie_expiry_days=1
)

name, auth_status, username = authenticator.login("Company Login", "main")

if auth_status is False:
    st.error("Invalid username or password")
    st.stop()
elif auth_status is None:
    st.warning("Please login")
    st.stop()

st.success(f"Welcome {name}")

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="AI Expense Dashboard", layout="wide")

def load_data():
    try:
        return pd.read_csv("expenses.csv")
    except:
        return pd.DataFrame(columns=[
            "Date", "Category", "Amount",
            "Supervisor", "Site", "Summary"
        ])

def save_data(df):
    df.to_csv("expenses.csv", index=False)

expenses = load_data()

def clean_uploaded_data(df):
    df_clean = pd.DataFrame()

    date_cols = ["date", "day", "purchase date", "entry date"]
    amount_cols = ["amount", "price", "cost", "expense"]
    category_cols = ["category", "type", "label"]
    supervisor_cols = ["supervisor", "manager", "incharge"]
    site_cols = ["site", "location", "project"]
    summary_cols = ["summary", "description", "details", "remark", "note"]

    col_map = {c.lower(): c for c in df.columns}

    def find_col(names):
        for n in names:
            if n in col_map:
                return col_map[n]
        return None

    if find_col(date_cols):
        df_clean["Date"] = pd.to_datetime(df[find_col(date_cols)], errors="coerce")
    else:
        df_clean["Date"] = pd.NaT

    if find_col(amount_cols):
        df_clean["Amount"] = pd.to_numeric(df[find_col(amount_cols)], errors="coerce")
    else:
        df_clean["Amount"] = 0

    df_clean["Category"] = df[find_col(category_cols)] if find_col(category_cols) else "Other"
    df_clean["Supervisor"] = df[find_col(supervisor_cols)] if find_col(supervisor_cols) else "Unknown"
    df_clean["Site"] = df[find_col(site_cols)] if find_col(site_cols) else "Unknown"
    df_clean["Summary"] = df[find_col(summary_cols)] if find_col(summary_cols) else ""

    return df_clean.dropna(subset=["Date", "Amount"], how="all")

st.sidebar.title("📊 AI Expense Dashboard")
menu = st.sidebar.radio(
    "Navigation",
    ["Add Expense", "Upload Expense File", "View Dashboard", "Data Table"]
)

if menu == "Add Expense":
    st.header("➕ Add New Expense")

    col1, col2, col3 = st.columns(3)

    with col1:
        date = st.date_input("Date", datetime.now())
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)

    with col2:
        category = st.selectbox(
            "Category",
            ["Food", "Travel", "Fuel", "Shopping", "Bills", "Other"]
        )
        supervisor = st.text_input("Supervisor Name")

    with col3:
        site = st.text_input("Site Name")
        summary = st.text_input("Summary / Description")

    if st.button("Save Expense"):
        new_row = pd.DataFrame({
            "Date": [date],
            "Category": [category],
            "Amount": [amount],
            "Supervisor": [supervisor],
            "Site": [site],
            "Summary": [summary]
        })

        expenses = pd.concat([expenses, new_row], ignore_index=True)
        save_data(expenses)
        st.success("Expense Saved Successfully ✅")
        st.rerun()

if menu == "Upload Expense File":
    st.header("📤 Upload Expense Sheet")

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file, engine="openpyxl")

            df_upload.columns = df_upload.columns.map(str)
            cleaned_df = clean_uploaded_data(df_upload)

            st.subheader("🧹 Cleaned Data Preview")
            st.dataframe(cleaned_df)

            if st.button("Add to Dashboard"):
                expenses = pd.concat([expenses, cleaned_df], ignore_index=True)
                save_data(expenses)
                st.success("Data Imported Successfully 🎉")
                st.rerun()

        except Exception as e:
            st.error(f"Error reading file: {e}")

if menu == "View Dashboard":
    st.header("📈 Expense Analytics")

    if expenses.empty:
        st.warning("No data available.")
    else:
        colA, colB, colC = st.columns(3)

        colA.metric("Total Spending", f"₹ {expenses['Amount'].sum():,.2f}")
        colB.metric("Total Entries", len(expenses))
        colC.metric("Total Sites", expenses["Site"].nunique())

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            fig_cat = px.pie(
                expenses,
                names="Category",
                values="Amount",
                title="Category-wise Expense"
            )
            st.plotly_chart(fig_cat, use_container_width=True)

        with col2:
            fig_day = px.bar(
                expenses,
                x="Date",
                y="Amount",
                color="Category",
                title="Daily Expenses"
            )
            st.plotly_chart(fig_day, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            site_data = expenses.groupby("Site")["Amount"].sum().reset_index()
            fig_site = px.bar(
                site_data,
                x="Site",
                y="Amount",
                title="Site-wise Expense"
            )
            st.plotly_chart(fig_site, use_container_width=True)

        with col4:
            sup_data = expenses.groupby("Supervisor")["Amount"].sum().reset_index()
            fig_sup = px.bar(
                sup_data,
                x="Supervisor",
                y="Amount",
                title="Supervisor-wise Expense"
            )
            st.plotly_chart(fig_sup, use_container_width=True)

if menu == "Data Table":
    st.header("📄 Expense Records")

    if expenses.empty:
        st.warning("No records found.")
    else:
        st.dataframe(expenses, use_container_width=True)

        if st.button("Clear All Data"):
            save_data(pd.DataFrame(columns=expenses.columns))
            st.success("All data cleared")
            st.rerun()


