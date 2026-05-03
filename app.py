“””
Kelly AI Premium Tools - v33
Full-stack Streamlit application with SQLite, Admin Dashboard,
Customer Portal, Security Question Recovery, PDF Receipts, and more.
“””

import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import urllib.parse
import io
import os
from datetime import datetime

# — FPDF for PDF receipts —————————————————

try:
from fpdf import FPDF
FPDF_AVAILABLE = True
except ImportError:
FPDF_AVAILABLE = False

# — PAGE CONFIG ———————————————————––

st.set_page_config(
page_title=“Kelly AI Premium Tools”,
page_icon=”?”,
layout=“wide”,
initial_sidebar_state=“expanded”,
)

# — STYLING —————————————————————–

st.markdown(”””

<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3, .big-title {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800;
}

/* Dark premium theme */
.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #0a0f1a 100%);
    color: #e2e8f0;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #111827 100%);
    border-right: 1px solid #1e293b;
}

/* Card style */
.card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
    backdrop-filter: blur(10px);
}
.tool-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(30,41,59,0.8) 100%);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 20px;
    padding: 28px;
    margin: 16px 0;
    transition: all 0.3s ease;
}

/* Accent color */
.accent { color: #818cf8; }
.green  { color: #34d399; }
.red    { color: #f87171; }
.yellow { color: #fbbf24; }

/* Welcome banner */
.welcome-banner {
    background: linear-gradient(135deg, #312e81, #1e1b4b);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    border-left: 4px solid #818cf8;
}

/* Metric override */
[data-testid="metric-container"] {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 16px;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    padding: 10px 24px;
    transition: all 0.3s;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(99,102,241,0.35);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15, 23, 42, 0.8);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    color: #94a3b8;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important;
}

/* Inputs */
.stTextInput>div>div>input,
.stSelectbox>div>div,
.stNumberInput>div>div>input {
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

div[data-testid="stExpander"] {
    background: rgba(30,41,59,0.5);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 12px;
}
</style>

“””, unsafe_allow_html=True)

# — DATABASE PATH ————————————————————

DB_PATH = “kelly_ai_v33.db”

SECURITY_QUESTIONS = [
“What was the name of your first pet?”,
“What city were you born in?”,
“What is your mother’s maiden name?”,
“What was the name of your primary school?”,
“What is the name of your favourite childhood friend?”,
“What street did you grow up on?”,
“What was your childhood nickname?”,
]

# — DB INIT —————————————————————–

def init_db():
with sqlite3.connect(DB_PATH) as conn:
c = conn.cursor()
c.execute(”””
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
email TEXT UNIQUE NOT NULL,
password TEXT NOT NULL,
role TEXT DEFAULT ‘customer’,
status TEXT DEFAULT ‘Active’,
security_question TEXT,
security_answer TEXT,
created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
“””)
c.execute(”””
CREATE TABLE IF NOT EXISTS products (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE NOT NULL,
price REAL NOT NULL,
description TEXT,
created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
“””)
c.execute(”””
CREATE TABLE IF NOT EXISTS sales (
id INTEGER PRIMARY KEY AUTOINCREMENT,
order_id TEXT UNIQUE NOT NULL,
cust_email TEXT NOT NULL,
cust_login TEXT,
cust_password TEXT,
product_name TEXT NOT NULL,
g2g_vendor TEXT,
g2g_order_id TEXT,
price_ngn REAL DEFAULT 0,
cost_usd REAL DEFAULT 0,
exchange_rate REAL DEFAULT 0,
profit REAL DEFAULT 0,
status TEXT DEFAULT ‘Active’,
sold_at TEXT DEFAULT CURRENT_TIMESTAMP
)
“””)
conn.commit()

```
    # Seed admin if not present
    admin_email = "admin@kellyai.com"
    c.execute("SELECT id FROM users WHERE email=?", (admin_email,))
    if not c.fetchone():
        c.execute("""
            INSERT INTO users (name, email, password, role, status, security_question, security_answer)
            VALUES (?, ?, ?, 'admin', 'Active', ?, ?)
        """, (
            "Kelly Admin",
            admin_email,
            hash_pw("Admin@1234"),
            "What is your mother's maiden name?",
            hash_pw("kelly"),
        ))
        conn.commit()
```

def hash_pw(pw: str) -> str:
return hashlib.sha256(pw.encode()).hexdigest()

def gen_order_id() -> str:
import random, string
return “KAI-” + “”.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# — AUTH HELPERS ———————————————————––

def login_user(email: str, password: str):
email = email.lower().strip()
with sqlite3.connect(DB_PATH) as conn:
c = conn.cursor()
c.execute(“SELECT id,name,email,role,status FROM users WHERE email=? AND password=?”,
(email, hash_pw(password)))
return c.fetchone()

def register_user(name, email, password, sq, sa):
email = email.lower().strip()
with sqlite3.connect(DB_PATH) as conn:
c = conn.cursor()
try:
c.execute(”””
INSERT INTO users (name,email,password,security_question,security_answer)
VALUES (?,?,?,?,?)
“””, (name, email, hash_pw(password), sq, hash_pw(sa.lower().strip())))
conn.commit()
return True, “Account created!”
except sqlite3.IntegrityError:
return False, “Email already registered.”

def get_security_question(email: str):
email = email.lower().strip()
with sqlite3.connect(DB_PATH) as conn:
c = conn.cursor()
c.execute(“SELECT security_question FROM users WHERE email=?”, (email,))
row = c.fetchone()
return row[0] if row else None

def verify_security_answer(email: str, answer: str) -> bool:
email = email.lower().strip()
with sqlite3.connect(DB_PATH) as conn:
c = conn.cursor()
c.execute(“SELECT security_answer FROM users WHERE email=?”, (email,))
row = c.fetchone()
if not row:
return False
return row[0] == hash_pw(answer.lower().strip())

def reset_password(email: str, new_pw: str):
email = email.lower().strip()
with sqlite3.connect(DB_PATH) as conn:
c = conn.cursor()
c.execute(“UPDATE users SET password=? WHERE email=?”, (hash_pw(new_pw), email))
conn.commit()

# — SESSION STATE INIT —————————————————––

def init_session():
defaults = {
“auth”: False, “user_id”: None, “name”: “”, “email”: “”,
“role”: “customer”, “page”: “login”,
“reset_email”: “”, “reset_verified”: False,
}
for k, v in defaults.items():
if k not in st.session_state:
st.session_state[k] = v

def logout():
for k in list(st.session_state.keys()):
del st.session_state[k]
st.rerun()

# — PDF RECEIPT –––––––––––––––––––––––––––––––

def generate_pdf_receipt(order_id, product, price_ngn, cust_email, sold_at):
pdf = FPDF()
pdf.add_page()
pdf.set_margins(20, 20, 20)

```
# Header
pdf.set_fill_color(15, 17, 35)
pdf.set_text_color(255, 255, 255)
pdf.set_font("Helvetica", "B", 22)
pdf.cell(0, 14, "Kelly AI Premium Tools", ln=True, align="C", fill=True)
pdf.set_font("Helvetica", "", 11)
pdf.cell(0, 8, "Official Purchase Receipt", ln=True, align="C", fill=True)
pdf.ln(6)

# Body
pdf.set_text_color(30, 30, 30)
pdf.set_font("Helvetica", "B", 12)
pdf.cell(60, 9, "Order ID:", border=0)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 9, order_id, ln=True)

pdf.set_font("Helvetica", "B", 12)
pdf.cell(60, 9, "Product:", border=0)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 9, product, ln=True)

pdf.set_font("Helvetica", "B", 12)
pdf.cell(60, 9, "Amount Paid:", border=0)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 9, f"NGN {price_ngn:,.2f}", ln=True)

pdf.set_font("Helvetica", "B", 12)
pdf.cell(60, 9, "Customer Email:", border=0)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 9, cust_email, ln=True)

pdf.set_font("Helvetica", "B", 12)
pdf.cell(60, 9, "Date:", border=0)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 9, str(sold_at), ln=True)

pdf.ln(10)
pdf.set_font("Helvetica", "I", 10)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(0, 7, "Thank you for your purchase! For support, contact us on WhatsApp: +2347060911547 or Telegram. Keep this receipt for your records.", align="C")

# Footer line
pdf.ln(6)
pdf.set_draw_color(99, 102, 241)
pdf.set_line_width(1)
pdf.line(20, pdf.get_y(), 190, pdf.get_y())

return bytes(pdf.output())
```

# — AUTH PAGES —————————————————————

def page_login():
st.markdown(”<h1 style='text-align:center;color:#818cf8;'>? Kelly AI Premium Tools</h1>”, unsafe_allow_html=True)
st.markdown(”<p style='text-align:center;color:#64748b;'>Your gateway to premium AI tools</p>”, unsafe_allow_html=True)
st.markdown(”—”)

```
tab_login, tab_register, tab_reset = st.tabs(["? Login", "? Register", "? Reset Password"])

with tab_login:
    st.markdown("### Sign In")
    email = st.text_input("Email", key="li_email", placeholder="you@example.com")
    password = st.text_input("Password", type="password", key="li_pw", placeholder="????????")
    if st.button("Login ?", key="btn_login"):
        if not email or not password:
            st.warning("Please fill in all fields.")
        else:
            row = login_user(email, password)
            if not row:
                st.error("? Invalid email or password.")
            elif row[4] == "Banned":
                st.error("? Your account has been banned. Contact support.")
            else:
                st.session_state.auth = True
                st.session_state.user_id = row[0]
                st.session_state.name = row[1]
                st.session_state.email = row[2]
                st.session_state.role = row[3]
                st.session_state.page = "dashboard"
                st.success(f"Welcome back, {row[1]}! ?")
                st.rerun()

with tab_register:
    st.markdown("### Create Account")
    col1, col2 = st.columns(2)
    with col1:
        r_name = st.text_input("Full Name", key="r_name", placeholder="Kelly Smith")
        r_email = st.text_input("Email", key="r_email", placeholder="kelly@gmail.com")
    with col2:
        r_pw = st.text_input("Password", type="password", key="r_pw", placeholder="Min 6 chars")
        r_pw2 = st.text_input("Confirm Password", type="password", key="r_pw2", placeholder="Repeat password")
    r_sq = st.selectbox("Security Question", SECURITY_QUESTIONS, key="r_sq")
    r_sa = st.text_input("Security Answer", key="r_sa", placeholder="Your answer (remembered exactly)")
    if st.button("Create Account ?", key="btn_reg"):
        if not all([r_name, r_email, r_pw, r_pw2, r_sa]):
            st.warning("All fields are required.")
        elif r_pw != r_pw2:
            st.error("Passwords do not match.")
        elif len(r_pw) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            ok, msg = register_user(r_name, r_email, r_pw, r_sq, r_sa)
            if ok:
                st.success(f"? {msg} Please login.")
            else:
                st.error(f"? {msg}")

with tab_reset:
    st.markdown("### Reset Password (No Email Required)")
    st.info("? Answer your security question to reset your password -- no email needed.")
    rs_email = st.text_input("Your Email", key="rs_email", placeholder="Registered email")
    if st.button("Fetch My Question ?", key="btn_fetch_q"):
        if not rs_email:
            st.warning("Enter your email first.")
        else:
            q = get_security_question(rs_email)
            if q:
                st.session_state.reset_email = rs_email.lower().strip()
                st.session_state["fetched_q"] = q
                st.success(f"Question: **{q}**")
            else:
                st.error("No account found with that email.")

    if st.session_state.get("fetched_q"):
        st.markdown(f"**Question:** {st.session_state['fetched_q']}")
        rs_ans = st.text_input("Your Answer", key="rs_ans", placeholder="Your security answer")
        if st.button("Verify Answer ?", key="btn_verify"):
            if verify_security_answer(st.session_state.reset_email, rs_ans):
                st.session_state.reset_verified = True
                st.success("? Answer verified! Set your new password below.")
            else:
                st.error("? Incorrect answer.")

        if st.session_state.reset_verified:
            new_pw = st.text_input("New Password", type="password", key="new_pw")
            new_pw2 = st.text_input("Confirm New Password", type="password", key="new_pw2")
            if st.button("Reset Password ?", key="btn_reset_pw"):
                if new_pw != new_pw2:
                    st.error("Passwords do not match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    reset_password(st.session_state.reset_email, new_pw)
                    st.success("? Password reset! You can now login.")
                    st.session_state.reset_verified = False
                    del st.session_state["fetched_q"]
```

# — SIDEBAR ——————————————————————

def render_sidebar():
with st.sidebar:
st.markdown(”””
<div style='text-align:center;padding:20px 0 10px;'>
<span style='font-size:48px;'>?</span>
<h2 style='font-family:Syne,sans-serif;color:#818cf8;margin:6px 0 2px;'>Kelly AI</h2>
<p style='color:#475569;font-size:12px;margin:0;'>Premium Tools Platform</p>
</div>
“””, unsafe_allow_html=True)
st.markdown(”—”)
if st.session_state.auth:
st.markdown(f”””
<div class='welcome-banner'>
<p style='color:#c7d2fe;font-size:12px;margin:0;'>WELCOME BACK</p>
<p style='color:#e2e8f0;font-weight:700;font-size:16px;margin:4px 0 2px;'>{st.session_state.name}</p>
<p style='color:#818cf8;font-size:12px;margin:0;'>{st.session_state.email}</p>
<p style='color:#34d399;font-size:11px;margin:4px 0 0;'>? {‘Admin’ if st.session_state.role==‘admin’ else ‘Customer’}</p>
</div>
“””, unsafe_allow_html=True)
st.markdown(””)
if st.button(”? Logout”, use_container_width=True):
logout()

# — ADMIN DASHBOARD –––––––––––––––––––––––––––––

def admin_dashboard():
st.markdown(”<h1>?? Admin Dashboard</h1>”, unsafe_allow_html=True)
st.markdown(”—”)

```
tabs = st.tabs(["? Delivery", "?? Tool Manager", "? Users", "? Inventory", "? Reports", "? Backup"])

# -- TAB 1: DELIVERY -------------------------------------------------------
with tabs[0]:
    st.markdown("### ? Record New Delivery")
    with sqlite3.connect(DB_PATH) as conn:
        tools_df = pd.read_sql("SELECT name FROM products ORDER BY name", conn)

    if tools_df.empty:
        st.warning("?? No tools found. Add tools in the **?? Tool Manager** tab first.")
    else:
        tool_names = tools_df["name"].tolist()
        with st.form("delivery_form"):
            col1, col2 = st.columns(2)
            with col1:
                d_product = st.selectbox("Product / Tool", tool_names)
                d_email = st.text_input("Customer Email")
                d_login = st.text_input("Delivered Login")
                d_password = st.text_input("Delivered Password")
            with col2:
                d_vendor = st.text_input("G2G Vendor Name")
                d_g2g_id = st.text_input("G2G Order ID")
                d_price = st.number_input("Sold Price (NGN)", min_value=0.0, step=100.0)
                d_cost = st.number_input("Cost (USD)", min_value=0.0, step=0.5)
                d_rate = st.number_input("Exchange Rate (?/USD)", min_value=0.0, value=1600.0)

            submit_d = st.form_submit_button("? Record Delivery", use_container_width=True)
            if submit_d:
                if not d_email:
                    st.error("Customer email is required.")
                else:
                    profit = d_price - (d_cost * d_rate)
                    oid = gen_order_id()
                    with sqlite3.connect(DB_PATH) as conn:
                        conn.execute("""
                            INSERT INTO sales
                            (order_id,cust_email,cust_login,cust_password,product_name,
                             g2g_vendor,g2g_order_id,price_ngn,cost_usd,exchange_rate,profit,status)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,'Active')
                        """, (oid, d_email.lower().strip(), d_login, d_password,
                              d_product, d_vendor, d_g2g_id, d_price, d_cost, d_rate, profit))
                        conn.commit()
                    st.success(f"? Delivery recorded! Order ID: **{oid}** | Profit: ?{profit:,.2f}")

# -- TAB 2: TOOL MANAGER ----------------------------------------------------
with tabs[1]:
    st.markdown("### ?? Tool Manager -- Command Center")
    with st.form("add_product_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            p_name = st.text_input("Product Name", placeholder="e.g. ChatGPT Plus")
            p_desc = st.text_area("Description", placeholder="Brief description for customers...")
        with col2:
            p_price = st.number_input("Price (NGN)", min_value=0.0, step=100.0)
        if st.form_submit_button("? Add Tool", use_container_width=True):
            if not p_name:
                st.error("Product name required.")
            else:
                try:
                    with sqlite3.connect(DB_PATH) as conn:
                        conn.execute("INSERT INTO products (name,price,description) VALUES (?,?,?)",
                                     (p_name, p_price, p_desc))
                        conn.commit()
                    st.success(f"? '{p_name}' added to marketplace!")
                except sqlite3.IntegrityError:
                    st.error("A product with that name already exists.")

    st.markdown("#### Current Products")
    with sqlite3.connect(DB_PATH) as conn:
        prod_df = pd.read_sql("SELECT id, name, price, description, created_at FROM products", conn)
    if prod_df.empty:
        st.info("No products yet. Add your first tool above.")
    else:
        st.dataframe(prod_df, use_container_width=True)
        st.markdown("#### Remove a Product")
        del_name = st.selectbox("Select product to delete", prod_df["name"].tolist(), key="del_prod")
        if st.button("?? Delete Product", key="btn_del_prod"):
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("DELETE FROM products WHERE name=?", (del_name,))
                conn.commit()
            st.success(f"Deleted '{del_name}'.")
            st.rerun()

# -- TAB 3: USER MANAGEMENT ------------------------------------------------
with tabs[2]:
    st.markdown("### ? User Management")
    with sqlite3.connect(DB_PATH) as conn:
        users_df = pd.read_sql(
            "SELECT id, name, email, role, status, created_at FROM users ORDER BY created_at DESC", conn)
    if users_df.empty:
        st.info("No users found.")
    else:
        st.dataframe(users_df, use_container_width=True)
        st.markdown("#### Ban / Unban a User")
        non_admin = users_df[users_df["role"] != "admin"]["email"].tolist()
        if non_admin:
            selected_email = st.selectbox("Select user", non_admin, key="ban_sel")
            user_row = users_df[users_df["email"] == selected_email].iloc[0]
            curr_status = user_row["status"]
            new_status = "Banned" if curr_status == "Active" else "Active"
            btn_label = f"? Ban User" if curr_status == "Active" else "? Unban User"
            if st.button(btn_label, key="btn_ban"):
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("UPDATE users SET status=? WHERE email=?", (new_status, selected_email))
                    conn.commit()
                st.success(f"User {selected_email} is now **{new_status}**.")
                st.rerun()
        else:
            st.info("No customer accounts to manage.")

# -- TAB 4: INVENTORY & TRACKING -------------------------------------------
with tabs[3]:
    st.markdown("### ? Sales Inventory & Tracking")
    with sqlite3.connect(DB_PATH) as conn:
        sales_df = pd.read_sql("SELECT * FROM sales ORDER BY sold_at DESC", conn)

    if sales_df.empty:
        st.info("No sales recorded yet. Deliveries will appear here.")
    else:
        st.dataframe(sales_df, use_container_width=True)
        st.markdown("---")
        col_r, col_s = st.columns(2)

        with col_r:
            st.markdown("#### ? Download PDF Receipt")
            if not FPDF_AVAILABLE:
                st.warning("Install `fpdf2` to enable PDF receipts: `pip install fpdf2`")
            else:
                r_oid = st.selectbox("Select Order ID", sales_df["order_id"].tolist(), key="receipt_oid")
                if st.button("? Generate Receipt"):
                    row = sales_df[sales_df["order_id"] == r_oid].iloc[0]
                    pdf_bytes = generate_pdf_receipt(
                        row["order_id"], row["product_name"],
                        row["price_ngn"], row["cust_email"], row["sold_at"]
                    )
                    st.download_button(
                        label="?? Download Receipt PDF",
                        data=pdf_bytes,
                        file_name=f"receipt_{r_oid}.pdf",
                        mime="application/pdf"
                    )

        with col_s:
            st.markdown("#### ? Update Order Status")
            s_oid = st.selectbox("Select Order", sales_df["order_id"].tolist(), key="status_oid")
            s_status = st.selectbox("New Status", ["Active", "Issue", "Refunded"], key="new_status")
            if st.button("Update Status", key="btn_upd_status"):
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("UPDATE sales SET status=? WHERE order_id=?", (s_status, s_oid))
                    conn.commit()
                st.success(f"Order {s_oid} ? **{s_status}**")
                st.rerun()

# -- TAB 5: REPORTS --------------------------------------------------------
with tabs[4]:
    st.markdown("### ? Profit Reports")
    with sqlite3.connect(DB_PATH) as conn:
        sales_df = pd.read_sql("SELECT * FROM sales", conn)

    if sales_df.empty:
        st.info("No sales data to report yet.")
    else:
        total_profit = sales_df["profit"].sum()
        total_revenue = sales_df["price_ngn"].sum()
        total_orders = len(sales_df)
        avg_profit = sales_df["profit"].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("? Total Profit (?)", f"?{total_profit:,.2f}")
        c2.metric("? Total Revenue (?)", f"?{total_revenue:,.2f}")
        c3.metric("? Total Orders", total_orders)
        c4.metric("? Avg Profit/Order", f"?{avg_profit:,.2f}")

        st.markdown("---")
        st.markdown("#### Profit by Product")
        by_product = sales_df.groupby("product_name")["profit"].sum().reset_index()
        by_product.columns = ["Product", "Total Profit (?)"]
        st.bar_chart(by_product.set_index("Product"))

        st.markdown("#### Orders by Status")
        by_status = sales_df["status"].value_counts().reset_index()
        by_status.columns = ["Status", "Count"]
        st.dataframe(by_status, use_container_width=True)

# -- TAB 6: BACKUP & RESTORE -----------------------------------------------
with tabs[5]:
    st.markdown("### ? Backup & Restore")
    col_b, col_rest = st.columns(2)

    with col_b:
        st.markdown("#### ?? Export Sales as CSV")
        with sqlite3.connect(DB_PATH) as conn:
            bk_df = pd.read_sql("SELECT * FROM sales", conn)
        if bk_df.empty:
            st.info("No sales to export.")
        else:
            csv_data = bk_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "? Download Backup CSV",
                data=csv_data,
                file_name=f"kelly_ai_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col_rest:
        st.markdown("#### ?? Restore / Append from CSV")
        uploaded = st.file_uploader("Upload CSV backup", type=["csv"])
        if uploaded:
            try:
                restore_df = pd.read_csv(uploaded)
                st.dataframe(restore_df.head(5), use_container_width=True)
                if st.button("? Append to Database", use_container_width=True):
                    with sqlite3.connect(DB_PATH) as conn:
                        restore_df.to_sql("sales", conn, if_exists="append", index=False)
                        conn.commit()
                    st.success(f"? {len(restore_df)} rows appended successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading file: {e}")
```

# — CUSTOMER PORTAL –––––––––––––––––––––––––––––

def customer_portal():
st.markdown(f”<h1>? Hello, {st.session_state.name}!</h1>”, unsafe_allow_html=True)
st.markdown(”—”)

```
tabs = st.tabs(["? My Tools", "? Marketplace", "? Support"])

# -- MY TOOLS --------------------------------------------------------------
with tabs[0]:
    st.markdown("### ? My Active Tools")
    with sqlite3.connect(DB_PATH) as conn:
        my_sales = pd.read_sql(
            "SELECT * FROM sales WHERE cust_email=? ORDER BY sold_at DESC",
            conn, params=(st.session_state.email,))

    if my_sales.empty:
        st.info("?? You have no active tools. Visit the **? Marketplace** to purchase!")
    else:
        st.success(f"You have **{len(my_sales)}** tool(s) in your account.")
        for _, row in my_sales.iterrows():
            with st.expander(f"? {row['product_name']} -- Order {row['order_id']} [{row['status']}]"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Login / Email:** `{row['cust_login'] or 'N/A'}`")
                    st.markdown(f"**Password:** `{row['cust_password'] or 'N/A'}`")
                with col2:
                    st.markdown(f"**Order ID:** `{row['order_id']}`")
                    st.markdown(f"**Purchased:** {row['sold_at']}")
                    status_color = {"Active": "?", "Issue": "?", "Refunded": "?"}.get(row["status"], "?")
                    st.markdown(f"**Status:** {status_color} {row['status']}")

# -- MARKETPLACE -----------------------------------------------------------
with tabs[1]:
    st.markdown("### ? Tool Marketplace")
    with sqlite3.connect(DB_PATH) as conn:
        products = pd.read_sql("SELECT * FROM products ORDER BY name", conn)

    if products.empty:
        st.warning("?? No tools available yet. Check back soon!")
    else:
        cols = st.columns(2)
        for i, (_, prod) in enumerate(products.iterrows()):
            with cols[i % 2]:
                wa_text = urllib.parse.quote(
                    f"Hello! I want to buy {prod['name']}. My email is {st.session_state.email}."
                )
                wa_link = f"https://wa.me/2347060911547?text={wa_text}"
                st.markdown(f"""
                <div class='tool-card'>
                    <h3 style='color:#818cf8;font-family:Syne,sans-serif;margin-bottom:6px;'>{prod['name']}</h3>
                    <p style='color:#34d399;font-size:22px;font-weight:700;margin:4px 0;'>?{prod['price']:,.0f}</p>
                    <p style='color:#94a3b8;font-size:14px;margin:8px 0 16px;'>{prod['description'] or 'Premium AI tool access.'}</p>
                    <a href='{wa_link}' target='_blank'
                       style='background:linear-gradient(135deg,#25d366,#128c7e);
                              color:white;padding:10px 20px;border-radius:8px;
                              text-decoration:none;font-weight:700;font-size:14px;'>
                       ? Buy on WhatsApp
                    </a>
                </div>
                """, unsafe_allow_html=True)

# -- SUPPORT ---------------------------------------------------------------
with tabs[2]:
    st.markdown("### ? Customer Support")
    st.markdown("""
    <div class='card'>
        <h3 style='color:#818cf8;'>Contact Us Instantly</h3>
        <p style='color:#94a3b8;'>Our team is available to help you 24/7. Reach us through:</p>
        <br>
        <a href='https://wa.me/2347060911547' target='_blank'
           style='background:linear-gradient(135deg,#25d366,#128c7e);
                  color:white;padding:12px 28px;border-radius:10px;
                  text-decoration:none;font-weight:700;font-size:15px;margin-right:16px;'>
           ? WhatsApp Support
        </a>
        <a href='https://t.me/kellyaitools' target='_blank'
           style='background:linear-gradient(135deg,#229ed9,#2aabee);
                  color:white;padding:12px 28px;border-radius:10px;
                  text-decoration:none;font-weight:700;font-size:15px;'>
           ?? Telegram Support
        </a>
        <br><br>
        <p style='color:#64748b;font-size:13px;'>
          WhatsApp: +234 706 091 1547 &nbsp;|&nbsp; Response time: usually within minutes
        </p>
    </div>
    """, unsafe_allow_html=True)
```

# — MAIN ROUTER –––––––––––––––––––––––––––––––

def main():
init_db()
init_session()
render_sidebar()

```
if not st.session_state.auth:
    page_login()
else:
    if st.session_state.role == "admin":
        admin_dashboard()
    else:
        customer_portal()
```

if **name** == “**main**”:
main()
