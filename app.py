import streamlit as st
import pandas as pd
import sqlite3
import smtplib
import urllib.parse
from email.message import EmailMessage
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# ==========================================
# 1. CONFIGURATION & DATABASE (v26)
# ==========================================
COMPANY_NAME = "Kelly AI Premium Tools"
ADMIN_PASSWORD = "Kelly500#"
MY_WHATSAPP = "2347060911547"

# EMAIL CONFIG - Replace with your Gmail App Password
EMAIL_ADDRESS = "your_email@gmail.com" 
EMAIL_PASSWORD = "your_app_password" 

@st.cache_resource
def get_connection():
    conn = sqlite3.connect('kelly_ai_v26.db', check_same_thread=False)
    return conn

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
# 2. CORE UTILITIES (Email & PDF)
# ==========================================
def send_email(to_email, tool, login, pswd, expiry):
    msg = EmailMessage()
    msg['Subject'] = f"🚀 {tool} Delivery - {COMPANY_NAME}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    body = f"Hello,\n\nYour {tool} is ready!\n\nDetails:\nEmail: {login}\nPass: {pswd}\nExpires: {expiry}\n\nSupport: {MY_WHATSAPP}"
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
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, COMPANY_NAME, 0, 1, 'C')
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    for k, v in data.items():
        pdf.cell(100, 10, f"{k}: {v}", 0, 1)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# ==========================================
# 3. INTERFACE LOGIC
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})

if not st.session_state['auth']:
    st.title(f"💎 {COMPANY_NAME}")
    t = st.tabs(["Login", "Register", "Forgot Password", "Admin"])
    
    with t[0]:
        e = st.text_input("Email", key="l_e")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Access Portal"):
            u = get_connection().execute("SELECT * FROM users WHERE email=? AND password=?", (e, p)).fetchone()
            if u: st.session_state.update({'auth':True, 'email':e, 'name':u[2], 'admin':False}); st.rerun()
            else: st.error("Login Failed.")

    with t[1]:
        n = st.text_input("Full Name", key="s_n")
        em = st.text_input("Email", key="s_e")
        pw = st.text_input("Password", type="password", key="s_p")
        if st.button("Create Profile"):
            try:
                conn = get_connection()
                conn.execute("INSERT INTO users VALUES (?,?,?)", (em, pw, n))
                conn.commit(); st.success("Account Ready!")
            except: st.error("Email taken.")

    with t[2]:
        re_e = st.text_input("Registered Email", key="r_e")
        re_n = st.text_input("Registered Name", key="r_n")
        new_p = st.text_input("New Password", type="password", key="r_p")
        if st.button("Reset My Password"):
            c = get_connection()
            if c.execute("SELECT * FROM users WHERE email=? AND name=?", (re_e, re_n)).fetchone():
                c.execute("UPDATE users SET password=? WHERE email=?", (new_p, re_e))
                c.commit(); st.success("Reset Successful!")
            else: st.error("Details do not match.")

    with t[3]:
        ak = st.text_input("Admin Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD: st.session_state.update({'auth':True, 'admin':True}); st.rerun()

else:
    # --- AUTHENTICATED AREA ---
    if st.sidebar.button("Logout"): st.session_state.update({'auth':False}); st.rerun()

    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Manager", "📋 Inventory", "📊 Revenue", "💾 Data Insurance"])
        
        with adm[0]:
            st.header("New Order Delivery")
            with st.form("d_form", clear_on_submit=True):
                tools = [r[0] for r in get_connection().execute("SELECT name FROM products").fetchall()]
                c_mail = st.text_input("Customer Email")
                tool = st.selectbox("Select Tool", tools if tools else ["Set tools in Manager first"])
                p_mail = st.text_input("Premium Email")
                p_pass = st.text_input("Premium Password")
                v_name = st.text_input("G2G Vendor")
                o_id = st.text_input("G2G Order Number")
                n_paid = st.number_input("Paid (NGN)")
                u_cost = st.number_input("Cost (USD)")
                rate = st.number_input("Rate", value=1550.0)
                p_date = st.date_input("Purchase Date", datetime.now())
                
                if st.form_submit_button("Deliver Tool & Email"):
                    prof = n_paid - (u_cost * rate)
                    e_date = p_date + timedelta(days=30)
                    conn = get_connection()
                    conn.execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status, price_paid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (c_mail, tool, p_mail, p_pass, prof, p_date, e_date, o_id, v_name, "Active", n_paid))
                    conn.commit()
                    send_email(c_mail, tool, p_mail, p_pass, e_date)
                    st.success("Delivered and Saved!")

        with adm[1]:
            st.header("Product Manager")
            with st.form("p_mgr"):
                pn = st.text_input("Tool Name")
                pp = st.number_input("Price (NGN)")
                pd = st.text_area("Description (Features)")
                if st.form_submit_button("Update Shop"):
                    get_connection().execute("INSERT OR REPLACE INTO products VALUES (?,?,?)", (pn, pp, pd))
                    get_connection().commit(); st.success("Marketplace Updated!")

        with adm[2]:
            st.header("Inventory & Tracker")
            df = pd.read_sql("SELECT * FROM sales", get_connection())
            # Suggestion 1: Highlighting Expiry
            def style_rows(row):
                days_left = (pd.to_datetime(row['e_date']).date() - datetime.now().date()).days
                if row['status'] != 'Active': return ['background-color: #ffcccc']*len(row)
                if days_left <= 2: return ['background-color: #ffffcc']*len(row)
                return ['']*len(row)
            
            st.dataframe(df.style.apply(style_rows, axis=1), use_container_width=True)
            
            st.divider()
            col_u, col_p = st.columns(2)
            with col_u:
                rid = st.number_input("Record ID", min_value=1)
                new_s = st.selectbox("Update Status", ["Active", "Issue", "Refunded", "Expired"])
                if st.button("Update Status"):
                    get_connection().execute("UPDATE sales SET status=? WHERE id=?", (new_s, rid))
                    get_connection().commit(); st.rerun()
            with col_p:
                prid = st.number_input("Receipt ID", min_value=1)
                if st.button("Print PDF"):
                    raw = df[df['id'] == prid].to_dict('records')[0]
                    st.download_button("Download PDF", generate_pdf(raw), f"Receipt_{prid}.pdf")

        with adm[3]:
            # Suggestion 3: Revenue Visuals
            st.header("Revenue Insights")
            rev_df = pd.read_sql("SELECT product, profit, p_date FROM sales", get_connection())
            if not rev_df.empty:
                st.bar_chart(rev_df.groupby('product')['profit'].sum())
                st.metric("Total Profit", f"N{rev_df['profit'].sum():,.2f}")

        with adm[4]:
            st.header("Data Insurance")
            full_df = pd.read_sql("SELECT * FROM sales", get_connection())
            st.download_button("Download Backup (CSV)", full_df.to_csv(index=False).encode('utf-8'), "kelly_backup.csv")
            
            up_file = st.file_uploader("Restore from CSV", type="csv")
            if up_file and st.button("Process Restore"):
                res_df = pd.read_csv(up_file)
                res_df.to_sql('sales', get_connection(), if_exists='append', index=False)
                st.success("Restored!")

    else:
        # --- CUSTOMER PORTAL ---
        c_tabs = st.tabs(["🔓 My Accounts", "🛒 Marketplace", "💬 Support"])
        
        with c_tabs[0]:
            st.header("My Premium Access")
            my_tools = pd.read_sql(f"SELECT * FROM sales WHERE cust_email='{st.session_state['email']}'", get_connection())
            if not my_tools.empty:
                for _, r in my_tools.iterrows():
                    with st.expander(f"⭐ {r['product']} (Exp: {r['e_date']})"):
                        st.code(f"Email: {r['p_login']}\nPass: {r['p_pass']}")
                        st.info(f"Status: {r['status']}")
            else: st.info("Purchase a tool in the Marketplace to see it here!")

        with c_tabs[1]:
            st.header("Marketplace")
            p_df = pd.read_sql("SELECT * FROM products", get_connection())
            for _, r in p_df.iterrows():
                with st.container():
                    st.write(f"### {r['name']} - N{r['price']:,.0f}")
                    st.write(r['description'])
                    txt = urllib.parse.quote(f"Hello Kelly AI, I want to buy {r['name']} for N{r['price']}. My email is {st.session_state['email']}")
                    st.link_button("Buy via WhatsApp", f"https://wa.me/{MY_WHATSAPP}?text={txt}")
                    st.divider()

        with c_tabs[2]:
            st.header("Customer Support")
            st.write("WhatsApp: 07060911547")
            st.link_button("Telegram Support", "https://t.me/yourlink")
