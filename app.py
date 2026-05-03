import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
from email.message import EmailMessage
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION
# ==========================================
COMPANY_NAME = "Kelly AI Premium Tools"
ADMIN_PASSWORD = "Kelly500#"
MY_WHATSAPP = "2347060911547"

# EMAIL CONFIG - Optional: Only works if App Password is correct
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx" 

def get_connection():
    return sqlite3.connect('kelly_ai_v31.db', check_same_thread=False)

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
# 2. INTERFACE LOGIC
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})

# --- SIDEBAR ---
if st.session_state['auth']:
    st.sidebar.title(f"👋 Welcome, {st.session_state.get('name', 'User')}")
    st.sidebar.info(f"Logged in: {st.session_state['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.update({'auth': False, 'admin': False})
        st.rerun()

# --- GATEKEEPER ---
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
                    if u[3] == 'Banned': st.error("🚫 Account Banned. Contact Support.")
                    else:
                        st.session_state.update({'auth':True, 'email':e_in, 'name':u[2], 'admin':False})
                        st.rerun()
                else: st.error("Login Failed.")

    with t[1]:
        st.subheader("New Registration")
        n_reg = st.text_input("Full Name")
        em_reg = st.text_input("Email").lower().strip()
        pw_reg = st.text_input("Password", type="password")
        sq = st.selectbox("Security Question", ["First pet's name", "Childhood best friend", "High school name"])
        sa = st.text_input("Security Answer")
        if st.button("Create Profile"):
            try:
                with get_connection() as conn:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (em_reg, pw_reg, n_reg, 'Active', sq, sa.lower()))
                    conn.commit()
                st.success("Registration Successful! Now Login.")
            except: st.error("Email already exists.")

    with t[2]:
        st.subheader("Recover Account")
        re_e = st.text_input("Registered Email", key="rec_e").lower().strip()
        if re_e:
            with get_connection() as conn:
                u = conn.execute("SELECT security_q FROM users WHERE email=?", (re_e,)).fetchone()
                if u:
                    st.info(f"Question: {u[0]}")
                    ans = st.text_input("Your Secret Answer", key="rec_a").lower().strip()
                    new_p = st.text_input("New Password", type="password")
                    if st.button("Reset Now"):
                        check = conn.execute("SELECT * FROM users WHERE email=? AND security_a=?", (re_e, ans)).fetchone()
                        if check:
                            conn.execute("UPDATE users SET password=? WHERE email=?", (new_p, re_e))
                            conn.commit(); st.success("Updated! Please Login.")
                        else: st.error("Wrong Answer.")
                else: st.error("Email not found.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD:
                st.session_state.update({'auth':True, 'admin':True, 'name':'Boss', 'email':'Admin'})
                st.rerun()

# --- ADMIN / CUSTOMER CONTENT ---
else:
    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Manager", "👥 User Mgmt", "📋 Inventory Tracker", "📊 Profit Report"])
        
        with adm[3]:
            st.header("Inventory & Vendor Tracker")
            with get_connection() as conn:
                df = pd.read_sql("SELECT * FROM sales", conn)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                row_id = st.number_input("Record ID", min_value=1)
                new_status = st.selectbox("Status", ["Active", "Issue with Vendor", "Refunded", "Expired"])
                if st.button("Update Status"):
                    get_connection().execute("UPDATE sales SET status=? WHERE id=?", (new_status, row_id))
                    get_connection().commit(); st.rerun()
            else: st.info("No records found.")

        with adm[4]:
            st.header("Financial Performance")
            with get_connection() as conn:
                rep_df = pd.read_sql("SELECT product, profit, p_date FROM sales", conn)
            if not rep_df.empty:
                st.metric("Total Overall Profit", f"N{rep_df['profit'].sum():,.2f}")
                st.bar_chart(rep_df.groupby('product')['profit'].sum())

        with adm[0]:
            st.header("Deliver New Tool")
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
                vendor = st.text_input("G2G Vendor")
                order = st.text_input("G2G Order ID")
                if st.form_submit_button("Deliver Tool"):
                    prof = price - (cost * rate)
                    exp = (datetime.now() + timedelta(days=30)).date()
                    with get_connection() as conn:
                        conn.execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status, price_paid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (c_mail, tool, p_l, p_p, prof, datetime.now().date(), exp, order, vendor, "Active", price))
                        conn.commit()
                    st.success("Sale Recorded!")

        with adm[1]:
            st.header("Product Marketplace Manager")
            with st.form("pm"):
                pn = st.text_input("Product Name")
                pp = st.number_input("Price (NGN)")
                pd = st.text_area("Description")
                if st.form_submit_button("Save Product"):
                    with get_connection() as conn:
                        conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?)", (pn, pp, pd))
                        conn.commit()
                    st.success("Store Updated!")

    else:
        # CUSTOMER PORTAL
        ct = st.tabs(["🔓 My Tools", "🛒 Store", "💬 Support"])
        with ct[0]:
            with get_connection() as conn:
                my_df = pd.read_sql(f"SELECT * FROM sales WHERE cust_email='{st.session_state['email']}'", conn)
            if not my_df.empty:
                for _, r in my_df.iterrows():
                    with st.expander(f"⭐ {r['product']} (Exp: {r['e_date']})"):
                        st.code(f"Email: {r['p_login']}\nPass: {r['p_pass']}")
            else: st.info("No active accounts.")
            
        with ct[1]:
            with get_connection() as conn:
                p_df = pd.read_sql("SELECT * FROM products", conn)
            for _, r in p_df.iterrows():
                st.write(f"### {r['name']} — N{r['price']:,.0f}")
                txt = urllib.parse.quote(f"Buy {r['name']}. Email: {st.session_state['email']}")
                st.link_button("Order via WhatsApp", f"https://wa.me/{MY_WHATSAPP}?text={txt}")
                st.divider()

        with ct[2]:
            st.header("Need Help?")
            st.link_button("Chat on WhatsApp", f"https://wa.me/{MY_WHATSAPP}")
            st.link_button("Join Telegram", "https://t.me/kelly_ai_tools")
