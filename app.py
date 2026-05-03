import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# ==========================================
# 1. CONFIGURATION
# ==========================================
COMPANY_NAME = "Kelly AI Premium Tools"
ADMIN_PASSWORD = "Kelly500#"
MY_WHATSAPP = "2347060911547"

def get_connection():
    return sqlite3.connect('kelly_ai_master_final.db', check_same_thread=False)

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
# 2. UTILITIES
# ==========================================
def generate_pdf_receipt(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, COMPANY_NAME, 0, 1, 'C')
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    for key, value in row.items():
        pdf.cell(100, 10, f"{key.upper()}: {value}", 0, 1)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 3. INTERFACE
# ==========================================
st.set_page_config(page_title=COMPANY_NAME, layout="wide")

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})

# --- SIDEBAR ---
if st.session_state['auth']:
    st.sidebar.title(f"👋 Welcome, {st.session_state.get('name', 'User')}")
    st.sidebar.info(f"Account: {st.session_state['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.update({'auth': False, 'admin': False, 'email': "", 'name': ""})
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
                    if u[3] == 'Banned': st.error("🚫 Your account is banned.")
                    else:
                        st.session_state.update({'auth':True, 'email':e_in, 'name':u[2], 'admin':False})
                        st.rerun()
                else: st.error("Invalid credentials.")

    with t[1]:
        n_reg = st.text_input("Full Name")
        em_reg = st.text_input("Email").lower().strip()
        pw_reg = st.text_input("Password", type="password")
        sq = st.selectbox("Security Question", ["First pet's name", "High school name", "Favorite food"])
        sa = st.text_input("Security Answer")
        if st.button("Create Profile"):
            try:
                with get_connection() as conn:
                    conn.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (em_reg, pw_reg, n_reg, 'Active', sq, sa.lower()))
                    conn.commit()
                st.success("Registration Successful! Now Login.")
            except: st.error("Email already exists.")

    with t[2]:
        re_e = st.text_input("Your Email", key="rec_e").lower().strip()
        if re_e:
            with get_connection() as conn:
                u = conn.execute("SELECT security_q FROM users WHERE email=?", (re_e,)).fetchone()
                if u:
                    st.info(f"Question: {u[0]}")
                    ans = st.text_input("Answer", key="rec_a").lower().strip()
                    new_p = st.text_input("New Pass", type="password")
                    if st.button("Reset"):
                        check = conn.execute("SELECT * FROM users WHERE email=? AND security_a=?", (re_e, ans)).fetchone()
                        if check:
                            conn.execute("UPDATE users SET password=? WHERE email=?", (new_p, re_e))
                            conn.commit(); st.success("Updated! Login now.")
                        else: st.error("Wrong Answer.")

    with t[3]:
        ak = st.text_input("Admin Secret Key", type="password")
        if st.button("Unlock Admin"):
            if ak == ADMIN_PASSWORD:
                st.session_state.update({'auth':True, 'admin':True, 'name':'Boss', 'email':'Admin'})
                st.rerun()

# --- CONTENT ---
else:
    if st.session_state['admin']:
        adm = st.tabs(["📦 Delivery", "🛠️ Tool Mgr", "👥 User Mgmt", "📋 Inventory & Tracking", "📊 Reports", "💾 Backup"])
        
        with adm[0]:
            st.header("New Delivery")
            with get_connection() as conn:
                tools = [r[0] for r in conn.execute("SELECT name FROM products").fetchall()]
            with st.form("d_form", clear_on_submit=True):
                c_mail = st.text_input("Customer Email")
                tool = st.selectbox("Tool", tools if tools else ["NO TOOLS FOUND! Go to Tool Mgr tab."])
                p_l = st.text_input("Premium Login")
                p_p = st.text_input("Premium Password")
                price = st.number_input("Sold Price (NGN)")
                cost = st.number_input("Cost (USD)")
                rate = st.number_input("Rate", value=1550.0)
                vendor = st.text_input("Vendor")
                order = st.text_input("Order ID")
                if st.form_submit_button("Deliver"):
                    prof = price - (cost * rate)
                    exp = (datetime.now() + timedelta(days=30)).date()
                    with get_connection() as conn:
                        conn.execute("INSERT INTO sales (cust_email, product, p_login, p_pass, profit, p_date, e_date, order_id, vendor, status, price_paid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                     (c_mail, tool, p_l, p_p, prof, datetime.now().date(), exp, order, vendor, "Active", price))
                        conn.commit()
                    st.success("Order Recorded Successfully!")

        with adm[1]:
            st.header("Tool Manager")
            with st.form("tool_add"):
                pn = st.text_input("Tool Name")
                pp = st.number_input("Price (NGN)")
                pd = st.text_area("Description")
                if st.form_submit_button("Add to Marketplace"):
                    with get_connection() as conn:
                        conn.execute("INSERT OR REPLACE INTO products VALUES (?,?,?)", (pn, pp, pd))
                        conn.commit()
                    st.success(f"{pn} added to store!")

        with adm[2]:
            st.header("Manage Users")
            with get_connection() as conn:
                u_df = pd.read_sql("SELECT name, email, status FROM users", conn)
            st.dataframe(u_df, use_container_width=True)
            target = st.text_input("User Email to Ban/Delete")
            c1, c2 = st.columns(2)
            if c1.button("🚫 Ban/Unban User"):
                with get_connection() as conn:
                    curr = conn.execute("SELECT status FROM users WHERE email=?", (target,)).fetchone()
                    if curr:
                        ns = 'Banned' if curr[0] == 'Active' else 'Active'
                        conn.execute("UPDATE users SET status=? WHERE email=?", (ns, target))
                        conn.commit(); st.rerun()
            if c2.button("🗑️ Delete User"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM users WHERE email=?", (target,))
                    conn.commit(); st.rerun()

        with adm[3]:
            st.header("Inventory Tracker")
            with get_connection() as conn:
                df = pd.read_sql("SELECT * FROM sales", conn)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                r_id = st.number_input("Receipt ID", min_value=1)
                if st.button("Generate Receipt"):
                    row_data = df[df['id'] == r_id].to_dict('records')[0]
                    st.download_button("Download PDF", generate_pdf_receipt(row_data), f"Receipt_{r_id}.pdf")
            else: st.warning("No sales recorded yet.")

        with adm[4]:
            st.header("Profit Report")
            with get_connection() as conn:
                rep = pd.read_sql("SELECT product, profit FROM sales", conn)
            if not rep.empty:
                st.metric("Total Profit", f"N{rep['profit'].sum():,.2f}")
                st.bar_chart(rep.groupby('product').sum())
            else: st.warning("No data for reports.")

        with adm[5]:
            st.header("Backup")
            with get_connection() as conn:
                full_csv = pd.read_sql("SELECT * FROM sales", conn)
            st.download_button("Export to CSV", full_csv.to_csv(index=False).encode('utf-8'), "backup.csv")
            up = st.file_uploader("Import CSV", type="csv")
            if up and st.button("Restore Data"):
                res_df = pd.read_csv(up)
                res_df.to_sql('sales', get_connection(), if_exists='append', index=False)
                st.success("Data Restored!")

    else:
        # CUSTOMER PORTAL
        ct = st.tabs(["🔓 My Tools", "🛒 Store", "💬 Support"])
        with ct[0]:
            with get_connection() as conn:
                my_tools = pd.read_sql(f"SELECT * FROM sales WHERE cust_email='{st.session_state['email']}'", conn)
            if not my_tools.empty:
                for _, r in my_tools.iterrows():
                    with st.expander(f"⭐ {r['product']} (Exp: {r['e_date']})"):
                        st.code(f"Email: {r['p_login']}\nPass: {r['p_pass']}")
            else: st.info("You don't have any active tools. Visit the Store tab to buy!")
            
        with ct[1]:
            st.header("Marketplace")
            with get_connection() as conn:
                p_df = pd.read_sql("SELECT * FROM products", conn)
            if not p_df.empty:
                for _, r in p_df.iterrows():
                    st.subheader(f"{r['name']} — N{r['price']:,.0f}")
                    st.write(r['description'])
                    msg = urllib.parse.quote(f"Buy {r['name']}. My email is {st.session_state['email']}")
                    st.link_button("Order via WhatsApp", f"https://wa.me/{MY_WHATSAPP}?text={msg}")
                    st.divider()
            else: st.warning("Store is currently being stocked. Check back soon!")

        with ct[2]:
            st.header("Support")
            st.link_button("WhatsApp Support", f"https://wa.me/{MY_WHATSAPP}")
            st.link_button("Telegram Group", "https://t.me/kelly_ai_tools")
