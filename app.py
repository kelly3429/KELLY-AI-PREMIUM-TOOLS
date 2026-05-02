import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import webbrowser
from email.message import EmailMessage
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION (REQUIRED)
# ==========================================
# IMPORTANT: You must generate a "Gmail App Password" to send emails
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "your_app_password" 
WHATSAPP_LINK = "https://wa.me/234XXXXXXXXXX" # Replace with your number

@st.cache_resource
def get_connection():
    conn = sqlite3.connect('kelly_ai_pro_v20.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table for Sales & Product Logins
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  cust_email TEXT, cust_name TEXT, product TEXT, 
                  p_login TEXT, p_pass TEXT, profit REAL, 
                  p_date DATE, e_date DATE, order_id TEXT, status TEXT)''')
    # Table for Customer Portal Logins
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    conn.commit()

init_db()

# ==========================================
# 2. THE AUTOMATION ENGINE (Emails & Notifications)
# ==========================================
def send_email(target_email, subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = target_email
    msg.set_content(body)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except: return False

# ==========================================
# 3. AUTHENTICATION & SESSION
# ==========================================
st.set_page_config(page_title="Kelly AI Premium", layout="centered")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})

# --- LOGIN/SIGNUP UI ---
if not st.session_state['auth']:
    st.title("💎 Kelly AI Premium Portal")
    choice = st.tabs(["Customer Login", "Create Account", "Admin"])
    
    with choice[0]:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Login to My Tools"):
            user = get_connection().execute("SELECT * FROM users WHERE email=? AND password=?", (e, p)).fetchone()
            if user:
                st.session_state.update({'auth': True, 'email': e, 'name': user[2], 'admin': False})
                st.rerun()
            else: st.error("Incorrect details.")

    with choice[1]:
        n = st.text_input("Your Full Name")
        em = st.text_input("Your Email")
        pw = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            try:
                get_connection().execute("INSERT INTO users VALUES (?,?,?)", (em, pw, n))
                get_connection().commit()
                st.success("Account Created! Use the Login tab.")
                # Send Welcome Email
                send_email(em, "Welcome to Kelly AI!", f"Hi {n}, thank you for joining! Access your tools here: {st.query_params.get('url', 'kelly-ai.streamlit.app')}")
            except: st.error("Email already in use.")

    with choice[2]:
        key = st.text_input("Admin Secret Key", type="password")
        if st.button("Manage Business"):
            if key == "KELLY_2026_PRO": # CHANGE THIS KEY
                st.session_state.update({'auth': True, 'admin': True})
                st.rerun()

# --- MAIN APP INTERFACE ---
else:
    st.sidebar.title(f"Hello, {st.session_state['name'] if not st.session_state['admin'] else 'Boss'}")
    if st.sidebar.button("Log Out"):
        st.session_state.update({'auth': False, 'admin': False})
        st.rerun()

    if st.session_state['admin']:
        # ADMIN DASHBOARD
        adm = st.tabs(["➕ Add Tool", "📋 Inventory", "📊 Finance", "🕵️ Vendor Tracker"])
        
        with adm[0]:
            st.header("Deliver New Account")
            with st.form("delivery"):
                c_mail = st.text_input("Customer Email (Must match their profile)")
                tool = st.selectbox("Tool", ["ChatGPT Plus", "CapCut Pro", "Canva Pro", "Claude Pro", "Grok"])
                login = st.text_input("Premium Login Email")
                pswd = st.text_input("Premium Login Password")
                order = st.text_input("G2G Order Number")
                price = st.number_input("Sold Price (NGN)")
                cost = st.number_input("Cost (USD)")
                rate = st.number_input("Rate", value=1550.0)
                days = st.number_input("Duration (Days)", value=30)
                
                if st.form_submit_button("Deliver & Notify"):
                    profit = price - (cost * rate)
                    exp = (datetime.now() + timedelta(days=days)).date()
                    get_connection().execute("INSERT INTO sales (cust_email, cust_name, product, p_login, p_pass, profit, p_date, e_date, order_id, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                            (c_mail, "Valued Customer", tool, login, pswd, profit, datetime.now().date(), exp, order, "Active"))
                    get_connection().commit()
                    # Trigger Email
                    body = f"Your {tool} is ready!\n\nLogin: {login}\nPassword: {pswd}\nExpires: {exp}"
                    send_email(c_mail, f"Delivery: Your {tool} is here!", body)
                    st.success("Account delivered via Email!")

        with adm[2]:
            st.header("Financial Performance")
            df_f = pd.read_sql("SELECT profit, p_date FROM sales", get_connection())
            if not df_f.empty:
                st.metric("Total Profit", f"N{df_f['profit'].sum():,.2f}")
                st.line_chart(df_f.set_index('p_date'))

    else:
        # CUSTOMER PORTAL
        cust = st.tabs(["🔓 My Premium Accounts", "💬 Support & Renewal"])
        
        with cust[0]:
            st.header("Your Active Subscriptions")
            my_df = pd.read_sql(f"SELECT * FROM sales WHERE cust_email='{st.session_state['email']}'", get_connection())
            if not my_df.empty:
                for _, row in my_df.iterrows():
                    with st.expander(f"⭐ {row['product']} (Exp: {row['e_date']})"):
                        st.code(f"Email: {row['p_login']}\nPass: {row['p_pass']}")
                        st.info(f"Status: {row['status']}")
                        if (pd.to_datetime(row['e_date']).date() - datetime.now().date()).days <= 3:
                            st.warning("⚠️ This account expires in less than 3 days! Contact support to renew.")
            else: st.write("You don't have any active tools. Purchase one and we will link it here!")

        with cust[1]:
            st.header("Need Help?")
            st.write("If you have issues or want to renew, tap below:")
            if st.button("Chat with Kelly AI on WhatsApp"):
                st.write(f"Redirecting to: {WHATSAPP_LINK}")
            st.write("Or join our Telegram for updates!")
