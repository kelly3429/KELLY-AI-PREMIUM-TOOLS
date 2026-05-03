import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
import random
from email.message import EmailMessage
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION & DATABASE (v30)
# ==========================================
COMPANY_NAME = "Kelly AI Premium Tools"
ADMIN_PASSWORD = "Kelly500#"
MY_WHATSAPP = "2347060911547"

# EMAIL CONFIG - Replace with your Gmail App Password
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "your_app_password" 

def get_connection():
    return sqlite3.connect('kelly_ai_v30.db', check_same_thread=False)

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sales 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, cust_email TEXT, product TEXT, 
                      p_login TEXT, p_pass TEXT, profit REAL, p_date DATE, e_date DATE, 
                      order_id TEXT, vendor TEXT, status TEXT, price_paid REAL)''')
        # Added 'status' column to users to handle Banning (Active vs Banned)
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (email TEXT PRIMARY KEY, password TEXT, name TEXT, status TEXT DEFAULT 'Active')''')
        c.execute('''CREATE TABLE IF NOT EXISTS products 
                     (name TEXT PRIMARY KEY, price REAL, description TEXT)''')
        conn.commit()

init_db()

# ==========================================
# 2. CORE UTILITIES
# ==========================================
def send_automated_email(to_email, subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(body)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except: return False

# ==========================================
# 3. INTERFACE
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': "", 'otp': None, 'otp_email': ""})

if not st.session_state['auth']:
    st.title(f"💎 {COMPANY_NAME}")
    t = st.tabs(["Login", "Register", "Forgot Password (OTP)", "Admin"])
    
    with t[0]:
        e_in = st.text_input("Email", key="l_e").lower().strip()
        p_in = st.text_input("Password", type="password", key="l_p")
        if st.button("Access Portal"):
            with get_connection() as conn:
                u = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (e_in, p_in)).fetchone()
                if u: 
                    if u[3] == 'Banned':
                        st.error("🚫 Your account has been banned. Please contact support.")
                    else:
                        st.session_state.update({'auth':True, 'email':e_in, 'name':u[2], 'admin':False})
                        st.rerun()
                else: st.error("Login Failed. Email or Password incorrect.")

    with t[1]:
        n_reg = st.text_input("Full Name", key="s_n")
        em_reg = st.text_input("Email Address", key="s_e").lower().strip()
        pw_reg = st.text_input("Create Password", type="password", key="s_p")
        if st.button("Create Profile"):
            try:
                with get_connection() as conn:
                    conn.execute("INSERT INTO users (email, password, name) VALUES (?,?,?)", (em_reg, pw_reg, n_reg))
                    conn.commit()
                st.success("Registration Successful! Now go to the Login tab.")
            except: st.error("Email is already taken.")

    with t[2]:
        st.subheader("Password Recovery via OTP")
        re_e = st.text_input("Enter Registered Email", key="recovery_email").lower().strip()
        if st.button("Send OTP Code"):
            with get_connection() as conn:
                u = conn.execute("SELECT * FROM users WHERE email=?", (re_e,)).fetchone()
                if u:
                    otp = str(random.randint(1000, 9999))
                    st.session_state.update({'otp': otp, 'otp_email': re_e})
                    send_automated_email(re_e, "Your OTP Code", f"Your Kelly AI Recovery code is: {otp}")
                    st.success("OTP sent to your email!")
                else: st.error("Email not found.")
        
        input_otp = st.text_input("Enter 4-Digit Code", key="otp_in")
        new_pw = st.text_input("New Password", type="password", key="otp_new_pw")
        if st.button("Verify & Reset"):
            if input_otp == st.session_state.get('otp') and st.session_state.get('otp_email') == re_e:
                with get_connection() as conn:
                    conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_e))
                    conn.commit()
                st.success("Password Updated! Please go to Login.")
            else: st.error("Invalid Code or Email.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD: 
                st.session_state.update({'auth':True, 'admin':True})
                st.rerun()

else:
    # --- AUTHENTICATED AREA ---
    st.sidebar.title(f"Hello, {st.session_state.get('name', 'Admin')}")
    if st.sidebar.button("Logout"): 
        st.session_state.update({'auth':False, 'admin':False})
        st.rerun()

    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Manager", "👥 User Management", "📋 Inventory", "📊 Revenue"])
        
        with adm[2]:
            st.header("Manage Customers")
            with get_connection() as conn:
                users_df = pd.read_sql("SELECT name, email, status FROM users", conn)
                st.dataframe(users_df, use_container_width=True)
                
                st.divider()
                target_user = st.text_input("Enter User Email to Action")
                action_col1, action_col2 = st.columns(2)
                
                if action_col1.button("🚫 Ban/Unban User"):
                    current_status = conn.execute("SELECT status FROM users WHERE email=?", (target_user,)).fetchone()
                    if current_status:
                        new_status = 'Banned' if current_status[0] == 'Active' else 'Active'
                        conn.execute("UPDATE users SET status=? WHERE email=?", (new_status, target_user))
                        conn.commit()
                        st.success(f"User is now {new_status}")
                        st.rerun()
                
                if action_col2.button("🗑️ Delete User Permanently"):
                    conn.execute("DELETE FROM users WHERE email=?", (target_user,))
                    conn.commit()
                    st.success("User deleted from database.")
                    st.rerun()

        with adm[0]:
            # [Previous Delivery Tab Logic Here]
            st.header("New Order Delivery")
            with st.form("d_form", clear_on_submit=True):
                with get_connection() as conn:
                    tools = [r[0] for r in conn.execute("SELECT name FROM products").fetchall()]
                
                col1, col2 = st.columns(2)
                with col1:
                    c_mail = st.text_input("Customer Registered Email")
                    tool = st.selectbox("Select Tool", tools if tools else ["Set tools in Manager first"])
                    p_mail = st.text_input("Premium Login Email")
                    p_pass = st.text_input("Premium Login Password")
                    p_date = st.date_input("Purchase Date", datetime.now())
                with col2:
                    v_name = st.text_input("G2G Vendor Name")
                    o_id = st.text_input("G2G Order Number")
                    n_paid = st.number_input("Amount Paid (NGN)")
                    u_cost = st.number_input("Cost (USD)")
                    rate = st.number_input("Exchange Rate", value=1550.0)
                
                if st.form_submit_button("Deliver & Save"):
                    prof = n_paid - (u_cost * rate)
                    e_date = p_date + timedelta(days=30)
                    with get_connection() as conn:
                        conn.execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status, price_paid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (c_mail, tool, p_mail, p_pass, prof, p_date, e_date, o_id, v_name, "Active", n_paid))
                        conn.commit()
                    send_automated_email(c_mail, "Your Account is Ready!", f"Tool: {tool}\nLogin: {p_mail}\nPass: {p_pass}\nExpires: {e_date}")
                    st.success("Delivery Successful!")

        with adm[1]:
            # [Tool Manager Tab Logic Here]
            st.header("Tool Manager")
            with st.form("p_mgr"):
                pn = st.text_input("New Tool Name")
                pp = st.number_input("Tool Price (NGN)")
                pd = st.text_area("Description / Features")
                if st.form_submit_button("Add/Update Tool"):
                    with get_connection() as conn:
                        conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?)", (pn, pp, pd))
                        conn.commit()
                    st.success("Marketplace Updated!")

    else:
        # --- CUSTOMER PORTAL ---
        c_tabs = st.tabs(["🔓 My Accounts", "🛒 Marketplace", "💬 Support"])
        with c_tabs[0]:
            with get_connection() as conn:
                my_tools = pd.read_sql(f"SELECT * FROM sales WHERE cust_email='{st.session_state['email']}'", conn)
            if not my_tools.empty:
                for _, r in my_tools.iterrows():
                    with st.expander(f"⭐ {r['product']} (Exp: {r['e_date']})"):
                        st.code(f"Email: {r['p_login']}\nPass: {r['p_pass']}")
            else: st.info("No active accounts.")
