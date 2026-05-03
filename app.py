import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF

# ==========================================
# 1. DATABASE SYSTEM (v20)
# ==========================================
def get_connection():
    return sqlite3.connect('kelly_ai_v20.db', check_same_thread=False)

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
    fields = ['customer_name', 'product_name', 'amount_paid_naira', 'purchase_date', 'expiry_date', 'g2g_order_number']
    for key in fields:
        pdf.cell(50, 10, f"{key.replace('_', ' ').title()}:")
        pdf.cell(100, 10, f"{data[key]}", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# ==========================================
# 3. UI SETUP
# ==========================================
st.set_page_config(page_title="Kelly AI Ultimate", layout="wide")
st.title("💎 Kelly AI Ultimate: Business Manager")

tabs = st.tabs(["➕ New Sale", "📜 History & Manager", "⏰ Expiry Tracker", "🚩 Vendor Tracker", "📊 Reports", "💾 Backup & Restore"])

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
            vendor = st.text_input("Vendor Name")
        with col2:
            acc_email = st.text_input("Account Email")
            acc_pass = st.text_input("Account Password")
            usd_cost = st.number_input("G2G Cost (USD)", min_value=0.0)
            rate = st.number_input("Exchange Rate", value=1550.0)
            order_no = st.text_input("G2G Order #")

        if st.form_submit_button("Save Sale"):
            prof = paid - (usd_cost * rate)
            exp = p_date + timedelta(days=30)
            with get_connection() as conn:
                conn.execute('''INSERT INTO sales (customer_name, product_name, login_email, login_password, 
                                amount_paid_naira, g2g_cost_usd, exchange_rate, profit, purchase_date, 
                                expiry_date, g2g_order_number, status, vendor_name) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                             (cust, prod, acc_email, acc_pass, paid, usd_cost, rate, prof, p_date, exp, order_no, "Active", vendor))
            st.success(f"Saved! Profit: N{prof:,.2f}")

# --- TAB 2: HISTORY, EDIT & DELETE ---
with tabs[1]:
    st.header("📜 Archive, Edit & Delete")
    df_hist = pd.read_sql("SELECT * FROM sales ORDER BY purchase_date DESC", get_connection())
    
    if not df_hist.empty:
        search = st.text_input("🔍 Search Archive (Name, Email, or Order #)")
        if search:
            df_hist = df_hist[df_hist.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        st.dataframe(df_hist, use_container_width=True)
        st.divider()
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.subheader("🛠️ Quick Update")
            manage_id = st.number_input("Enter ID #", min_value=1)
            new_status = st.selectbox("Status", ["Active", "Issue", "Refunded", "Settled"])
            if st.button("Apply Status"):
                with get_connection() as conn:
                    conn.execute("UPDATE sales SET status=? WHERE id=?", (new_status, manage_id))
                st.rerun()
            if st.button("Generate PDF Receipt"):
                target = df_hist[df_hist['id'] == manage_id].iloc[0].to_dict()
                st.download_button("Download PDF", create_pdf(target), f"Receipt_{manage_id}.pdf")

        with c2:
            st.subheader("📝 Full Edit")
            if manage_id:
                record = df_hist[df_hist['id'] == manage_id]
                if not record.empty:
                    with st.expander("Click to Edit Details"):
                        new_name = st.text_input("Name", value=record.iloc[0]['customer_name'])
                        new_login = st.text_input("Login", value=record.iloc[0]['login_email'])
                        new_pass = st.text_input("Pass", value=record.iloc[0]['login_password'])
                        if st.button("Save Changes"):
                            with get_connection() as conn:
                                conn.execute("UPDATE sales SET customer_name=?, login_email=?, login_password=? WHERE id=?", 
                                             (new_name, new_login, new_pass, manage_id))
                            st.success("Record Updated!")
                            st.rerun()

        with c3:
            st.subheader("🗑️ Danger Zone")
            if st.button("DELETE PERMANENTLY"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM sales WHERE id=?", (manage_id,))
                st.error(f"ID {manage_id} Deleted.")
                st.rerun()
    else:
        st.info("No records found.")

# --- TAB 3: EXPIRY TRACKER ---
with tabs[2]:
    st.header("⏰ Expiry Alerts")
    df_exp = pd.read_sql("SELECT customer_name, product_name, expiry_date, login_email FROM sales", get_connection())
    if not df_exp.empty:
        df_exp['expiry_date'] = pd.to_datetime(df_exp['expiry_date']).dt.date
        today = datetime.now().date()
        upcoming = df_exp[df_exp['expiry_date'] <= (today + timedelta(days=3))]
        st.table(upcoming) if not upcoming.empty else st.success("All accounts healthy!")

# --- TAB 4: VENDOR TRACKER ---
with tabs[3]:
    st.header("🚩 G2G Vendor Issues")
    df_vend = pd.read_sql("SELECT vendor_name, g2g_order_number, product_name, status, customer_name FROM sales WHERE status != 'Active'", get_connection())
    st.table(df_vend) if not df_vend.empty else st.success("No vendor issues!")

# --- TAB 5: REPORTS ---
with tabs[4]:
    st.header("📊 Profit Analytics")
    df_rep = pd.read_sql("SELECT profit, purchase_date FROM sales", get_connection())
    if not df_rep.empty:
        st.metric("Total Overall Profit", f"N{df_rep['profit'].sum():,.2f}")
        st.bar_chart(df_rep.groupby('purchase_date')['profit'].sum())

# --- TAB 6: BACKUP & RESTORE ---
with tabs[5]:
    st.header("💾 Data Insurance")
    full_df = pd.read_sql("SELECT * FROM sales", get_connection())
    st.download_button("📥 Download Backup (CSV)", full_df.to_csv(index=False).encode('utf-8'), "kelly_ai_backup.csv")
    
    st.divider()
    st.subheader("📤 Restore History")
    restore_file = st.file_uploader("Upload CSV", type="csv")
    if restore_file is not None and st.button("Merge Data"):
        new_data = pd.read_csv(restore_file)
        with get_connection() as conn:
            new_data.to_sql('sales', conn, if_exists='append', index=False)
        st.success("Restored!")
        st.rerun()
