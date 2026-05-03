import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF

# ==========================================
# 1. DATABASE SYSTEM (v18 - Historical Fix)
# ==========================================
def get_connection():
    return sqlite3.connect('kelly_ai_v18.db', check_same_thread=False)

def init_db():
    with get_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS sales 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      customer_name TEXT, product_name TEXT, 
                      login_email TEXT, login_password TEXT,
                      amount_paid_naira REAL, g2g_cost_usd REAL, 
                      exchange_rate REAL, profit REAL, 
                      purchase_date DATE, expiry_date DATE,
                      g2g_order_number TEXT, status TEXT, 
                      vendor_name TEXT)''')

init_db()

# ==========================================
# 2. UI SETUP
# ==========================================
st.set_page_config(page_title="Kelly AI Ultimate", layout="wide")
st.title("💎 Kelly AI: Full Business Manager")

tabs = st.tabs(["➕ New Sale", "📜 Sales History", "⏰ Expiry Tracker", "📊 Reports", "💾 Backup & Restore"])

# --- TAB 1: NEW SALE ---
with tabs[0]:
    st.header("Record Transaction")
    with st.form("sale_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cust = st.text_input("Customer Name")
            prod = st.selectbox("Product", ["ChatGPT Plus", "CapCut Pro", "Canva Pro", "Claude Pro", "Grok"])
            paid = st.number_input("Amount Paid (NGN)", min_value=0.0)
            p_date = st.date_input("Purchase Date", datetime.now())
        with col2:
            acc_email = st.text_input("Account Email")
            acc_pass = st.text_input("Account Password")
            usd_cost = st.number_input("G2G Cost (USD)", min_value=0.0)
            rate = st.number_input("Rate", value=1550.0)
            order_no = st.text_input("G2G Order #")

        if st.form_submit_button("Save Sale"):
            profit = paid - (usd_cost * rate)
            expiry = p_date + timedelta(days=30)
            with get_connection() as conn:
                conn.execute('''INSERT INTO sales (customer_name, product_name, login_email, login_password, 
                                amount_paid_naira, g2g_cost_usd, exchange_rate, profit, purchase_date, 
                                expiry_date, g2g_order_number, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                             (cust, prod, acc_email, acc_pass, paid, usd_cost, rate, profit, p_date, expiry, order_no, "Active"))
            st.success(f"Saved! Sale recorded for {p_date}")

# --- TAB 2: SALES HISTORY (Fix for "Previous Sales") ---
with tabs[1]:
    st.header("📜 All-Time Sales Archive")
    df = pd.read_sql("SELECT * FROM sales ORDER BY purchase_date DESC", get_connection())
    if not df.empty:
        search = st.text_input("Search by Name or Order ID")
        if search:
            df = df[df['customer_name'].str.contains(search, case=False)]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No sales found.")

# --- TAB 3: EXPIRY TRACKER ---
with tabs[2]:
    st.header("⏰ Expiry & Renewal Watch")
    df_exp = pd.read_sql("SELECT customer_name, product_name, expiry_date FROM sales", get_connection())
    if not df_exp.empty:
        df_exp['expiry_date'] = pd.to_datetime(df_exp['expiry_date']).dt.date
        today = datetime.now().date()
        # Filter for accounts expiring in next 3 days
        upcoming = df_exp[df_exp['expiry_date'] <= (today + timedelta(days=3))]
        st.write("### Accounts Expiring Soon")
        st.table(upcoming)

# --- TAB 4: REPORTS (Fix for "Historical Profit") ---
with tabs[3]:
    st.header("📊 Business Performance")
    df_rep = pd.read_sql("SELECT profit, purchase_date FROM sales", get_connection())
    if not df_rep.empty:
        total_p = df_rep['profit'].sum()
        st.metric("All-Time Total Profit", f"N{total_p:,.2f}")
        st.write("### Profit Trend")
        st.bar_chart(df_rep.groupby('purchase_date')['profit'].sum())

# --- TAB 5: BACKUP ---
with tabs[4]:
    st.header("💾 Data Safety")
    full_df = pd.read_sql("SELECT * FROM sales", get_connection())
    st.download_button("Download CSV Backup", full_df.to_csv(index=False).encode('utf-8'), "kelly_backup.csv")
