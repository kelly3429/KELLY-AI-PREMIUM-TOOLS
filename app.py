import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
from email.message import EmailMessage
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIG & DATABASE
# ==========================================
# GMAIL CONFIG - YOU MUST SETUP A GMAIL "APP PASSWORD"
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "your_app_password" 
MY_WHATSAPP = "2347060911547"

@st.cache_resource
def get_connection():
    conn = sqlite3.connect('kelly_ai_enterprise_v21.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table for Deliveries
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cust_email TEXT, product TEXT, 
                  p_login TEXT, p_pass TEXT, profit REAL, p_date DATE, e_date DATE, 
                  order_id TEXT, vendor TEXT, status TEXT)''')
    # Table for Customer Portal Logins
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    # Table for Store Products
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (name TEXT PRIMARY KEY, price REAL)''')
    conn.commit()

init_db()

# ==========================================
# 2. AUTHENTICATION UI (FIXED KEYS)
# ==========================================
st.set_page_config(page_title="Kelly AI Enterprise", layout="centered")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})

if not st.session_state['auth']:
    st.title("💎 Kelly AI Enterprise")
    choice = st.tabs(["Login", "Sign Up", "Forgot Password", "Admin"])
    
    with choice[0]:
        e = st.text_input("Email", key="login_email")
        p = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = get_connection().execute("SELECT * FROM users WHERE email=? AND password=?", (e, p)).fetchone()
            if user:
                st.session_state.update({'auth': True, 'email': e, 'name': user[2], 'admin': False})
                st.rerun()
            else: st.error("Wrong details.")

    with choice[1]:
        n = st.text_input("Full Name", key="signup_name")
        em = st.text_input("Email", key="signup_email")
        pw = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Register"):
            try:
                get_connection().execute("INSERT INTO users VALUES (?,?,?)", (em, pw, n))
                get_connection().commit()
                st.success("Success! Now Login.")
            except: st.error("Email taken.")

    with choice[2]:
        st.subheader("Reset Password")
        re_em = st.text_input("Registered Email", key="reset_email_input")
        re_name = st.text_input("Full Name for Verification", key="reset_name_input")
        new_pw = st.text_input("New Password", type="password", key="reset_new_pass")
        if st.button("Update Password"):
            conn = get_connection()
            check = conn.execute("SELECT * FROM users WHERE email=? AND name=?", (re_em, re_name)).fetchone()
            if check:
                conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_em))
                conn.commit()
                st.success("Password Updated!")
            else: st.error("Verification Failed. Name or Email incorrect.")

    with choice[3]:
        key = st.text_input("Admin Secret Key", type="password", key="admin_key_input")
        if st.button("Access Admin Panel"):
            if key == "KELLY_2026_PRO":
                st.session_state.update({'auth': True, 'admin': True})
                st.rerun()

# ==========================================
# 3. MAIN APP INTERFACE
# ==========================================
else:
    st.sidebar.title(f"Logged in as: {st.session_state['name'] if not st.session_state['admin'] else 'Admin'}")
    if st.sidebar.button("Logout"):
        st.session_state.update({'auth': False, 'admin': False})
        st.rerun()

    if st.session_state['admin']:
        adm = st.tabs(["➕ Deliver Tool", "🏷️ Product Manager", "📊 Finance", "🕵️ Vendor Tracker"])
        
        with adm[0]:
            st.header("Deliver Account to Customer")
            with st.form("delivery_form"):
                c_mail = st.text_input("Customer's Email")
                # Dynamically get products from the database for the dropdown
                prod_list = [row[0] for row in get_connection().execute("SELECT name FROM products").fetchall()]
                tool = st.selectbox("Select Tool", prod_list if prod_list else ["Default Tool"])
                p_log = st.text_input("Premium Email Login")
                p_pas = st.text_input("Premium Password")
                vend = st.text_input("G2G Vendor Name")
                oid = st.text_input("G2G Order ID")
                price = st.number_input("Sold Price (NGN)", min_value=0.0)
                cost = st.number_input("Cost (USD)", min_value=0.0)
                rate = st.number_input("Rate (NGN/$)", value=1550.0)
                if st.form_submit_button("Deliver & Save"):
                    profit = price - (cost * rate)
                    exp = (datetime.now() + timedelta(days=30)).date()
                    get_connection().execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                            (c_mail, tool, p_log, p_pas, profit, datetime.now().date(), exp, oid, vend, "Active"))
                    get_connection().commit()
                    st.success(f"Delivery recorded for {c_mail}!")

        with adm[1]:
            st.header("Manage Shop Products")
            with st.form("prod_form"):
                new_p = st.text_input("Product Name (e.g. ChatGPT Plus)")
                new_pr = st.number_input("Price (NGN)", min_value=0.0)
                if st.form_submit_button("Update/Add to Shop"):
                    get_connection().execute("INSERT OR REPLACE INTO products VALUES (?,?)", (new_p, new_pr))
                    get_connection().commit()
                    st.success(f"{new_p} is now listed at N{new_pr:,.0f}")
            
            st.subheader("Current Price List")
            st.dataframe(pd.read_sql("SELECT * FROM products", get_connection()), use_container_width=True)

    else:
        # CUSTOMER PORTAL
        cust = st.tabs(["🔓 My Accounts", "🛒 Marketplace", "💬 Support"])
        
        with cust[1]:
            st.header("Premium Marketplace")
            prods = pd.read_sql("SELECT * FROM products", get_connection())
            if not prods.empty:
                for _, row in prods.iterrows():
                    with st.container():
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"### {row['name']}")
                        c1.write(f"Price: **N{row['price']:,.0f}**")
                        # Automated WhatsApp Message
                        msg = urllib.parse.quote(f"Hello Kelly AI, I want to buy {row['name']} for N{row['price']:,.0f}. My account email is {st.session_state['email']}")
                        wa_url = f"https://wa.me/{MY_WHATSAPP}?text={msg}"
                        c2.link_button("Buy via WhatsApp", wa_url)
                        st.divider()
            else:
                st.info("The marketplace is currently being updated. Check back soon!")

        with cust[0]:
            st.header("My Active Accounts")
            my_df = pd.read_sql(f"SELECT product, p_login, p_pass, e_date, status FROM sales WHERE cust_email='{st.session_state['email']}'", get_connection())
            if not my_df.empty:
                st.dataframe(my_df, use_container_width=True)
            else:
                st.info("You haven't purchased any tools yet. Visit the Marketplace!")
