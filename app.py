import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# ==========================================
# 1. DATABASE SYSTEM (v16)
# ==========================================
@st.cache_resource
def get_connection():
    # v16 includes columns for order IDs and expiry tracking
    conn = sqlite3.connect('kelly_ai_v16.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  customer_name TEXT, product_name TEXT, 
                  amount_paid_naira REAL, g2g_cost_usd REAL, 
                  exchange_rate REAL, profit REAL, 
                  purchase_date DATE, expiry_date DATE,
                  g2g_order_number TEXT, status TEXT, 
                  vendor_name TEXT)''')
    conn.commit()

init_db()

# ==========================================
# 2. UI SETUP (Mobile Optimized)
# ==========================================
st.set_page_config(page_title="Kelly AI Ultimate", layout="wide")
st.title("💰 Kelly AI Sales & Inventory")

tab1, tab2, tab3, tab4 = st.tabs(["➕ New Sale", "🔍 Search & Manage", "📊 Reports", "🚩 Vendor Tracker"])

# --- TAB 1: NEW SALE ---
with tab1:
    st.header("Record Transaction")
    with st.form("sale_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cust = st.text_input("Customer Name")
            prod = st.selectbox("Product", ["ChatGPT Plus", "CapCut Pro", "Canva Pro", "Claude Pro", "Super Grok"])
            order_no = st.text_input("G2G Order Number")
            paid = st.number_input("Customer Paid (NGN)", min_value=0.0)
        with col2:
            usd = st.number_input("G2G Cost (USD)", min_value=0.0)
            rate = st.number_input("Rate (NGN/$)", value=1550.0)
            vendor = st.text_input("G2G Vendor Name")
            duration = st.number_input("Duration (Days)", value=30)
        
        if st.form_submit_button("Save Sale"):
            p_date = datetime.now().date()
            e_date = p_date + timedelta(days=duration)
            profit = paid - (usd * rate)
            
            conn = get_connection()
            conn.execute('''INSERT INTO sales (customer_name, product_name, amount_paid_naira, 
                            g2g_cost_usd, exchange_rate, profit, purchase_date, expiry_date, 
                            g2g_order_number, status, vendor_name) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)''', 
                         (cust, prod, paid, usd, rate, profit, p_date, e_date, order_no, "Active", vendor))
            conn.commit()
            st.success("Sale Recorded Successfully!")
            st.rerun()

# --- TAB 2: SEARCH & EXPIRY TRACKING ---
with tab2:
    st.header("Inventory & Expiry Management")
    df = pd.read_sql("SELECT * FROM sales", get_connection())
    
    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date']).dt.date
        today = datetime.now().date()

        # Logic for Expiry Highlighting
        def highlight_expiry(row):
            diff = (row['expiry_date'] - today).days
            if row['status'] in ["Issue", "Refunded"]: return ['background-color: #ffcccc'] * len(row)
            if diff < 0: return ['background-color: #ff4b4b'] * len(row) # Red for Expired
            if 0 <= diff <= 3: return ['background-color: #ffaa00'] * len(row) # Orange for 3-day notice
            return [''] * len(row)

        search = st.text_input("🔍 Search Name or Order #")
        if search:
            df = df[(df['customer_name'].str.contains(search, case=False)) | 
                    (df['g2g_order_number'].str.contains(search, case=False))]
        
        st.write("💡 **Orange**: 3 Days Left | **Red**: Expired")
        st.dataframe(df.style.apply(highlight_expiry, axis=1), use_container_width=True)
        
        st.divider()
        col_upd, col_del = st.columns(2)
        with col_upd:
            u_id = st.number_input("ID # to Update", min_value=1, key="u_id")
            new_stat = st.selectbox("Status", ["Active", "Issue", "Refunded", "Expired"], key="u_stat")
            if st.button("Update Status"):
                get_connection().execute("UPDATE sales SET status=? WHERE id=?", (new_stat, u_id))
                get_connection().commit()
                st.rerun()
        with col_del:
            d_id = st.number_input("ID # to Delete", min_value=1, key="d_id")
            if st.button("🗑️ Delete Permanently"):
                get_connection().execute("DELETE FROM sales WHERE id=?", (d_id,))
                get_connection().commit()
                st.rerun()

# --- TAB 3: REPORTS ---
with tab3:
    st.header("Financials")
    df_f = pd.read_sql("SELECT profit, purchase_date FROM sales", get_connection())
    if not df_f.empty:
        df_f['purchase_date'] = pd.to_datetime(df_f['purchase_date']).dt.date
        today = datetime.now().date()
        daily = df_f[df_f['purchase_date'] == today]['profit'].sum()
        st.metric("Today's Profit", f"N{daily:,.2f}")
        st.dataframe(df_f)

# --- TAB 4: VENDOR TRACKER ---
with tab4:
    st.header("G2G Vendor Performance")
    # Filters only for problematic accounts to specify the customer and order ID
    vendor_query = """SELECT vendor_name, g2g_order_number, customer_name, product_name, status 
                      FROM sales WHERE status IN ('Issue', 'Refunded')"""
    df_v = pd.read_sql(vendor_query, get_connection())
    if not df_v.empty:
        st.warning("Accounts requiring vendor contact:")
        st.table(df_v)
    else:
        st.success("No vendor issues found!")
