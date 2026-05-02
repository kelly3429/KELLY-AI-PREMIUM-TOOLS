import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# ==========================================
# 1. DATABASE SYSTEM (v15)
# ==========================================
@st.cache_resource
def get_connection():
    # Using v15 to ensure the database starts clean with all required columns
    conn = sqlite3.connect('kelly_ai_v15.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  customer_name TEXT, product_name TEXT, 
                  amount_paid_naira REAL, g2g_cost_usd REAL, 
                  exchange_rate REAL, profit REAL, 
                  purchase_date DATE, status TEXT, 
                  vendor_name TEXT)''')
    conn.commit()

init_db()

# ==========================================
# 2. UI SETUP (Mobile Optimized)
# ==========================================
st.set_page_config(page_title="Kelly AI Manager", layout="wide")
st.title("💰 Kelly AI Sales Tracker")

# Tabs are easier to tap than a sidebar on an iPhone
tab1, tab2, tab3, tab4 = st.tabs(["➕ New Sale", "🔍 Search & Manage", "📊 Reports", "🚩 Vendors"])

# --- TAB 1: NEW SALE ---
with tab1:
    st.header("Record Transaction")
    with st.form("sale_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cust = st.text_input("Customer Name")
            prod = st.selectbox("Product", ["ChatGPT Plus", "CapCut Pro", "Canva Pro", "Claude Pro", "Super Grok"])
            paid = st.number_input("Customer Paid (NGN)", min_value=0.0)
        with col2:
            usd = st.number_input("G2G Cost (USD)", min_value=0.0)
            rate = st.number_input("Rate (NGN/$)", value=1550.0)
            vendor = st.text_input("G2G Vendor Name")
        
        if st.form_submit_button("Save Sale"):
            n_cost = usd * rate
            calc_profit = paid - n_cost
            today = datetime.now().date()
            
            conn = get_connection()
            conn.execute('''INSERT INTO sales (customer_name, product_name, amount_paid_naira, 
                            g2g_cost_usd, exchange_rate, profit, purchase_date, status, vendor_name) 
                            VALUES (?,?,?,?,?,?,?,?,?)''', 
                         (cust, prod, paid, usd, rate, calc_profit, today, "Active", vendor))
            conn.commit()
            st.success(f"Saved! Profit: N{calc_profit:,.2f}")
            st.rerun()

# --- TAB 2: SEARCH & DELETE (FIXED) ---
with tab2:
    st.header("Inventory Manager")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM sales", conn)
    
    search = st.text_input("🔍 Search by Name")
    if search:
        df = df[df['customer_name'].str.contains(search, case=False)]
    
    st.dataframe(df, use_container_width=True)
    
    st.divider()
    # Unique keys prevent "Duplicate Widget ID" errors
    d_id = st.number_input("Enter ID # to Delete", min_value=1, step=1, key="del_id_input")
    confirm = st.checkbox("Confirm permanent deletion", key="del_confirm")
    if st.button("🗑️ Delete Now", key="del_button"):
        if confirm:
            conn.execute("DELETE FROM sales WHERE id=?", (d_id,))
            conn.commit()
            st.warning(f"Record {d_id} deleted!")
            st.rerun()
        else:
            st.error("Please check the box to confirm.")

# --- TAB 3: DAILY/WEEKLY/MONTHLY REPORTS ---
with tab3:
    st.header("Financial Overview")
    df_f = pd.read_sql("SELECT profit, purchase_date FROM sales", get_connection())
    if not df_f.empty:
        df_f['purchase_date'] = pd.to_datetime(df_f['purchase_date']).dt.date
        today = datetime.now().date()
        
        daily = df_f[df_f['purchase_date'] == today]['profit'].sum()
        week_ago = today - timedelta(days=7)
        weekly = df_f[df_f['purchase_date'] >= week_ago]['profit'].sum()
        this_month = today.month
        monthly = df_f[pd.to_datetime(df_f['purchase_date']).dt.month == this_month]['profit'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Today", f"N{daily:,.2f}")
        c2.metric("Weekly", f"N{weekly:,.2f}")
        c3.metric("Monthly", f"N{monthly:,.2f}")
    else:
        st.info("No sales data yet.")

# --- TAB 4: VENDOR TRACKER ---
with tab4:
    st.header("Vendor Accountability")
    issues = pd.read_sql("SELECT vendor_name, customer_name, status FROM sales WHERE status != 'Active'", get_connection())
    if not issues.empty:
        st.table(issues)
    else:
        st.success("No issues found!")
