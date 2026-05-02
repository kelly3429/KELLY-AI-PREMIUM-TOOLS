import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# ==========================================
# 1. DATABASE SYSTEM (v16)
# ==========================================
@st.cache_resource
def get_connection():
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
# 2. RECEIPT GENERATOR FUNCTION
# ==========================================
def create_receipt_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, "KELLY AI PREMIUM TOOLS", ln=True, align='C')
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(190, 10, f"Date: {data['purchase_date']}", ln=True, align='C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "OFFICIAL PURCHASE RECEIPT", ln=True, align='L')
    pdf.set_font("Helvetica", '', 11)
    pdf.ln(5)
    
    details = [
        ("Order Number", str(data['g2g_order_number'])),
        ("Customer Name", str(data['customer_name'])),
        ("Product", str(data['product_name'])),
        ("Amount Paid", f"N{data['amount_paid_naira']:,.2f}"),
        ("Expiry Date", str(data['expiry_date']))
    ]
    
    for label, val in details:
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(50, 10, f"{label}:", border=0)
        pdf.set_font("Helvetica", '', 11)
        pdf.cell(140, 10, f"{val}", ln=True, border=0)
    
    pdf.ln(20)
    pdf.set_font("Helvetica", 'I', 10)
    pdf.cell(190, 10, "Thank you for your patronage! Stay Premium.", align='C')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# ==========================================
# 3. UI SETUP
# ==========================================
st.set_page_config(page_title="Kelly AI Ultimate", layout="wide")
st.title("💰 Kelly AI Management Suite")

tabs = st.tabs(["➕ New Sale", "🔍 Search & Manage", "📈 Insights", "📊 Reports", "🚩 Vendors"])

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
            st.success("Sale Recorded!")
            st.rerun()

# --- TAB 2: SEARCH & MANAGE & RECEIPTS ---
with tabs[1]:
    st.header("Inventory & Receipts")
    df = pd.read_sql("SELECT * FROM sales", get_connection())
    
    if not df.empty:
        # Search
        search = st.text_input("🔍 Search Name or Order #")
        if search:
            df = df[(df['customer_name'].str.contains(search, case=False)) | 
                    (df['g2g_order_number'].str.contains(search, case=False))]
        
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🖨️ Generate Receipt")
            r_id = st.number_input("Enter ID for Receipt", min_value=1, key="rec_id")
            if st.button("Prepare PDF"):
                record = df[df['id'] == r_id].iloc[0]
                pdf_bytes = create_receipt_pdf(record)
                st.download_button("Download PDF Receipt", pdf_bytes, f"Receipt_{record['customer_name']}.pdf", "application/pdf")
        
        with c2:
            st.subheader("🗑️ Delete / Update")
            d_id = st.number_input("Enter ID #", min_value=1, key="man_id")
            if st.button("Delete Permanentely"):
                get_connection().execute("DELETE FROM sales WHERE id=?", (d_id,))
                get_connection().commit()
                st.rerun()

# --- TAB 3: CUSTOMER INSIGHTS (NEW) ---
with tabs[2]:
    st.header("📈 Customer Growth Tracking")
    df_in = pd.read_sql("SELECT customer_name, purchase_date FROM sales", get_connection())
    
    if not df_in.empty:
        total_purchases = len(df_in)
        # Unique customer count (Doesn't double count names)
        unique_customers = df_in['customer_name'].nunique()
        
        col_in1, col_in2 = st.columns(2)
        col_in1.metric("Total Successful Sales", total_purchases)
        col_in2.metric("Unique Customer Base", unique_customers)
        
        st.write(f"On average, your customers buy **{total_purchases/unique_customers:.1f}** items each.")
    else:
        st.info("No data yet.")

# --- TAB 4: FINANCIAL REPORTS & BACKUP ---
with tabs[3]:
    st.header("📊 Financial Reports")
    df_f = pd.read_sql("SELECT * FROM sales", get_connection())
    if not df_f.empty:
        df_f['purchase_date'] = pd.to_datetime(df_f['purchase_date']).dt.date
        today = datetime.now().date()
        daily = df_f[df_f['purchase_date'] == today]['profit'].sum()
        st.metric("Today's Profit", f"N{daily:,.2f}")
        
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Backup Database (CSV)", csv, "kelly_backup.csv", "text/csv")

# --- TAB 5: VENDOR TRACKER ---
with tabs[4]:
    st.header("🚩 Vendor Issue Tracker")
    df_v = pd.read_sql("SELECT vendor_name, g2g_order_number, customer_name, status FROM sales WHERE status != 'Active'", get_connection())
    if not df_v.empty:
        st.table(df_v)
    else:
        st.success("No issues reported!")
