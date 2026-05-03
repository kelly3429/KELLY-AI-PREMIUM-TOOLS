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

# CRITICAL: Put your 16-character Google App Password here
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx" 

def get_connection():
    # Standardized database name
    return sqlite3.connect('kelly_ai_master_v3.db', check_same_thread=False)

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
# 3. INTERFACE LOGIC
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': "", 'otp': None, 'otp_email': ""})

# --- SIDEBAR WELCOME ---
if st.session_state['auth']:
    st.sidebar.title(f"👋 Welcome, {st.session_state.get('name', 'User')}")
    st.sidebar.write(f"Logged in as: **{st.session_state['email']}**")
    st.sidebar.write("---")
    if st.sidebar.button("Logout"):
        st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})
        st.rerun()

# --- LOGIN / SIGNUP SCREEN ---
if not st.session_state['auth']:
    st.title(f"💎 {COMPANY_NAME}")
    t = st.tabs(["Login", "Register", "Forgot Password", "Admin"])
    
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
                else: st.error("Login Failed. Check details or Register.")

    with t[1]:
        n_reg = st.text_input("Full Name")
        em_reg = st.text_input("Email").lower().strip()
        pw_reg = st.text_input("Password", type="password")
        if st.button("Create Profile"):
            try:
                with get_connection() as conn:
                    conn.execute("INSERT INTO users (email, password, name) VALUES (?,?,?)", (em_reg, pw_reg, n_reg))
                    conn.commit()
                st.success("Registration Successful! Now go to Login.")
            except: st.error("Email already exists.")

    with t[2]:
        re_e = st.text_input("Enter Registered Email", key="rec_e").lower().strip()
        if st.button("Send OTP Code"):
            with get_connection() as conn:
                user_exists = conn.execute("SELECT * FROM users WHERE email=?", (re_e,)).fetchone()
                if user_exists:
                    otp = str(random.randint(1000, 9999))
                    st.session_state.update({'otp': otp, 'otp_email': re_e})
                    send_automated_email(re_e, "Your Recovery Code", f"Your code is: {otp}")
                    st.success("OTP sent! Check your inbox.")
                else: st.error("Email not found.")
        
        in_otp = st.text_input("Enter 4-Digit OTP")
        new_pw = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            if in_otp == st.session_state.get('otp'):
                with get_connection() as conn:
                    conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_e))
                    conn.commit()
                st.success("Success! Please Login.")
            else: st.error("Invalid Code.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD: 
                st.session_state.update({'auth':True, 'admin':True, 'email': 'Admin', 'name': 'Boss'})
                st.rerun()

# --- LOGGED IN AREA ---
else:
    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Manager", "👥 Users", "📋 Inventory", "📊 Revenue", "💾 Data Insurance"])
        
        with adm[0]:
            st.header("New Order Delivery")
            with get_connection() as conn:
                tools = [r[0] for r in conn.execute("SELECT name FROM products").fetchall()]
            with st.form("d_form", clear_on_submit=True):
                c_mail = st.text_input("Customer Email")
                tool = st.selectbox("Tool", tools if tools else ["Add tools in Manager first"])
                p_l = st.text_input("Premium Login")
                p_p = st.text_input("Premium Pass")
                price = st.number_input("Sold Price (NGN)")
                cost = st.number_input("Cost (USD)")
                rate = st.number_input("Rate", value=1550.0)
                vend = st.text_input("Vendor")
                oid = st.text_input("Order Number")
                if st.form_submit_button("Deliver & Save"):
                    prof = price - (cost * rate)
                    exp = (datetime.now() + timedelta(days=30)).date()
                    with get_connection() as conn:
                        conn.execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status, price_paid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (c_mail, tool, p_l, p_p, prof, datetime.now().date(), exp, oid, vend, "Active", price))
                        conn.commit()
                    send_automated_email(c_mail, "Account Ready!", f"Tool: {tool}\nLogin: {p_l}\nPass: {p_p}\nExpires: {exp}")
                    st.success("Delivered!")

        with adm[1]:
            st.header("Tool Manager")
            with st.form("tool_mgr"):
                tn = st.text_input("Product Name")
                tp = st.number_input("Price (NGN)")
                td = st.text_area("Short Description")
                if st.form_submit_button("Update Store"):
                    with get_connection() as conn:
                        conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?)", (tn, tp, td))
                        conn.commit()
                    st.success("Store Updated!")

        with adm[5]:
            st.header("Backup & Restore")
            with get_connection() as conn:
                full_df = pd.read_sql("SELECT * FROM sales", conn)
            st.download_button("💾 Download Backup", full_df.to_csv(index=False).encode('utf-8'), "kelly_backup.csv")
            
            up = st.file_uploader("Restore Data", type="csv")
            if up and st.button("Run Restore"):
                res_df = pd.read_csv(up)
                res_df.to_sql('sales', get_connection(), if_exists='append', index=False)
                st.success("Data Restored!")

    else:
        # --- CUSTOMER PORTAL ---
        c_tabs = st.tabs(["🔓 My Tools", "🛒 Store", "💬 Support"])
        
        with c_tabs[0]:
            st.header("Your Active Premium Tools")
            with get_connection() as conn:
                my_df = pd.read_sql(f"SELECT * FROM sales WHERE cust_email='{st.session_state['email']}'", conn)
            if not my_df.empty:
                for _, r in my_df.iterrows():
                    with st.expander(f"⭐ {r['product']} (Expires: {r['e_date']})"):
                        st.code(f"Email: {r['p_login']}\nPassword: {r['p_pass']}")
                        st.write(f"Status: **{r['status']}**")
            else:
                st.info("You haven't purchased any tools yet. Visit the Store!")

        with c_tabs[1]:
            st.header("Marketplace")
            with get_connection() as conn:
                p_df = pd.read_sql("SELECT * FROM products", conn)
            if not p_df.empty:
                for _, r in p_df.iterrows():
                    st.subheader(f"{r['name']} — N{r['price']:,.0f}")
                    st.write(r['description'])
                    txt = urllib.parse.quote(f"Hello, I want to buy {r['name']} for N{r['price']}. My email is {st.session_state['email']}")
                    st.link_button("Order via WhatsApp", f"https://wa.me/{MY_WHATSAPP}?text={txt}")
                    st.divider()
            else:
                st.info("The store is currently empty.")

        with c_tabs[2]:
            st.header("Contact Support")
            st.write("WhatsApp: 07060911547")
            st.link_button("Chat on WhatsApp", f"https://wa.me/{MY_WHATSAPP}")
            st.link_button("Telegram Group", "https://t.me/kelly_ai_tools")
