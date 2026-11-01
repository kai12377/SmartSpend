
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

st.set_page_config(
    page_title="SmartSpend",
    page_icon="💰",
    layout="wide"
)

DB = "smartspend.db"

def connect():
    return sqlite3.connect(DB)

def initialize():
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            mode TEXT,
            notes TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY,
            monthly_limit REAL NOT NULL
        )
        """)

def get_transactions():
    with connect() as conn:
        return pd.read_sql_query(
            "SELECT * FROM transactions ORDER BY date DESC",
            conn
        )

def get_budgets():
    with connect() as conn:
        return pd.read_sql_query("SELECT * FROM budgets", conn)

initialize()

st.sidebar.title("💰 SmartSpend")
st.sidebar.caption("Personal Expense Tracker")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Transaction",
     "Budget Planner", "Transaction Ledger"]
)

st.title("💰 SmartSpend")
st.caption("Track your money. Manage your budget.")

df = get_transactions()
today = date.today()
month = today.strftime("%Y-%m")

monthly = df[df["date"].str.startswith(month)] if not df.empty else df

if page == "Dashboard":

    income = monthly.loc[
        monthly["type"] == "Income", "amount"
    ].sum()

    expense = monthly.loc[
        monthly["type"] == "Expense", "amount"
    ].sum()

    savings = income - expense
    rate = savings / income * 100 if income else 0

    st.subheader("Financial Dashboard")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Income", f"₹{income:,.2f}")
    c2.metric("Total Expenses", f"₹{expense:,.2f}")
    c3.metric("Net Savings", f"₹{savings:,.2f}")
    c4.metric("Savings Rate", f"{rate:.1f}%")

    st.divider()

    st.subheader("Expense Analysis")

    expenses = monthly[monthly["type"] == "Expense"]

    if not expenses.empty:
        chart = expenses.groupby("category")["amount"].sum()
        st.bar_chart(chart)
    else:
        st.info("No expenses recorded yet.")

    st.subheader("Recent Transactions")
    st.dataframe(df.head(5), use_container_width=True)

elif page == "Add Transaction":

    st.subheader("Add New Transaction")

    with st.form("transaction_form"):

        txn_date = st.date_input("Date", value=today)

        txn_type = st.selectbox(
            "Transaction Type",
            ["Expense", "Income"]
        )

        amount = st.number_input(
            "Amount (₹)", min_value=1.0
        )

        category = st.selectbox(
            "Category",
            ["Food & Dining", "Transport",
             "Rent/Bills", "Books & Stationery",
             "Entertainment", "Healthcare",
             "Salary/Allowance", "Other"]
        )

        mode = st.selectbox(
            "Payment Mode",
            ["UPI", "Cash", "Card", "Bank Transfer"]
        )

        notes = st.text_input("Notes")

        submit = st.form_submit_button("Save Transaction")

        if submit:
            with connect() as conn:
                conn.execute("""
                INSERT INTO transactions
                (date,type,category,amount,mode,notes)
                VALUES (?,?,?,?,?,?)
                """, (
                    txn_date.isoformat(),
                    txn_type,
                    category,
                    amount,
                    mode,
                    notes
                ))

            st.success("Transaction saved successfully!")
            st.rerun()

elif page == "Budget Planner":

    st.subheader("Monthly Budget Planner")

    with st.form("budget_form"):

        category = st.selectbox(
            "Select Category",
            ["Food & Dining", "Transport",
             "Rent/Bills", "Books & Stationery",
             "Entertainment", "Healthcare", "Other"]
        )

        limit = st.number_input(
            "Monthly Budget (₹)",
            min_value=100.0,
            value=5000.0
        )

        submit = st.form_submit_button("Save Budget")

        if submit:
            with connect() as conn:
                conn.execute("""
                INSERT OR REPLACE INTO budgets
                VALUES (?,?)
                """, (category, limit))

            st.success("Budget saved!")
            st.rerun()

    budgets = get_budgets()

    st.divider()
    st.subheader("Budget Status")

    for _, row in budgets.iterrows():

        spent = monthly.loc[
            (monthly["type"] == "Expense") &
            (monthly["category"] == row["category"]),
            "amount"
        ].sum()

        ratio = spent / row["monthly_limit"]

        st.write(
            f"{row['category']}: ₹{spent:.2f} / "
            f"₹{row['monthly_limit']:.2f}"
        )

        st.progress(min(float(ratio), 1.0))

        if ratio > 1:
            st.error("Budget exceeded!")
        elif ratio >= 0.8:
            st.warning("Budget almost exhausted!")
        else:
            st.success("Within budget.")

elif page == "Transaction Ledger":

    st.subheader("Transaction History")

    if not df.empty:

        txn_type = st.selectbox(
            "Filter by Type",
            ["All", "Income", "Expense"]
        )

        filtered = df.copy()

        if txn_type != "All":
            filtered = filtered[
                filtered["type"] == txn_type
            ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        csv = filtered.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download CSV Statement",
            csv,
            "smartspend_ledger.csv",
            "text/csv"
        )

    else:
        st.info("No transactions available.")
