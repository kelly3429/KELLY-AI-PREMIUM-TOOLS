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

# EMAIL CONFIG - Replace with your 16-character App Password
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx" 

def get_connection():
    return sqlite3.connect('kelly_ai_final_v2.db', check_same_thread=False)

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
    except Exception as e:
        st.error(f"Mail Error: {e}")
        return False

# ==========================================
# 3. INTERFACE
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': "", 'otp': None, 'otp_email': ""})

# SIDEBAR
if st.session_state['auth']:
    st.sidebar.title(f"👋 Welcome, {st.session_state.get('name', 'User')}")
    st.sidebar.write(f"Account: **{st.session_state['email']}**")
    st.sidebar.info(f"Glad to have you back at {COMPANY_NAME}!")
    if st.sidebar.button("Logout"):
        st.session_state.update({'auth': False, 'admin': False})
        st.rerun()

# LOGIN SCREEN
if not st.session_state['auth']:
    st.title(f"💎 {COMPANY_NAME}")
    t = st.tabs(["Login", "Register", "Forgot Password", "Admin"])
    
    with t[0]:
        e_in = st.text_input("Email", key="login_e").lower().strip()
        p_in = st.text_input("Password", type="password", key="login_p")
        if st.button("Access Portal"):
            with get_connection() as conn:
                u = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (e_in, p_in)).fetchone()
                if u:
                    if u[3] == 'Banned': st.error("🚫 Account Banned.")
                    else:
                        st.session_state.update({'auth':True, 'email':e_in, 'name':u[2], 'admin':False})
                        st.rerun()
                else: st.error("Invalid Login. Please ensure you have registered.")

    with t[1]:
        n_reg = st.text_input("Full Name")
        em_reg = st.text_input("Email Address").lower().strip()
        pw_reg = st.text_input("Create Password", type="password")
        if st.button("Create Profile"):
            try:
                with get_connection() as conn:
                    conn.execute("INSERT INTO users (email, password, name) VALUES (?,?,?)", (em_reg, pw_reg, n_reg))
                    conn.commit()
                st.success("Registration Successful! Now go to the Login tab.")
            except: st.error("Email taken.")

    with t[2]:
        re_e = st.text_input("Registered Email").lower().strip()
        if st.button("Send OTP"):
            with get_connection() as conn:
                u = conn.execute("SELECT * FROM users WHERE email=?", (re_e,)).fetchone()
                if u:
                    otp = str(random.randint(1000, 9999))
                    st.session_state.update({'otp': otp, 'otp_email': re_e})
                    send_automated_email(re_e, "Your OTP Code", f"Code: {otp}")
                    st.success("Check your email!")
        
        in_otp = st.text_input("OTP Code")
        new_pw = st.text_input("New Password", type="password")
        if st.button("Reset"):
            if in_otp == st.session_state.get('otp'):
                with get_connection() as conn:
                    conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_e))
                    conn.commit()
                st.success("Updated!")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD:
                st.session_state.update({'auth':True, 'admin':True, 'name':'Admin', 'email':'Admin'})
                st.rerun()

else:
    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Manager", "👥 Users", "📋 Inventory", "📊 Revenue", "💾 Backup"])
        
        with adm[0]:
            st.header("Deliver Order")
            with get_connection() as conn:
                tools = [r[0] for r in conn.execute("SELECT name FROM products").fetchall()]
            with st.form("deliv"):
                c_mail = st.text_input("Customer Email")
                tool = st.selectbox("Tool", tools if tools else ["Add tools in Manager first"])
                p_l = st.text_input("Premium Login")
                p_p = st.text_input("Premium Pass")
                price = st.number_input("Sold Price")
                cost = st.number_input("Cost (USD)")
                rate = st.number_input("Rate", value=1550.0)
                vend = st.text_input("Vendor")
                oid = st.text_input("Order ID")
                if st.form_submit_button("Deliver"):
                    prof = price - (cost * rate)
                    exp = (datetime.now() + timedelta(days=30)).date()
                    with get_connection() as conn:
                        conn.execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status, price_paid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (c_mail, tool, p_l, p_p, prof, datetime.now().date(), exp, oid, vend, "Active", price))
                        conn.commit()
                    send_automated_email(c_mail, "Tool Ready", f"Login: {p_l}\nPass: {p_p}")
                    st.success("Delivered!")

        with adm[1]:
            st.header("Manage Tools")
            with st.form("tools"):
                tn = st.text_input("Tool Name")
                tp = st.number_input("Price")
                td = st.text_area("Desc")
                if st.form_submit_button("Save Tool"):
                    with get_connection() as conn:
                        conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?)", (tn, tp, td))
                        conn.commit()
                    st.success("Tool Added!")

        with adm[2]:
            st.header("Users")
            with get_connection() as conn:
                u_df = pd.read_sql("SELECT name, email, status FROM users", conn)
            st.table(u_df)
            target = st.text_input("User Email")
            if st.button("Ban/Unban"):
                with get_connection() as conn:
                    curr = conn.execute("SELECT status FROM users WHERE email=?", (target,)).fetchone()
                    if curr:
                        ns = 'Banned' if curr[0] == 'Active' else 'Active'
                        conn.execute("UPDATE users SET status=? WHERE email=?", (ns, target))
                        conn.commit()
                        st.rerun()

        with adm[3]:
            st.header("Inventory")
            with get_connection() as conn:
                df = pd.read_sql("SELECT * FROM sales", conn)
            st.dataframe(df)

        with adm[4]:
            st.header("Revenue")
            with get_connection() as conn:
                df = pd.read_sql("SELECT profit, p_date FROM sales", conn)
            if not df.empty:
                st.metric("Total Profit", f"N{df['profit'].sum():,.2f}")
                st.bar_chart(df.set_index('p_date'))

    else:
        # CUSTOMER
        ct = st.tabs(["🔓 My Tools", "🛒 Store", "💬 Support"])
        with ct[1]:
            with get_connection() as conn:
                p_df = pd.read_sql("SELECT * FROM products", conn)
            for _, r in p_df.iterrows():
                st.write(f"### {r['name']} - N{r['price']:,.0f}")
                msg = urllib.parse.quote(f"I want to buy {r['name']}. Email: {st.session_state['email']}")
                st.link_button("Buy Now", f"https://wa.me/{MY_WHATSAPP}?text={msg}")
