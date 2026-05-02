import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
from email.message import EmailMessage
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIG & DATABASE (v21)
# ==========================================
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
    # Tables: Sales, Users, and the new Products table
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cust_email TEXT, product TEXT, 
                  p_login TEXT, p_pass TEXT, profit REAL, p_date DATE, e_date DATE, 
                  order_id TEXT, vendor TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (name TEXT PRIMARY KEY, price REAL)''')
    conn.commit()

init_db()

# ==========================================
# 2. THE CUSTOMER PORTAL & LOGIN
# ==========================================
st.set_page_config(page_title="Kelly AI Enterprise", layout="centered")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})

if not st.session_state['auth']:
    st.title("💎 Kelly AI Enterprise")
    choice = st.tabs(["Login", "Sign Up", "Forgot Password", "Admin"])
    
    with choice[0]:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            user = get_connection().execute("SELECT * FROM users WHERE email=? AND password=?", (e, p)).fetchone()
            if user:
                st.session_state.update({'auth': True, 'email': e, 'name': user[2], 'admin': False})
                st.rerun()
            else: st.error("Wrong details.")

    with choice[1]:
        n = st.text_input("Full Name")
        em = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        if st.button("Register"):
            try:
                get_connection().execute("INSERT INTO users VALUES (?,?,?)", (em, pw, n))
                get_connection().commit()
                st.success("Success! Now Login.")
            except: st.error("Email taken.")

    with choice[2]:
        st.subheader("Reset Password")
        re_em = st.text_input("Registered Email", key="reset_em")
        re_name = st.text_input("Full Name for Verification")
        new_pw = st.text_input("New Password", type="password")
        if st.button("Reset Now"):
            conn = get_connection()
            check = conn.execute("SELECT * FROM users WHERE email=? AND name=?", (re_em, re_name)).fetchone()
            if check:
                conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_em))
                conn.commit()
                st.success("Password Updated!")
            else: st.error("Verification Failed.")

    with choice[3]:
        key = st.text_input("Admin Key", type="password")
        if st.button("Access Admin"):
            if key == "KELLY_2026_PRO":
                st.session_state.update({'auth': True, 'admin': True})
                st.rerun()

# ==========================================
# 3. THE MAIN APP (ADMIN & CUSTOMER)
# ==========================================
else:
    if st.sidebar.button("Logout"):
        st.session_state.update({'auth': False, 'admin': False})
        st.rerun()

    if st.session_state['admin']:
        adm = st.tabs(["➕ Deliver Account", "🏷️ Product Manager", "📊 Finance", "🕵️ Vendor Tracker"])
        
        with adm[0]:
            st.header("Deliver to Customer")
            with st.form("deliv"):
                c_mail = st.text_input("Customer Email")
                tool = st.selectbox("Tool", ["ChatGPT Plus", "CapCut Pro", "Canva Pro", "Claude Pro"])
                p_log = st.text_input("Premium Email")
                p_pas = st.text_input("Premium Pass")
                vend = st.text_input("G2G Vendor Name")
                oid = st.text_input("G2G Order ID")
                price = st.number_input("Price Sold (NGN)")
                cost = st.number_input("Cost (USD)")
                rate = st.number_input("Rate", value=1550.0)
                if st.form_submit_button("Deliver"):
                    profit = price - (cost * rate)
                    exp = (datetime.now() + timedelta(days=30)).date()
                    get_connection().execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                            (c_mail, tool, p_log, p_pas, profit, datetime.now().date(), exp, oid, vend, "Active"))
                    get_connection().commit()
                    st.success("Delivered!")

        with adm[1]:
            st.header("Price Settings")
            new_p = st.text_input("Tool Name")
            new_pr = st.number_input("Price (NGN)")
            if st.button("Update/Add Product"):
                get_connection().execute("INSERT OR REPLACE INTO products VALUES (?,?)", (new_p, new_pr))
                get_connection().commit()
                st.success(f"{new_p} price updated to N{new_pr}")

    else:
        # CUSTOMER MARKETPLACE
        cust = st.tabs(["🔓 My Accounts", "🛒 Marketplace", "💬 Support"])
        
        with cust[1]:
            st.header("Available Tools")
            prods = pd.read_sql("SELECT * FROM products", get_connection())
            for _, row in prods.iterrows():
                with st.container():
                    col1, col2 = st.columns([2, 1])
                    col1.write(f"**{row['name']}** - N{row['price']:,.0f}")
                    msg = urllib.parse.quote(f"Hello Kelly AI, I want to buy {row['name']} for N{row['price']}. My account email is {st.session_state['email']}")
                    link = f"https://wa.me/{MY_WHATSAPP}?text={msg}"
                    col2.link_button("Buy Now", link)

        with cust[0]:
            st.header("Your Subscriptions")
            my_df = pd.read_sql(f"SELECT * FROM sales WHERE cust_email='{st.session_state['email']}'", get_connection())
            if not my_df.empty:
                for _, row in my_df.iterrows():
                    st.info(f"{row['product']} | Login: {row['p_login']} | Pass: {row['p_pass']} | Exp: {row['e_date']}")
            else: st.write("No active accounts.")
