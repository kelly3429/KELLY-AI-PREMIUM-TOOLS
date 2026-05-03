import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
import random
from email.message import EmailMessage
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION
# ==========================================
COMPANY_NAME = "Kelly AI Premium Tools"
ADMIN_PASSWORD = "Kelly500#"
MY_WHATSAPP = "2347060911547"

# EMAIL CONFIG - Get your 16-character App Password from Google
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx" 

def get_connection():
    # Standardizing on ONE database name to stop losing users
    return sqlite3.connect('kelly_ai_final_master.db', check_same_thread=False)

def init_db():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sales 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, cust_email TEXT, product TEXT, 
                      p_login TEXT, p_pass TEXT, profit REAL, p_date DATE, e_date DATE, 
                      order_id TEXT, vendor TEXT, status TEXT, price_paid REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (email TEXT PRIMARY KEY, password TEXT, name TEXT, status TEXT DEFAULT 'Active')''')
        c.execute('''CREATE TABLE IF NOT EXISTS products 
                     (name TEXT PRIMARY KEY, price REAL, description TEXT)''')
        conn.commit()

init_db()

# ==========================================
# 2. EMAIL ENGINE
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
    except Exception as e:
        st.sidebar.error(f"Mail Error: {e}")
        return False

# ==========================================
# 3. INTERFACE
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

# Initializing Session States
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': "", 'otp': None, 'otp_email': ""})

# --- SIDEBAR WELCOME NOTE ---
if st.session_state['auth']:
    st.sidebar.title(f"👋 Welcome, {st.session_state.get('name', 'User')}")
    st.sidebar.write(f"Logged in as: **{st.session_state['email']}**")
    st.sidebar.info("Glad to have you back at Kelly AI Premium Tools!")
    st.sidebar.write("---")
    if st.sidebar.button("Logout"):
        st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': "", 'otp': None})
        st.rerun()

# --- LOGIN / SIGNUP SCREEN ---
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
                    if u[3] == 'Banned': st.error("🚫 Your account is banned.")
                    else:
                        st.session_state.update({'auth':True, 'email':e_in, 'name':u[2], 'admin':False})
                        st.rerun()
                else: st.error("Invalid Login. Please Register if you haven't.")

    with t[1]:
        n_reg = st.text_input("Full Name", key="s_n")
        em_reg = st.text_input("Email", key="s_e").lower().strip()
        pw_reg = st.text_input("Password", type="password", key="s_p")
        if st.button("Create Profile"):
            if not n_reg or not em_reg or not pw_reg:
                st.warning("Please fill all fields.")
            else:
                try:
                    with get_connection() as conn:
                        conn.execute("INSERT INTO users (email, password, name) VALUES (?,?,?)", (em_reg, pw_reg, n_reg))
                        conn.commit()
                    st.success("Profile Created! You can now switch to the Login tab.")
                except: st.error("Email already taken.")

    with t[2]:
        re_e = st.text_input("Enter Registered Email", key="recovery_email").lower().strip()
        if st.button("Send OTP Code"):
            with get_connection() as conn:
                u = conn.execute("SELECT * FROM users WHERE email=?", (re_e,)).fetchone()
                if u:
                    otp_val = str(random.randint(1000, 9999))
                    st.session_state.update({'otp': otp_val, 'otp_email': re_e})
                    if send_automated_email(re_e, "Security Code", f"Your recovery code is: {otp_val}"):
                        st.success("OTP sent! Check your inbox.")
                else: st.error("Email not found.")
        
        input_otp = st.text_input("Enter 4-Digit Code", key="otp_in")
        new_pw = st.text_input("New Password", type="password", key="otp_new_pw")
        if st.button("Verify & Reset"):
            if st.session_state['otp'] and input_otp == st.session_state['otp']:
                with get_connection() as conn:
                    conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_e))
                    conn.commit()
                st.success("Password Updated! Go to Login.")
            else: st.error("Invalid Code.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin Dashboard"):
            if ak == ADMIN_PASSWORD: 
                st.session_state.update({'auth':True, 'admin':True, 'email': 'Admin', 'name': 'Boss'})
                st.rerun()

# --- LOGGED IN CONTENT ---
else:
    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Manager", "👥 Users", "📋 Inventory"])
        with adm[0]:
            st.header("New Order Delivery")
            # Pull dynamic tools
            with get_connection() as conn:
                tools = [r[0] for r in conn.execute("SELECT name FROM products").fetchall()]
            
            with st.form("d_form"):
                c_mail = st.text_input("Customer Email")
                tool = st.selectbox("Tool", tools if tools else ["Add tools in Manager first"])
                p_mail = st.text_input("Premium Login")
                p_pass = st.text_input("Premium Password")
                price = st.number_input("Sold Price (NGN)")
                cost = st.number_input("Cost (USD)")
                rate = st.number_input("Rate", value=1550.0)
                vendor = st.text_input("Vendor")
                order = st.text_input("Order ID")
                if st.form_submit_button("Deliver"):
                    prof = price - (cost * rate)
                    exp = (datetime.now() + timedelta(days=30)).date()
                    with get_connection() as conn:
                        conn.execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status, price_paid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (c_mail, tool, p_mail, p_pass, prof, datetime.now().date(), exp, order, vendor, "Active", price))
                        conn.commit()
                    send_automated_email(c_mail, "Account Ready", f"Login: {p_mail}\nPass: {p_pass}\nExpires: {exp}")
                    st.success("Delivered!")
        # (Other Admin tabs remain same...)
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
            else: st.info("No active accounts. Go to Marketplace!")
            
        with c_tabs[1]:
            with get_connection() as conn:
                p_df = pd.read_sql("SELECT * FROM products", conn)
            for _, r in p_df.iterrows():
                st.write(f"### {r['name']} — N{r['price']:,.0f}")
                txt = urllib.parse.quote(f"Buy {r['name']} for N{r['price']}. Email: {st.session_state['email']}")
                st.link_button("Buy via WhatsApp", f"https://wa.me/{MY_WHATSAPP}?text={txt}")
                st.divider()
                
        with c_tabs[2]:
            st.header("Support")
            st.link_button("WhatsApp Support", f"https://wa.me/{MY_WHATSAPP}")
