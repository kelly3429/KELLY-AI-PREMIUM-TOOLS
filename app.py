import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF

# ==========================================
# 1. DATABASE SETUP
# ==========================================
@st.cache_resource
def get_db_connection():
    # check_same_thread=False is required for SQLite in Streamlit
    conn = sqlite3.connect('kelly_tools_v1.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  customer_name TEXT, product_name TEXT, 
                  login_email TEXT, login_password TEXT,
                  amount_received REAL, profit REAL, 
                  purchase_date DATE, expiry_date DATE, 
                  status TEXT)''')
    conn.commit()

init_db()

# ==========================================
# 2. PDF RECEIPT GENERATOR
# ==========================================
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, "KELLY AI PREMIUM TOOLS", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", '', 12)
    fields = [
        ("Customer", data['customer_name']),
        ("Product", data['product_name']),
        ("Login", data['login_email']),
        ("Password", data['login_password']),
        ("Expiry", str(data['expiry_date']))
    ]
    for label, val in fields:
        pdf.cell(40, 10, f"{label}:")
        pdf.cell(150, 10, f"{val}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# ==========================================
# 3. MOBILE APP INTERFACE
# ==========================================
st.set_page_config(page_title="Kelly AI", layout="centered")
st.title("💎 Kelly AI Manager")

# Using Tabs for better mobile navigation
tab1, tab2, tab3 = st.tabs(["➕ New Sale", "📋 Inventory", "📊 Finance"])

# --- TAB 1: ADD NEW SALE ---
with tab1:
    with st.form("sale_form", clear_on_submit=True):
        c_name = st.text_input("Customer Name")
        p_name = st.selectbox("Product", ["CapCut", "ChatGPT", "Canva", "Claude"])
        email = st.text_input("Account Email")
        pwd = st.text_input("Password")
        price = st.number_input("Amount Received (NGN)", min_value=0)
        cost = st.number_input("Cost (NGN)", min_value=0)
        duration = st.number_input("Days (Duration)", value=30)
        
        if st.form_submit_button("Record Sale"):
            p_date = datetime.now().date()
            e_date = p_date + timedelta(days=duration)
            profit = price - cost
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''INSERT INTO sales (customer_name, product_name, login_email, 
                         login_password, amount_received, profit, purchase_date, 
                         expiry_date, status) VALUES (?,?,?,?,?,?,?,?,?)''',
                      (c_name, p_name, email, pwd, price, profit, p_date, e_date, "Active"))
            conn.commit()
            st.success("Sale Saved Successfully!")

# --- TAB 2: INVENTORY & RECEIPTS ---
with tab2:
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM sales", conn)
    
    if not df.empty:
        st.dataframe(df[['id', 'customer_name', 'product_name', 'expiry_date']])
        
        target_id = st.selectbox("Select ID for Receipt", df['id'].tolist())
        if st.button("Generate Receipt"):
            row = df[df['id'] == target_id].iloc[0]
            pdf_file = create_pdf(row)
            st.download_button("Download PDF", pdf_file, f"Receipt_{target_id}.pdf")
            
        # Backup Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Backup to Excel (CSV)", csv, "my_data.csv", "text/csv")
    else:
        st.write("No records found.")

# --- TAB 3: FINANCIALS ---
with tab3:
    conn = get_db_connection()
    df_fin = pd.read_sql("SELECT profit FROM sales", conn)
    if not df_fin.empty:
        total_profit = df_fin['profit'].sum()
        st.metric("Total Net Profit", f"N{total_profit:,.2f}")
