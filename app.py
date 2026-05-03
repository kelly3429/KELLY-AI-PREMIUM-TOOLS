import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
from email.message import EmailMessage
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# ==========================================
# 1. CONFIGURATION
# ==========================================
COMPANY_NAME = "Kelly AI Premium Tools"
ADMIN_PASSWORD = "Kelly500#"
MY_WHATSAPP = "2347060911547"

# EMAIL CONFIG
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "your_app_password" 

def get_connection():
    return sqlite3.connect('kelly_ai_v32.db', check_same_thread=False)

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sales 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, cust_email TEXT, product TEXT, 
                      p_login TEXT, p_pass TEXT, profit REAL, p_date DATE, e_date DATE, 
                      order_id TEXT, vendor TEXT, status TEXT, price_paid REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (email TEXT PRIMARY KEY, password TEXT, name TEXT, 
                      status TEXT DEFAULT 'Active', security_q TEXT, security_a TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS products 
                     (name TEXT PRIMARY KEY, price REAL, description TEXT)''')
        conn.commit()

init_db()

# ==========================================
# 2. CORE UTILITIES
# ==========================================
def generate_pdf_receipt(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, COMPANY_NAME, 0, 1, 'C')
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(100, 10, f"Receipt ID: {row['id']}", 0, 1)
    pdf.cell(100, 10, f"Customer: {row['cust_email']}", 0, 1)
    pdf.cell(100, 10, f"Product: {row['product']}", 0, 1)
    pdf.cell(100, 10, f"Amount Paid: N{row['price_paid']:,.2f}", 0, 1)
    pdf.cell(100, 10, f"Date: {row['p_date']}", 0, 1)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 3. INTERFACE LOGIC
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})

if st.session_state['auth']:
    st.sidebar.title(f"👋 Welcome, {st.session_state.get('name', 'User')}")
    st.sidebar.write(f"ID: {st.session_state['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.update({'auth': False, 'admin': False})
        st.rerun()

if not st.session_state['auth']:
    st.title(f"💎 {COMPANY_NAME}")
    t = st.tabs(["Login", "Register", "Reset Password", "Admin"])
    
    with t[0]:
        e_in = st.text_input("Email", key="l_e").lower().strip()
        p_in = st.text_input("Password", type="password", key="l_p")
        if st.button("Access Portal"):
            with get_connection() as conn:
                u = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (e_in, p_in)).fetchone()
                if u:
                    if u[3] == 'Banned': st.error("🚫 Account Banned.")
                    else:
                        st.session_state.update({'auth':True, 'email':e_in, 'name':u[2], 'admin':False})
                        st.rerun()
                else: st.error("Login Failed.")

    with t[1]:
        st.subheader("New Registration")
        n_reg = st.text_input("Full Name")
        em_reg = st.text_input("Email").lower().strip()
        pw_reg = st.text_input("Password", type="password")
        sq = st.selectbox("Security Question", ["First pet's name", "High school name", "Favorite food"])
        sa = st.text_input("Answer")
        if st.button("Create Profile"):
            try:
                with get_connection() as conn:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (em_reg, pw_reg, n_reg, 'Active', sq, sa.lower()))
                    conn.commit()
                st.success("Success! Please Login.")
            except: st.error("Email taken.")

    with t[2]:
        st.subheader("Account Recovery")
        re_e = st.text_input("Your Email", key="rec_e").lower().strip()
        if re_e:
            with get_connection() as conn:
                u = conn.execute("SELECT security_q FROM users WHERE email=?", (re_e,)).fetchone()
                if u:
                    st.info(f"Question: {u[0]}")
                    ans = st.text_input("Answer", key="rec_a").lower().strip()
                    new_p = st.text_input("New Pass", type="password")
                    if st.button("Reset Now"):
                        check = conn.execute("SELECT * FROM users WHERE email=? AND security_a=?", (re_e, ans)).fetchone()
                        if check:
                            conn.execute("UPDATE users SET password=? WHERE email=?", (new_p, re_e))
                            conn.commit(); st.success("Updated! Login now.")
                        else: st.error("Wrong Answer.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD:
                st.session_state.update({'auth':True, 'admin':True, 'name':'Boss', 'email':'Admin'})
                st.rerun()

else:
    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Mgr", "👥 User Mgmt", "📋 Inventory & Tracking", "📊 Reports", "💾 Backup"])
        
        with adm[2]:
            st.header("Manage Customers")
            with get_connection() as conn:
                u_df = pd.read_sql("SELECT name, email, status FROM users", conn)
                st.table(u_df)
                t_user = st.text_input("Enter Email to Ban/Delete")
                c1, c2 = st.columns(2)
                if c1.button("Ban/Unban"):
                    curr = conn.execute("SELECT status FROM users WHERE email=?", (t_user,)).fetchone()
                    if curr:
                        ns = 'Banned' if curr[0] == 'Active' else 'Active'
                        conn.execute("UPDATE users SET status=? WHERE email=?", (ns, t_user))
                        conn.commit(); st.rerun()
                if c2.button("Delete Permanently"):
                    conn.execute("DELETE FROM users WHERE email=?", (t_user,))
                    conn.commit(); st.rerun()

        with adm[3]:
            st.header("Inventory & Receipt Generation")
            with get_connection() as conn:
                df = pd.read_sql("SELECT * FROM sales", conn)
            if not df.empty:
                st.dataframe(df)
                r_id = st.number_input("ID for Receipt", min_value=1)
                if st.button("Generate PDF Receipt"):
                    row = df[df['id'] == r_id].to_dict('records')[0]
                    st.download_button("Download Receipt", generate_pdf_receipt(row), f"Receipt_{r_id}.pdf")
            
        with adm[5]:
            st.header("Data Insurance")
            with get_connection() as conn:
                full_df = pd.read_sql("SELECT * FROM sales", conn)
            st.download_button("Download CSV Backup", full_df.to_csv(index=False).encode('utf-8'), "backup.csv")
            up = st.file_uploader("Upload Backup", type="csv")
            if up and st.button("Restore"):
                res_df = pd.read_csv(up)
                res_df.to_sql('sales', get_connection(), if_exists='append', index=False)
                st.success("Restored!")

    else:
        # CUSTOMER PORTAL
        ct = st.tabs(["🔓 My Tools", "🛒 Store", "💬 Support"])
        with ct[1]:
            with get_connection() as conn:
                p_df = pd.read_sql("SELECT * FROM products", conn)
            for _, r in p_df.iterrows():
                st.subheader(f"{r['name']} — N{r['price']:,.0f}")
                txt = urllib.parse.quote(f"Buy {r['name']}. Email: {st.session_state['email']}")
                st.link_button("Order via WhatsApp", f"https://wa.me/{MY_WHATSAPP}?text={txt}")
