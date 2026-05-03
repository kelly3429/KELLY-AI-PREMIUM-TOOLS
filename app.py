import streamlit as st
import pd as pd
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# ==========================================
# 1. DATABASE SYSTEM (v17)
# ==========================================
@st.cache_resource
def get_connection():
    conn = sqlite3.connect('kelly_ai_v17.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Added login_password to the schema
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  customer_name TEXT, product_name TEXT, 
                  login_email TEXT, login_password TEXT,
                  amount_paid_naira REAL, 
                  g2g_cost_usd REAL, exchange_rate REAL, profit REAL, 
                  purchase_date DATE, expiry_date DATE,
                  g2g_order_number TEXT, status TEXT, 
                  vendor_name TEXT)''')
    conn.commit()

init_db()

# ==========================================
# 2. RECEIPT GENERATOR FUNCTION
# ==========================================
def create_receipt_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, "KELLY AI PREMIUM TOOLS", ln=True, align='C')
    pdf.ln(10)
    
    details = [
        ("Order Number", str(data['g2g_order_number'])),
        ("Customer Name", str(data['customer_name'])),
        ("Product", str(data['product_name'])),
        ("Login Account", str(data['login_email'])),
        ("Amount Paid", f"N{data['amount_paid_naira']:,.2f}"),
        ("Purchase Date", str(data['purchase_date'])),
        ("Expiry Date", str(data['expiry_date']))
    ]
    
    for label, val in details:
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(50, 10, f"{label}:")
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(140, 10, f"{val}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# ==========================================
# 3. UI SETUP
# ==========================================
st.set_page_config(page_title="Kelly AI Ultimate", layout="wide")
st.title("💰 Kelly AI Management Suite")

tabs = st.tabs(["➕ New Sale", "🔍 Search & Manage", "📈 Insights & Restore", "📊 Reports", "🚩 Vendor Tracker"])

# --- TAB 1: NEW SALE ---
with tabs[0]:
    st.header("Record Transaction")
    with st.form("sale_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cust = st.text_input("Customer Name")
            prod = st.selectbox("Product", ["ChatGPT Plus", "CapCut Pro", "Canva Pro", "Claude Pro", "Super Grok"])
            order_no = st.text_input("G2G Order Number")
            paid = st.number_input("Customer Paid (NGN)", min_value=0.0)
            manual_date = st.date_input("Purchase Date", datetime.now())
        
        with col2:
            # NEW INPUTS FOR ACCOUNT CREDENTIALS
            acc_email = st.text_input("Account Email/Login")
            acc_pass = st.text_input("Account Password")
            
            usd = st.number_input("G2G Cost (USD)", min_value=0.0)
            rate = st.number_input("Rate (NGN/$)", value=1550.0)
            vendor = st.text_input("G2G Vendor Name")
            duration = st.number_input("Duration (Days)", value=30)
            initial_status = st.selectbox("Initial Account Status", ["Active", "Issue", "Refunded"])
        
        if st.form_submit_button("Save Sale"):
            e_date = manual_date + timedelta(days=duration)
            profit = paid - (usd * rate)
            
            conn = get_connection()
            # Updated INSERT to include password
            conn.execute('''INSERT INTO sales (customer_name, product_name, login_email, login_password, 
                            amount_paid_naira, g2g_cost_usd, exchange_rate, profit, 
                            purchase_date, expiry_date, g2g_order_number, status, vendor_name) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                         (cust, prod, acc_email, acc_pass, paid, usd, rate, profit, 
                          manual_date, e_date, order_no, initial_status, vendor))
            conn.commit()
            st.success(f"Sale Recorded for {cust} on {manual_date}!")
            st.rerun()

# --- TAB 2: SEARCH & MANAGE ---
with tabs[1]:
    st.header("Inventory & Status Management")
    df = pd.read_sql("SELECT * FROM sales", get_connection())
    
    if not df.empty:
        search = st.text_input("🔍 Search Name, Account, or Order #")
        if search:
            df = df[(df['customer_name'].str.contains(search, case=False)) | 
                    (df['login_email'].str.contains(search, case=False)) |
                    (df['g2g_order_number'].str.contains(search, case=False))]
        
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            target_id = st.number_input("Enter ID # to Manage", min_value=1, key="manage_id")
            new_status = st.selectbox("Change Status To", ["Active", "Issue", "Refunded", "Settled"], key="status_update")
            if st.button("Apply Status Update"):
                get_connection().execute("UPDATE sales SET status=? WHERE id=?", (new_status, target_id))
                get_connection().commit()
                st.rerun()
                
            if st.button("Prepare PDF Receipt"):
                record = df[df['id'] == target_id].iloc[0]
                pdf_bytes = create_receipt_pdf(record)
                st.download_button("Download PDF", pdf_bytes, f"Receipt_{record['customer_name']}.pdf")
        
        with c2:
            d_id = st.number_input("Enter ID # to Delete", min_value=1, key="del_id")
            if st.button("🗑️ Delete Permanently"):
                get_connection().execute("DELETE FROM sales WHERE id=?", (d_id,))
                get_connection().commit()
                st.rerun()

# --- TAB 3: INSIGHTS & RESTORE ---
with tabs[2]:
    st.header("📈 Growth & Data Restore")
    df_in = pd.read_sql("SELECT * FROM sales", get_connection())
    
    c_i1, c_i2 = st.columns(2)
    if not df_in.empty:
        c_i1.metric("Total Purchases", len(df_in))
        c_i2.metric("Unique Customers", df_in['customer_name'].nunique())
    
    st.divider()
    st.subheader("📤 Restore from Backup")
    uploaded_file = st.file_uploader("Choose your backup CSV file", type="csv")
    
    if uploaded_file is not None:
        if st.button("Process Restore"):
            backup_df = pd.read_csv(uploaded_file)
            conn = get_connection()
            for index, row in backup_df.iterrows():
                conn.execute('''INSERT OR IGNORE INTO sales 
                                (customer_name, product_name, login_email, login_password, amount_paid_naira, 
                                 g2g_cost_usd, exchange_rate, profit, purchase_date, expiry_date, 
                                 g2g_order_number, status, vendor_name) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                             (row['customer_name'], row['product_name'], row.get('login_email', ''), 
                              row.get('login_password', ''), row['amount_paid_naira'], 
                              row['g2g_cost_usd'], row['exchange_rate'], row['profit'], 
                              row['purchase_date'], row['expiry_date'], row['g2g_order_number'], 
                              row['status'], row['vendor_name']))
            conn.commit()
            st.success("Backup successfully integrated!")
            st.rerun()

# --- TAB 4: FINANCIAL REPORTS ---
with tabs[3]:
    st.header("📊 Financial Reports")
    df_f = pd.read_sql("SELECT profit, purchase_date FROM sales", get_connection())
    if not df_f.empty:
        df_f['purchase_date'] = pd.to_datetime(df_f['purchase_date']).dt.date
        today = datetime.now().date()
        daily = df_f[df_f['purchase_date'] == today]['profit'].sum()
        st.metric("Today's Profit", f"N{daily:,.2f}")
        
        full_df = pd.read_sql("SELECT * FROM sales", get_connection())
        csv = full_df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Download Backup (CSV)", csv, f"kelly_backup_{today}.csv", "text/csv")

# --- TAB 5: VENDOR TRACKER ---
with tabs[4]:
    st.header("🚩 Vendor Tracker")
    query = "SELECT vendor_name, g2g_order_number, customer_name, login_email, status FROM sales WHERE status != 'Active'"
    df_v = pd.read_sql(query, get_connection())
    if not df_v.empty:
        st.table(df_v)
    else:
        st.success("No vendor issues reported!")
