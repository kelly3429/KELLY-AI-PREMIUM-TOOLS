import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF

# ==========================================
# 1. DATABASE SYSTEM (v19)
# ==========================================
def get_connection():
    return sqlite3.connect('kelly_ai_v19.db', check_same_thread=False)

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
    conn.commit()

init_db()

# ==========================================
# 2. PDF RECEIPT ENGINE
# ==========================================
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "KELLY AI PREMIUM TOOLS - RECEIPT", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    for key, value in data.items():
        if key in ['customer_name', 'product_name', 'amount_paid_naira', 'purchase_date', 'expiry_date', 'g2g_order_number']:
            pdf.cell(50, 10, f"{key.replace('_', ' ').title()}:")
            pdf.cell(100, 10, f"{value}", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# ==========================================
# 3. UI SETUP
# ==========================================
st.set_page_config(page_title="Kelly AI Ultimate", layout="wide")
st.title("💎 Kelly AI Ultimate: Business Manager")

tabs = st.tabs(["➕ New Sale", "📜 History & Status", "⏰ Expiry Tracker", "🚩 Vendor Tracker", "📊 Reports", "💾 Backup & Restore"])

# --- TAB 1: NEW SALE (Full Details) ---
with tabs[0]:
    st.header("Record Transaction")
    with st.form("sale_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cust = st.text_input("Customer Name")
            prod = st.selectbox("Product", ["ChatGPT Plus", "CapCut Pro", "Canva Pro", "Claude Pro", "Grok"])
            paid = st.number_input("Amount Paid (NGN)", min_value=0.0)
            p_date = st.date_input("Purchase Date", datetime.now())
            vendor = st.text_input("Vendor Name")
        with col2:
            acc_email = st.text_input("Account Email")
            acc_pass = st.text_input("Account Password")
            usd_cost = st.number_input("G2G Cost (USD)", min_value=0.0)
            rate = st.number_input("Exchange Rate", value=1550.0)
            order_no = st.text_input("G2G Order #")

        if st.form_submit_button("Save Sale"):
            profit = paid - (usd_cost * rate)
            expiry = p_date + timedelta(days=30)
            with get_connection() as conn:
                conn.execute('''INSERT INTO sales (customer_name, product_name, login_email, login_password, 
                                amount_paid_naira, g2g_cost_usd, exchange_rate, profit, purchase_date, 
                                expiry_date, g2g_order_number, status, vendor_name) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                             (cust, prod, acc_email, acc_pass, paid, usd_cost, rate, profit, p_date, expiry, order_no, "Active", vendor))
            st.success(f"Record Saved! Profit: N{profit:,.2f}")

# --- TAB 2: HISTORY, STATUS & PRINTING ---
with tabs[1]:
    st.header("📜 Sales Archive & Management")
    df_hist = pd.read_sql("SELECT * FROM sales ORDER BY purchase_date DESC", get_connection())
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            manage_id = st.number_input("Enter ID to Update/Print", min_value=1)
            new_status = st.selectbox("Update Status", ["Active", "Issue", "Refunded", "Settled"])
            if st.button("Update Status"):
                with get_connection() as conn:
                    conn.execute("UPDATE sales SET status=? WHERE id=?", (new_status, manage_id))
                st.success(f"ID {manage_id} status updated to {new_status}")
                st.rerun()
        with c2:
            if st.button("Generate PDF Receipt"):
                target_row = df_hist[df_hist['id'] == manage_id].iloc[0].to_dict()
                pdf_data = create_pdf(target_row)
                st.download_button("Download Receipt", pdf_data, f"Receipt_{manage_id}.pdf")
    else:
        st.info("No sales found.")

# --- TAB 3: EXPIRY TRACKER ---
with tabs[2]:
    st.header("⏰ Upcoming Expirations")
    df_exp = pd.read_sql("SELECT customer_name, product_name, expiry_date, login_email FROM sales", get_connection())
    if not df_exp.empty:
        df_exp['expiry_date'] = pd.to_datetime(df_exp['expiry_date']).dt.date
        today = datetime.now().date()
        upcoming = df_exp[df_exp['expiry_date'] <= (today + timedelta(days=3))]
        if not upcoming.empty:
            st.table(upcoming)
        else:
            st.success("No accounts expiring in the next 3 days!")

# --- TAB 4: VENDOR TRACKER (Issue Tracker) ---
with tabs[3]:
    st.header("🚩 G2G Vendor Issue Tracker")
    df_vend = pd.read_sql("SELECT vendor_name, g2g_order_number, product_name, status, customer_name FROM sales WHERE status != 'Active'", get_connection())
    if not df_vend.empty:
        st.warning("Below are the accounts with issues. Follow up with vendors.")
        st.table(df_vend)
    else:
        st.success("All accounts are currently Active. No vendor issues!")

# --- TAB 5: REPORTS ---
with tabs[4]:
    st.header("📊 Financial Performance")
    df_rep = pd.read_sql("SELECT profit, purchase_date FROM sales", get_connection())
    if not df_rep.empty:
        total_p = df_rep['profit'].sum()
        st.metric("Total All-Time Profit", f"N{total_p:,.2f}")
        st.write("### Profit per Day")
        st.bar_chart(df_rep.groupby('purchase_date')['profit'].sum())

# --- TAB 6: BACKUP & RESTORE (RE-UPLOAD ADDED) ---
with tabs[5]:
    st.header("💾 Data Insurance")
    # Backup Download
    full_df = pd.read_sql("SELECT * FROM sales", get_connection())
    st.download_button("📥 Download Database (CSV)", full_df.to_csv(index=False).encode('utf-8'), "kelly_ai_backup.csv")
    
    st.divider()
    # Restore Upload
    st.subheader("📤 Restore/Re-upload History")
    restore_file = st.file_uploader("Upload your backup CSV file to restore data", type="csv")
    if restore_file is not None:
        if st.button("Click to Restore All Data"):
            new_data = pd.read_csv(restore_file)
            with get_connection() as conn:
                new_data.to_sql('sales', conn, if_exists='append', index=False)
            st.success("Database restored! All old sales have been added.")
            st.rerun()
