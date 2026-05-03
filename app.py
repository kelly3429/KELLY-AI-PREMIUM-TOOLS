import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
import random
from email.message import EmailMessage
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# ==========================================
# 1. CONFIGURATION & DATABASE
# ==========================================
COMPANY_NAME = "Kelly AI Premium Tools"
ADMIN_PASSWORD = "Kelly500#"
MY_WHATSAPP = "2347060911547"

# EMAIL CONFIG - Replace with your Gmail App Password
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "your_app_password" 

@st.cache_resource
def get_connection():
    return sqlite3.connect('kelly_ai_v28.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cust_email TEXT, product TEXT, 
                  p_login TEXT, p_pass TEXT, profit REAL, p_date DATE, e_date DATE, 
                  order_id TEXT, vendor TEXT, status TEXT, price_paid REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT)''')
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

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 10, COMPANY_NAME, 0, 1, 'C')
    pdf.set_font("Arial", '', 12); pdf.ln(10)
    for k, v in data.items(): pdf.cell(100, 10, f"{k}: {v}", 0, 1)
    return pdf.output(dest='S').encode('latin-1', 'replace')

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
        e = st.text_input("Email", key="l_e")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Access Portal"):
            u = get_connection().execute("SELECT * FROM users WHERE email=? AND password=?", (e, p)).fetchone()
            if u: 
                st.session_state.update({'auth':True, 'email':e, 'name':u[2], 'admin':False})
                st.rerun()
            else: st.error("Login Failed.")

    with t[1]:
        n = st.text_input("Full Name", key="s_n")
        em = st.text_input("Email Address", key="s_e")
        pw = st.text_input("Create Password", type="password", key="s_p")
        if st.button("Create Profile"):
            try:
                conn = get_connection(); conn.execute("INSERT INTO users VALUES (?,?,?)", (em, pw, n))
                conn.commit(); st.success("Account Ready!")
            except: st.error("Email taken.")

    with t[2]:
        st.subheader("Password Recovery via OTP")
        re_e = st.text_input("Enter Registered Email", key="recovery_email")
        if st.button("Send OTP Code"):
            u = get_connection().execute("SELECT * FROM users WHERE email=?", (re_e,)).fetchone()
            if u:
                otp = str(random.randint(1000, 9999))
                st.session_state['otp'] = otp
                st.session_state['otp_email'] = re_e
                send_automated_email(re_e, "Your OTP Code", f"Your Kelly AI Recovery code is: {otp}")
                st.success("OTP sent to your email!")
            else: st.error("Email not found.")
        
        input_otp = st.text_input("Enter 4-Digit Code", key="otp_in")
        new_pw = st.text_input("New Password", type="password", key="otp_new_pw")
        if st.button("Verify & Reset"):
            if input_otp == st.session_state['otp'] and st.session_state['otp_email'] == re_e:
                conn = get_connection()
                conn.execute("UPDATE users SET password=? WHERE email=?", (new_pw, re_e))
                conn.commit(); st.success("Password Updated! Go to Login.")
            else: st.error("Invalid Code or Email.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD: 
                st.session_state.update({'auth':True, 'admin':True})
                st.rerun()

else:
    # --- AUTHENTICATED AREA ---
    if st.sidebar.button("Logout"): 
        st.session_state.update({'auth':False, 'admin':False}); st.rerun()

    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Manager", "📋 Inventory", "📊 Revenue", "💾 Data Insurance"])
        
        with adm[0]:
            with st.form("d_form", clear_on_submit=True):
                tools = [r[0] for r in get_connection().execute("SELECT name FROM products").fetchall()]
                c_mail = st.text_input("Customer Email")
                tool = st.selectbox("Tool", tools if tools else ["Add tools first"])
                p_mail = st.text_input("Premium Email")
                p_pass = st.text_input("Premium Password")
                v_name = st.text_input("G2G Vendor")
                o_id = st.text_input("G2G Order ID")
                n_paid = st.number_input("Paid (NGN)")
                u_cost = st.number_input("Cost (USD)")
                rate = st.number_input("Rate", value=1550.0)
                p_date = st.date_input("Purchase Date", datetime.now())
                if st.form_submit_button("Deliver & Email"):
                    prof = n_paid - (u_cost * rate); e_date = p_date + timedelta(days=30)
                    conn = get_connection()
                    conn.execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status, price_paid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (c_mail, tool, p_mail, p_pass, prof, p_date, e_date, o_id, v_name, "Active", n_paid))
                    conn.commit()
                    send_automated_email(c_mail, "Your Account is Ready!", f"Tool: {tool}\nLogin: {p_mail}\nPass: {p_pass}\nExpires: {e_date}")
                    st.success("Delivered!")

        with adm[1]:
            with st.form("p_mgr"):
                pn = st.text_input("Tool Name"); pp = st.number_input("Price (NGN)"); pd = st.text_area("Description")
                if st.form_submit_button("Update Marketplace"):
                    get_connection().execute("INSERT OR REPLACE INTO products VALUES (?,?,?)", (pn, pp, pd))
                    get_connection().commit(); st.success("Updated!")

        with adm[2]:
            df = pd.read_sql_query("SELECT * FROM sales", get_connection())
            if not df.empty:
                def style_rows(row):
                    days_left = (pd.to_datetime(row['e_date']).date() - datetime.now().date()).days
                    if row['status'] != 'Active': return ['background-color: #ffcccc']*len(row)
                    if days_left <= 2: return ['background-color: #ffffcc']*len(row)
                    return ['']*len(row)
                st.dataframe(df.style.apply(style_rows, axis=1), use_container_width=True)
                
                rid = st.number_input("ID to Update Status", min_value=1)
                new_s = st.selectbox("Status", ["Active", "Issue", "Refunded", "Expired"])
                if st.button("Apply"):
                    get_connection().execute("UPDATE sales SET status=? WHERE id=?", (new_s, rid))
                    get_connection().commit(); st.rerun()

    else:
        # --- CUSTOMER PORTAL ---
        c_tabs = st.tabs(["🔓 My Accounts", "🛒 Marketplace", "💬 Support"])
        with c_tabs[0]:
            my_tools = pd.read_sql_query(f"SELECT * FROM sales WHERE cust_email='{st.session_state['email']}'", get_connection())
            if not my_tools.empty:
                for _, r in my_tools.iterrows():
                    with st.expander(f"⭐ {r['product']} (Exp: {r['e_date']})"):
                        st.code(f"Email: {r['p_login']}\nPass: {r['p_pass']}")
            else: st.info("No active accounts.")

        with c_tabs[1]:
            p_df = pd.read_sql_query("SELECT * FROM products", get_connection())
            for _, r in p_df.iterrows():
                st.write(f"### {r['name']} — N{r['price']:,.0f}")
                txt = urllib.parse.quote(f"I want to buy {r['name']} for N{r['price']}. Email: {st.session_state['email']}")
                st.link_button("Buy via WhatsApp", f"https://wa.me/{MY_WHATSAPP}?text={txt}")
                st.divider()
