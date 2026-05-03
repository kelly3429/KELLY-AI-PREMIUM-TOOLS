import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
import random
from email.message import EmailMessage
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION & DATABASE
# ==========================================
COMPANY_NAME = "Kelly AI Premium Tools"
ADMIN_PASSWORD = "Kelly500#"
MY_WHATSAPP = "2347060911547"

# EMAIL CONFIG - YOU MUST GENERATE A GMAIL "APP PASSWORD"
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "your_app_password" 

def get_connection():
    return sqlite3.connect('kelly_ai_final.db', check_same_thread=False)

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
# 2. CORE UTILITIES (Email & Logic)
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
                    if u[3] == 'Banned': st.error("🚫 Account Banned.")
                    else:
                        st.session_state.update({'auth':True, 'email':e_in, 'name':u[2], 'admin':False})
                        st.rerun()
                else: st.error("Login Failed.")

    with t[1]:
        n_reg = st.text_input("Full Name", key="s_n")
        em_reg = st.text_input("Email Address", key="s_e").lower().strip()
        pw_reg = st.text_input("Create Password", type="password", key="s_p")
        if st.button("Create Profile"):
            try:
                with get_connection() as conn:
                    conn.execute("INSERT INTO users (email, password, name) VALUES (?,?,?)", (em_reg, pw_reg, n_reg))
                    conn.commit()
                st.success("Account Created! Use the Login tab.")
            except: st.error("Email already taken.")

    with t[2]:
        re_e = st.text_input("Registered Email", key="recovery_email").lower().strip()
        if st.button("Send OTP Code"):
            with get_connection() as conn:
                u = conn.execute("SELECT * FROM users WHERE email=?", (re_e,)).fetchone()
                if u:
                    otp = str(random.randint(1000, 9999))
                    st.session_state.update({'otp': otp, 'otp_email': re_e})
                    if send_automated_email(re_e, "Your OTP Code", f"Your Kelly AI Recovery code is: {otp}"):
                        st.success("OTP sent! Check your inbox.")
                else: st.error("Email not found.")
        
        input_otp = st.text_input("Enter 4-Digit Code", key="otp_in")
        new_pw = st.text_input("New Password", type="password", key="otp_new_pw")
        if st.button("Verify & Reset"):
            if input_otp == st.session_state.get('otp'):
                with get_connection() as conn:
                    conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_e))
                    conn.commit()
                st.success("Reset Complete!")
            else: st.error("Invalid Code.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD: 
                st.session_state.update({'auth':True, 'admin':True})
                st.rerun()

else:
    # --- AUTHENTICATED AREA ---
    if st.sidebar.button("Logout"): 
        st.session_state.update({'auth':False, 'admin':False})
        st.rerun()

    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Manager", "👥 Users", "📋 Inventory"])
        with adm[2]: # User Management
            with get_connection() as conn:
                users_df = pd.read_sql("SELECT name, email, status FROM users", conn)
                st.table(users_df)
                target = st.text_input("User Email for Action")
                if st.button("Ban/Unban"):
                    curr = conn.execute("SELECT status FROM users WHERE email=?", (target,)).fetchone()
                    if curr:
                        new_s = 'Banned' if curr[0] == 'Active' else 'Active'
                        conn.execute("UPDATE users SET status=? WHERE email=?", (new_s, target))
                        conn.commit(); st.rerun()
        # [Delivery and Tool Manager tabs remain as previous logic]

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

        with c_tabs[1]:
            with get_connection() as conn:
                p_df = pd.read_sql_query("SELECT * FROM products", conn)
            for _, r in p_df.iterrows():
                st.write(f"### {r['name']} — N{r['price']:,.0f}")
                txt = urllib.parse.quote(f"Buy {r['name']} for N{r['price']}. Email: {st.session_state['email']}")
                st.link_button("Buy via WhatsApp", f"https://wa.me/{MY_WHATSAPP}?text={txt}")
                st.divider()

        with c_tabs[2]:
            st.header("Need Support?")
            st.write("Our team is available 24/7 to help you.")
            st.link_button("Chat with Us on WhatsApp", f"https://wa.me/{MY_WHATSAPP}")
            st.link_button("Join Telegram Community", "https://t.me/kelly_ai_tools")
