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

# CRITICAL: Replace these with your actual details
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx" # 16-character App Password

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
        st.error(f"Mail Error: {e}") # This shows the error in the app for debugging
        return False

# ==========================================
# 3. INTERFACE
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': "", 'otp': None, 'otp_email': ""})

# --- SIDEBAR WELCOME NOTE ---
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
                else: st.error("Invalid Login.")

    with t[1]:
        n_reg = st.text_input("Full Name", key="s_n")
        em_reg = st.text_input("Email", key="s_e").lower().strip()
        pw_reg = st.text_input("Password", type="password", key="s_p")
        if st.button("Create Profile"):
            try:
                with get_connection() as conn:
                    conn.execute("INSERT INTO users (email, password, name) VALUES (?,?,?)", (em_reg, pw_reg, n_reg))
                    conn.commit()
                st.success("Registration Successful! Now go to the Login tab.")
            except: st.error("Email already taken.")

    with t[2]:
        re_e = st.text_input("Enter Registered Email", key="recovery_email").lower().strip()
        if st.button("Send OTP Code"):
            with get_connection() as conn:
                u = conn.execute("SELECT * FROM users WHERE email=?", (re_e,)).fetchone()
                if u:
                    otp = str(random.randint(1000, 9999))
                    st.session_state.update({'otp': otp, 'otp_email': re_e})
                    if send_automated_email(re_e, "Your OTP Code", f"Your Kelly AI Recovery code is: {otp}"):
                        st.success("OTP sent! Check your email inbox.")
                else: st.error("Email not found.")
        
        input_otp = st.text_input("Enter 4-Digit Code", key="otp_in")
        new_pw = st.text_input("New Password", type="password", key="otp_new_pw")
        if st.button("Verify & Reset"):
            if st.session_state['otp'] and input_otp == st.session_state['otp']:
                with get_connection() as conn:
                    conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_e))
                    conn.commit()
                st.success("Reset Complete! Go to Login.")
            else: st.error("Invalid Code.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin Dashboard"):
            if ak == ADMIN_PASSWORD: 
                st.session_state.update({'auth':True, 'admin':True, 'email': 'Admin', 'name': 'Admin'})
                st.rerun()

# --- LOGGED IN CONTENT ---
else:
    if st.session_state['admin']:
        # [Admin Tabs: Delivery, Manager, Users, Inventory, Revenue]
        st.title("Admin Dashboard")
        st.write("Manage your business tools and customers below.")
        # (Include the logic for your Admin tabs here...)
    else:
        # --- CUSTOMER PORTAL ---
        c_tabs = st.tabs(["🔓 My Accounts", "🛒 Marketplace", "💬 Support"])
        
        with c_tabs[0]:
            st.header("Your Active Subscriptions")
            # Logic to pull from sales where cust_email = session_state['email']
        
        with c_tabs[1]:
            st.header("Marketplace")
            # Logic to show products and WhatsApp buy buttons
            
        with c_tabs[2]:
            st.header("Customer Support")
            st.write("WhatsApp: 07060911547")
            st.link_button("Chat with Support", f"https://wa.me/{MY_WHATSAPP}")
