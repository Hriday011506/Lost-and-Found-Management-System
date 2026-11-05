"""Campus Lost & Found — Streamlit pilot application."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import date, datetime
from zoneinfo import ZoneInfo
from html import escape
import hashlib
import hmac
import secrets

import pandas as pd
import streamlit as st
import streamlit as pt

ROOT = Path(__file__).parent
DB_PATH = ROOT / "lost_found.db"
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="MUJ Lost & Found", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
          salt TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS items (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          report_type TEXT NOT NULL CHECK(report_type IN ('Lost','Found')),
          item_name TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL,
          location TEXT NOT NULL, event_date TEXT NOT NULL, image_path TEXT,
          identification_mark TEXT DEFAULT '',
          status TEXT NOT NULL DEFAULT 'Open',
          created_at TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS claims (
          id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
          claimant_id INTEGER NOT NULL, ownership_details TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'Pending', admin_note TEXT DEFAULT '',
          created_at TEXT NOT NULL,
          FOREIGN KEY(item_id) REFERENCES items(id),
          FOREIGN KEY(claimant_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS audit_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id INTEGER,
          action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
        );
        """)
        item_columns = {row[1] for row in c.execute("PRAGMA table_info(items)").fetchall()}
        if "identification_mark" not in item_columns:
            c.execute("ALTER TABLE items ADD COLUMN identification_mark TEXT DEFAULT ''")
        # Demo admin is created only when the database is first initialized.
        # Admin provisioning is intentionally not seeded in the public app.
        # Create the first administrator locally through the documented bootstrap procedure
        # before deploying to an approved pilot environment.

def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 240000).hex()

def verify_password(password: str, salt: str, expected: str) -> bool:
    return hmac.compare_digest(hash_password(password, salt), expected)

def log_action(actor_id, action, detail):
    with get_conn() as c:
        c.execute("INSERT INTO audit_log(actor_id,action,detail,created_at) VALUES(?,?,?,?)",
                  (actor_id, action, detail, datetime.now().isoformat(timespec="seconds")))

def rows(query, args=()):
    with get_conn() as c:
        return c.execute(query, args).fetchall()

def one(query, args=()):
    with get_conn() as c:
        return c.execute(query, args).fetchone()

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
 
    :root {
      color-scheme: light;
      --o600:#D9541E; --o700:#B8430F; --o50:#FFF4EC; --o100:#FFE4D1; --o200:#FFCBA8;
      --ink:#26201C; --muted:#6F655E; --line:#EDE4DE; --field:#DDD2CB;
      --found-bg:#E8F5EE; --found-fg:#17623D;
      --radius:12px;
    }
 
    /* ---------- Base ---------- */
    html, body, .stApp, [data-testid="stAppViewContainer"],
    .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp select,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp li {
      font-family:'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
    }
    /* Do not override Streamlit's icon font: doing so prints words such as
       "visibility" instead of rendering the password eye icon. */
    .material-icons, .material-icons-outlined, .material-symbols-rounded,
    .material-symbols-outlined, [data-testid="stIconMaterial"] {
      font-family:'Material Icons', 'Material Symbols Rounded' !important;
      font-weight:normal !important; font-style:normal !important;
      letter-spacing:normal !important; text-transform:none !important;
      white-space:nowrap !important; direction:ltr !important;
      -webkit-font-feature-settings:'liga'; -webkit-font-smoothing:antialiased;
    }
    .stApp, [data-testid="stAppViewContainer"] {background:#FFFFFF !important; color:var(--ink);}
    [data-testid="stHeader"] {background:rgba(255,255,255,.92) !important; backdrop-filter:blur(8px);
      border-bottom:3px solid var(--o600);}
    #MainMenu, footer {visibility:hidden;}
    .block-container {padding-top:2.2rem; padding-bottom:4rem; max-width:1200px;}
    h1,h2,h3,h4 {color:var(--ink); letter-spacing:-.025em; font-weight:750;}
    h2 {font-size:1.5rem;} h3 {font-size:1.2rem;}
    p, li, label, .stMarkdown {line-height:1.65;}
    a {color:var(--o700) !important; text-decoration-color:var(--o200); text-underline-offset:3px;}
    a:hover {color:var(--o600) !important;}
    hr {border-color:var(--line) !important;}
 
    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {background:var(--o50); border-right:1px solid var(--o100);}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {color:var(--ink) !important;}
    [data-testid="stSidebar"] .stButton button:not([kind="primary"]) {
      background:#fff; border:1px solid var(--o200); color:var(--o700) !important;
    }
 
    /* ---------- Hero ---------- */
    .hero {
      position:relative; overflow:hidden;
      padding:2rem 2.2rem 2rem 2.4rem; margin-bottom:1.8rem;
      background:linear-gradient(105deg, var(--o50) 0%, #FFFFFF 70%);
      border:1px solid var(--o100); border-radius:16px;
    }
    .hero::before {content:""; position:absolute; left:0; top:0; bottom:0; width:6px; background:var(--o600);}
    .hero h1 {font-size:2.3rem; line-height:1.15; letter-spacing:-.04em; margin:0 0 .6rem 0; color:var(--ink); font-weight:800;}
    .hero p {color:var(--muted); margin:0; font-size:1.05rem; max-width:62ch;}
 
    /* ---------- Metrics ---------- */
    .metric-card {
      background:#fff; border:1px solid var(--line); border-top:3px solid var(--o600);
      border-radius:var(--radius); padding:1rem 1.2rem; box-shadow:0 1px 2px rgba(38,32,28,.04);
    }
    .metric-label {font-size:.85rem; color:var(--muted); font-weight:500;}
    .metric-value {font-size:2rem; font-weight:800; color:var(--ink); letter-spacing:-.03em; line-height:1.2;}
    [data-testid="stMetric"] {background:#fff; border:1px solid var(--line); border-top:3px solid var(--o600);
      border-radius:var(--radius); padding:.9rem 1.1rem;}
    [data-testid="stMetricValue"] {font-weight:800; color:var(--ink);}
    [data-testid="stMetricLabel"] p {color:var(--muted) !important;}
 
    /* ---------- Cards (st.container(border=True)) and item cards ---------- */
    [data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {
      border-radius:var(--radius);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
      border:1px solid var(--line) !important; border-radius:var(--radius) !important;
      background:#fff; box-shadow:0 1px 2px rgba(38,32,28,.04);
      transition:border-color .15s ease, box-shadow .15s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
      border-color:var(--o200) !important; box-shadow:0 6px 20px rgba(217,84,30,.08);
    }
    /* nested wrappers (layout columns) should stay flat */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"] {
      box-shadow:none;
    }
    [data-testid="stImage"] img {border-radius:10px;}
 
    /* Optional helpers for your own markup */
    .item-card {background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:1.1rem 1.2rem;
      margin-bottom:1rem; transition:border-color .15s ease, box-shadow .15s ease;}
    .item-card:hover {border-color:var(--o200); box-shadow:0 6px 20px rgba(217,84,30,.08);}
    .item-title {font-size:1.08rem; font-weight:700; color:var(--ink); margin:.35rem 0 .25rem 0;}
    .item-meta {font-size:.88rem; color:var(--muted);}
    .badge {display:inline-block; padding:.18rem .65rem; border-radius:999px; font-size:.78rem; font-weight:700; margin-right:.4rem;}
    .badge-lost {background:var(--o100); color:var(--o700);}
    .badge-found {background:var(--found-bg); color:var(--found-fg);}
    .badge-open {background:#fff; color:var(--ink); border:1px solid var(--field);}
    .badge-pending {background:#FFF6D6; color:#7A5600;}
    .badge-approved {background:var(--found-bg); color:var(--found-fg);}
    .badge-rejected {background:#FDE8E8; color:#9B1C1C;}
    .badge-closed {background:#EFEAE6; color:var(--muted);}
 
    /* ---------- Forms ---------- */
    div[data-testid="stForm"] {background:#fff; border:1px solid var(--line); border-radius:16px;
      padding:1.6rem 1.6rem 1.2rem; box-shadow:0 1px 3px rgba(38,32,28,.05);}
    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    .stTextInput label, .stTextArea label, .stSelectbox label {color:var(--ink) !important; opacity:1 !important;}
    [data-testid="stWidgetLabel"] p {font-weight:600; font-size:.92rem;}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color:var(--muted) !important; opacity:1 !important;}
 
    input, textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
      background:#fff !important; color:var(--ink) !important;
    }
    [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
      background:#fff !important; border:1px solid var(--field) !important; border-radius:9px !important;
      transition:border-color .15s ease, box-shadow .15s ease;
    }
    [data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within,
    [data-baseweb="select"] > div:focus-within {
      border-color:var(--o600) !important; box-shadow:0 0 0 3px rgba(217,84,30,.18) !important;
    }
    input::placeholder, textarea::placeholder {color:#8F857E !important; opacity:1 !important;}
    [data-baseweb="popover"] ul {background:#fff !important;}
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] [aria-selected="true"] {background:var(--o50) !important;}
 
    [data-testid="stFileUploaderDropzone"] {background:var(--o50); border:1.5px dashed var(--o200); border-radius:var(--radius);}
    [data-testid="stFileUploaderDropzone"] * {color:var(--ink) !important;}
    [data-testid="stFileUploaderDropzone"] button {background:#fff !important; border:1px solid var(--o200) !important; color:var(--o700) !important;}
    [data-testid="stFileUploaderDropzone"] button [data-testid="stIconMaterial"] {
      display:none !important;
    }
    [data-testid="stFileUploaderDropzone"] button span {
      color:var(--o700) !important; -webkit-text-fill-color:var(--o700) !important;
    }
    [data-testid="stDateInput"] input,
    [data-testid="stDateInput"] [data-baseweb="input"],
    [data-testid="stDateInput"] [data-baseweb="datepicker"] {
      background:#fff !important; color:var(--ink) !important;
    }
    [data-testid="stDateInput"] svg {color:var(--o600) !important; fill:var(--o600) !important;}
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
      background:#fff !important; color:var(--ink) !important;
    }
 
    /* ---------- Buttons ---------- */
    .stButton button, .stFormSubmitButton button, .stDownloadButton button {
      border-radius:9px; min-height:2.7rem; font-weight:650; padding:0 1.2rem;
      transition:background .15s ease, border-color .15s ease, transform .05s ease;
    }
    .stButton button:not([kind="primary"]), .stDownloadButton button {
      background:#fff; color:var(--o700); border:1px solid var(--o200);
    }
    .stButton button:not([kind="primary"]):hover, .stDownloadButton button:hover {
      background:var(--o50); border-color:var(--o600); color:var(--o700);
    }
    .stButton button[kind="primary"], .stFormSubmitButton button,
    [data-testid="stFormSubmitButton"] button, [data-testid="stFormSubmitButton"] button *,
    button[kind="primary"] {
      background:var(--o600) !important; border:1px solid var(--o600) !important;
      color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
      box-shadow:0 2px 8px rgba(217,84,30,.18);
    }
    [data-testid="stFormSubmitButton"] button p,
    [data-testid="stFormSubmitButton"] button span {
      color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
      background:var(--o700) !important; border-color:var(--o700) !important;
    }
    [data-testid="stTextInput"] button {
      background:transparent !important; border:0 !important; box-shadow:none !important;
      color:var(--muted) !important; -webkit-text-fill-color:var(--muted) !important;
    }
    [data-testid="stTextInput"] button span {
      font-family:'Material Icons', 'Material Symbols Rounded' !important;
    }
    .stButton button[kind="primary"]:hover, .stFormSubmitButton button:hover {
      background:var(--o700) !important; border-color:var(--o700) !important; color:#fff !important;
    }
    .stButton button:active, .stFormSubmitButton button:active {transform:translateY(1px);}
    button:focus-visible, a:focus-visible, [role="tab"]:focus-visible {outline:3px solid rgba(217,84,30,.4) !important; outline-offset:2px;}
 
    /* ---------- Tabs ---------- */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {gap:.35rem; border-bottom:1px solid var(--line);}
    [data-testid="stTabs"] [role="tab"], [data-testid="stTabs"] button, [data-baseweb="tab"] {
      color:var(--muted) !important; -webkit-text-fill-color:var(--muted) !important;
      opacity:1 !important; font-weight:650 !important; font-size:1rem !important;
      padding:.7rem 1.1rem !important; border-radius:9px 9px 0 0;
    }
    [data-testid="stTabs"] [role="tab"]:hover {background:var(--o50); color:var(--o700) !important; -webkit-text-fill-color:var(--o700) !important;}
    [data-testid="stTabs"] [role="tab"][aria-selected="true"],
    [data-testid="stTabs"] button[aria-selected="true"],
    [data-baseweb="tab"][aria-selected="true"] {
      color:var(--o600) !important; -webkit-text-fill-color:var(--o600) !important; background:var(--o50);
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:var(--o600) !important; height:3px !important;}
    [data-testid="stTabs"] [data-baseweb="tab-border"] {background:var(--line) !important;}
 
    /* ---------- Expanders, alerts, tables ---------- */
    [data-testid="stExpander"] {border:1px solid var(--line) !important; border-radius:var(--radius) !important; background:#fff;}
    [data-testid="stExpander"] summary:hover {color:var(--o700);}
    [data-testid="stAlert"] {border-radius:var(--radius); border:1px solid var(--line);}
    [data-testid="stDataFrame"] {border:1px solid var(--line); border-radius:var(--radius); overflow:hidden;}
    [data-testid="stSpinner"] * {color:var(--o600) !important;}
    [data-testid="stProgress"] > div > div > div {background:var(--o600);}
 
    /* ---------- Full-screen campus login ---------- */
    .stApp:has(.login-shell) [data-testid="stSidebar"] {display:none !important;}
    .stApp:has(.login-shell) [data-testid="stHeader"] {background:transparent !important; border:0 !important;}
    .stApp:has(.login-shell) [data-testid="stToolbar"] {display:none !important;}
    .stApp:has(.login-shell) [data-testid="stAppViewContainer"] {background:transparent !important;}
    .stApp:has(.login-shell) [data-testid="stAppViewContainer"]::before {
      content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
      background:
        linear-gradient(90deg,rgba(36,20,9,.16),rgba(36,20,9,.03) 58%,rgba(36,20,9,.08)),
        url('/app/static/campus_bg.jpg') center center/cover no-repeat,
        linear-gradient(125deg,#8B431D,#F0A13F);
    }
    .stApp:has(.login-shell) [data-testid="stMain"],
    .stApp:has(.login-shell) [data-testid="stMainBlockContainer"] {background:transparent !important; position:relative; z-index:1;}
    .stApp:has(.login-shell) .block-container {max-width:none !important; padding:3.5rem 0 2rem 10.2% !important;}
    .login-shell {max-width:430px; margin:0 0 1.1rem 0; position:relative; z-index:2;}
    .login-brand {display:flex; align-items:center; gap:.8rem; margin:0 0 1rem .1rem; color:#fff;
      text-shadow:0 1px 8px rgba(0,0,0,.35);}
    .login-brand-mark {width:42px; height:42px; display:grid; place-items:center; border-radius:12px;
      background:var(--o600); color:#fff; font-size:1.35rem; font-weight:800;}
    .login-brand-name {font-size:1.1rem; font-weight:800; color:#fff; letter-spacing:-.02em;}
    .login-brand-sub {font-size:.7rem; color:rgba(255,255,255,.9); letter-spacing:.12em; font-weight:700;}
    .login-visual {display:none;}
    .login-panel {background:rgba(255,255,255,.98); border:1px solid rgba(255,255,255,.85);
      border-radius:24px; padding:1.65rem 1.7rem 1.35rem; width:100%; max-width:430px;
      min-height:0; box-shadow:0 18px 55px rgba(45,25,12,.22);}
    .login-panel h2 {font-size:1.45rem; margin:.1rem 0 .3rem; color:var(--ink);}
    .login-panel-intro {color:var(--muted); margin:0 0 .9rem; font-size:.9rem;}
    .login-eyebrow {font-size:.7rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:var(--o700); margin-bottom:.55rem;}
    .login-footnote {font-size:.74rem; color:var(--muted); text-align:center; margin-top:.85rem;}
    .login-panel [data-testid="stTabs"] [role="tab"] {font-size:.88rem !important; padding:.6rem .8rem !important;}
    .login-panel [data-testid="stForm"] {border:0 !important; padding:.6rem 0 0 !important; box-shadow:none !important;}
    @media (max-width:900px) {
      .stApp:has(.login-shell) .block-container {padding:2rem 1rem !important;}
      .login-panel,.login-shell {max-width:100%;}
    }

    /* ---------- Mobile ---------- */
    @media (max-width:640px) {
      .block-container {padding-top:1.4rem; padding-left:1rem; padding-right:1rem;}
      .hero {padding:1.4rem 1.2rem 1.4rem 1.5rem;}
      .hero h1 {font-size:1.7rem;}
      div[data-testid="stForm"] {padding:1.1rem;}
    }
    @media (prefers-reduced-motion:reduce) {* {transition:none !important;}}
    </style>
    """, unsafe_allow_html=True)
 

def metric(label, value, note=""):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-label">{note}</div></div>', unsafe_allow_html=True)

def institutional_role(email: str):
    address = email.strip().lower()
    if address.endswith('@muj.manipal.edu'):
        return 'student'
    if address.endswith('@jaipur.manipal.edu'):
        return 'staff'
    return None

def create_account(name,email,password):
    role = institutional_role(email)
    if role is None:
        return False
    salt = secrets.token_hex(16)
    digest = hash_password(password,salt)
    try:
        with get_conn() as c:
            c.execute("INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)",
                      (name,email.lower().strip(),digest,salt,role,datetime.now().isoformat(timespec="seconds")))
        return True
    except sqlite3.IntegrityError:
        return False

init_db()
# Provision the first administrator from Streamlit secrets; never hard-code credentials.
try:
    admin_email = st.secrets["bootstrap"]["admin_email"]
    admin_password = st.secrets["bootstrap"]["admin_password"]
    if admin_email and admin_password and not one("SELECT id FROM users WHERE role='admin'"):
        salt = secrets.token_hex(16)
        digest = hash_password(admin_password, salt)
        with get_conn() as c:
            c.execute("""INSERT INTO users(name,email,password_hash,salt,role,created_at)
                         VALUES(?,?,?,?,?,?)""",
                      ("Campus Administrator", admin_email.lower().strip(), digest, salt, "admin",
                       datetime.now().isoformat(timespec="seconds")))
except Exception:
    pass

if "user" not in st.session_state:
    st.session_state.user = None
inject_css()

with st.sidebar:
    st.markdown("## 🔎 MUJ Lost & Found")
    st.caption("MANIPAL UNIVERSITY JAIPUR")
    st.divider()
    if st.session_state.user:
        u = st.session_state.user
        st.markdown(f"**{u['name']}**")
        st.caption(u["role"].title())
        nav_options = ["Overview","Browse items","Claims & verification","User directory","Audit log"] if u["role"]=="admin" else ["Overview","Browse items","Report an item","My activity","My claims"]
        page = st.radio("NAVIGATION", nav_options, label_visibility="collapsed")
        if st.button("Log out", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        page = "Sign in"

if not st.session_state.user:
    st.markdown('<div class="login-shell"><div class="login-brand"><div class="login-brand-mark">⌕</div><div><div class="login-brand-name">MUJ Lost &amp; Found</div><div class="login-brand-sub">MANIPAL UNIVERSITY JAIPUR</div></div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="login-panel"><div class="login-eyebrow">WELCOME TO MUJ LOST &amp; FOUND</div><h2>Find what matters. Return what belongs.</h2><p class="login-panel-intro">Sign in with your university account to report, find or reclaim belongings.</p>', unsafe_allow_html=True)
    signin, signup = st.tabs(["Sign in","Create account"])
    with signin:
        with st.form("login_form"):
            email = st.text_input("University email", placeholder="name@muj.manipal.edu")
            password = st.text_input("Password", type="password")
            go = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if go:
            user = one("SELECT * FROM users WHERE email=?", (email.lower().strip(),))
            permitted_role = institutional_role(email)
            domain_ok = user is not None and (user["role"] == "admin" or (permitted_role is not None and user["role"] == permitted_role))
            if domain_ok and verify_password(password,user["salt"],user["password_hash"]):
                st.session_state.user = dict(user)
                log_action(user["id"],"LOGIN","Successful sign in")
                st.rerun()
            else:
                st.error("Use your registered university account: @muj.manipal.edu for students or @jaipur.manipal.edu for faculty, with the correct password.")

    with signup:
        with st.form("signup_form"):
            name = st.text_input("Full name")
            email2 = st.text_input("University email address")
            password2 = st.text_input("Create password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            ok = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if ok:
            detected_role = institutional_role(email2)
            if not name.strip() or detected_role is None:
                st.error("Registration is restricted to @muj.manipal.edu student accounts and @jaipur.manipal.edu faculty accounts.")
            elif len(password2)<10 or password2!=confirm:
                st.error("Use a password of at least 10 characters and make both passwords match.")
            elif create_account(name.strip(),email2,password2):
                st.success(f"{'Student' if detected_role == 'student' else 'Faculty'} account created. Sign in to continue.")
                log_action(None,"ACCOUNT_CREATED",f"{detected_role}: {email2.lower().strip()}")
            else:
                st.error("An account with this email already exists.")
    st.markdown('<div class="login-footnote">For MUJ students and faculty · Secure campus access</div></div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user
uid = user["id"]
is_admin = user["role"]=="admin"

if page == "Overview":
    local_hour = datetime.now(ZoneInfo("Asia/Kolkata")).hour
    time_greeting = "Good morning" if 5 <= local_hour < 12 else "Good afternoon" if 12 <= local_hour < 17 else "Good evening"
    display_name = "Admin" if is_admin else escape(user["name"].strip().split()[0])
    welcome_line = f"{time_greeting}, {display_name}."
    welcome_copy = "Here is your administration overview. Review campus reports, monitor claims and keep the service running smoothly." if is_admin else "Welcome to your campus lost and found workspace. Keep track of reports, discover found items and follow your claims."
    st.markdown(f'<div class="hero"><h1>{welcome_line}</h1><p>{welcome_copy}</p></div>', unsafe_allow_html=True)
    total = one("SELECT COUNT(*) n FROM items")["n"]
    lost = one("SELECT COUNT(*) n FROM items WHERE report_type='Lost' AND status='Open'")["n"]
    found = one("SELECT COUNT(*) n FROM items WHERE report_type='Found' AND status='Open'")["n"]
    pending = one("SELECT COUNT(*) n FROM claims WHERE status='Pending'")["n"]
    cols = st.columns(4)
    for col,(label,val,note) in zip(cols,[("Total reports",total,"All campus listings"),("Lost items",lost,"Open reports"),("Found items",found,"Open reports"),("Pending claims",pending,"Awaiting review")]):
        with col: metric(label,val,note)
    st.subheader("Recently reported")
    recent = rows("""SELECT i.id,i.report_type,i.item_name,i.category,i.location,i.event_date,i.status,u.name reporter
                     FROM items i JOIN users u ON i.user_id=u.id ORDER BY i.created_at DESC LIMIT 6""")
    if recent:
        st.dataframe(pd.DataFrame([dict(r) for r in recent]), use_container_width=True, hide_index=True)
    else:
        st.info("No reports yet. Start by reporting a lost or found item.")
    if is_admin:
        st.subheader("Administrator snapshot")
        st.write("Use **Claims & verification** to review reports and ownership submissions. All decisions should be based on evidence and the university's eventual operating policy.")

elif page == "Browse items":
    st.markdown('<div class="hero"><h1>Browse campus items</h1><p>Search reports and narrow results by type, category or location.</p></div>', unsafe_allow_html=True)
    f1,f2,f3 = st.columns(3)
    with f1: q=st.text_input("Search keywords",placeholder="e.g. black wallet")
    with f2: typ=st.selectbox("Report type",["All","Lost","Found"])
    with f3: cat=st.selectbox("Category",["All","Electronics","ID / Cards","Bags","Clothing","Accessories","Books","Keys","Other"])
    sql="""SELECT i.*,u.name reporter FROM items i JOIN users u ON i.user_id=u.id WHERE i.status='Open'"""
    args=[]
    if q: sql+=" AND (i.item_name LIKE ? OR i.description LIKE ? OR i.location LIKE ?)"; args += [f"%{q}%"]*3
    if typ!="All": sql+=" AND i.report_type=?"; args.append(typ)
    if cat!="All": sql+=" AND i.category=?"; args.append(cat)
    sql+=" ORDER BY i.created_at DESC"
    found_rows=rows(sql,args)
    if not found_rows: st.info("No matching open reports found.")
    for r in found_rows:
        with st.container(border=True):
            a,b=st.columns([4,1])
            with a:
                st.markdown(f"**{r['item_name']}**  ·  {r['report_type']}  ·  {r['category']}")
                st.write(r["description"])
                st.caption(f"📍 {r['location']}  •  Date: {r['event_date']}  •  Reported by {r['reporter']}")
                if r["identification_mark"]:
                    st.markdown(f"**Identification mark:** {r['identification_mark']}")
            with b:
                if r["image_path"] and Path(r["image_path"]).exists(): st.image(r["image_path"],use_container_width=True)
                if not is_admin and r["user_id"]!=uid and r["report_type"]=="Found":
                    if st.button("Claim item",key=f"claim_{r['id']}",use_container_width=True):
                        st.session_state[f"claim_item_{r['id']}"]=True
                if st.session_state.get(f"claim_item_{r['id']}"):
                    with st.form(f"claim_form_{r['id']}"):
                        details=st.text_area("Describe identifying details or proof of ownership")
                        submit=st.form_submit_button("Submit claim")
                    if submit:
                        if len(details.strip())<20: st.error("Please provide at least 20 characters of useful identifying detail.")
                        else:
                            with get_conn() as c:
                                c.execute("INSERT INTO claims(item_id,claimant_id,ownership_details,created_at) VALUES(?,?,?,?)",
                                          (r["id"],uid,details.strip(),datetime.now().isoformat(timespec="seconds")))
                            log_action(uid,"CLAIM_SUBMITTED",f"Item #{r['id']}")
                            st.success("Claim submitted for administrator review.")
                            st.session_state[f"claim_item_{r['id']}"]=False
                            st.rerun()

elif page == "Report an item":
    st.markdown('<div class="hero"><h1>Make a report</h1><p>Share clear details so the campus community can help.</p></div>', unsafe_allow_html=True)
    with st.form("report_form",clear_on_submit=True):
        a,b=st.columns(2)
        with a:
            typ=st.radio("I want to report",["Lost","Found"],horizontal=True)
            name=st.text_input("Item name",placeholder="e.g. Black leather wallet")
            category=st.selectbox("Category",["Electronics","ID / Cards","Bags","Clothing","Accessories","Books","Keys","Other"])
            location_label = "Where did you lose the item?" if typ == "Lost" else "Where did you find the item?"
            location_hint = "Enter the campus location where you last had the item, e.g. Academic Block 1, Room 204." if typ == "Lost" else "Enter the exact campus location where you found it, e.g. Central Library, Ground Floor."
            location=st.text_input(location_label,placeholder="e.g. Central Library, Ground Floor",help=location_hint)
        with b:
            event_date=st.date_input("Date lost" if typ == "Lost" else "Date found",value=date.today(),max_value=date.today())
            image_file=st.file_uploader("Upload item photo (optional but recommended)",type=["png","jpg","jpeg"],help="Add a clear photo of the lost or found item to help others recognise it.")
            identification_mark=st.text_input("Identification mark (if any)",placeholder="e.g. initials engraved on the back, a scratch near the corner, a sticker")
            description=st.text_area("Description and identifying details",height=120,placeholder="Colour, brand, size, distinctive features and other useful details...")
        submit=st.form_submit_button("Submit report",type="primary")
    if submit:
        if not name.strip() or not location.strip() or len(description.strip())<15:
            st.error("Please provide the item name, the campus location, and a description of at least 15 characters.")
        else:
            image_path=None
            if image_file:
                suffix=Path(image_file.name).suffix.lower()
                image_path=str(UPLOAD_DIR/f"{secrets.token_hex(12)}{suffix}")
                Path(image_path).write_bytes(image_file.getbuffer())
            with get_conn() as c:
                cur=c.execute("""INSERT INTO items(user_id,report_type,item_name,category,description,location,event_date,image_path,identification_mark,created_at)
                                 VALUES(?,?,?,?,?,?,?,?,?,?)""",
                              (uid,typ,name.strip(),category,description.strip(),location.strip(),event_date.isoformat(),image_path,identification_mark.strip(),datetime.now().isoformat(timespec="seconds")))
                item_id=cur.lastrowid
            log_action(uid,"ITEM_REPORTED",f"{typ} item #{item_id}: {name.strip()}")
            st.success(f"Report #{item_id} submitted and is now visible in Browse items.")

elif page == "My activity":
    st.markdown('<div class="hero"><h1>My activity</h1><p>Review the reports you have submitted.</p></div>', unsafe_allow_html=True)
    data=rows("SELECT * FROM items WHERE user_id=? ORDER BY created_at DESC",(uid,))
    if data:
        for r in data:
            with st.container(border=True):
                a,b=st.columns([4,1])
                with a:
                    st.markdown(f"**#{r['id']} · {r['item_name']}** — {r['report_type']}")
                    st.caption(f"{r['category']} • {r['location']} • {r['event_date']}")
                    if r["identification_mark"]:
                        st.write(f"Identification mark: {r['identification_mark']}")
                with b: st.write(f"**{r['status']}**")
                if is_admin or r["status"]=="Open":
                    if st.button("Mark resolved / closed",key=f"close_{r['id']}"):
                        with get_conn() as c: c.execute("UPDATE items SET status='Resolved' WHERE id=? AND user_id=?",(r["id"],uid))
                        log_action(uid,"ITEM_RESOLVED",f"Item #{r['id']}")
                        st.rerun()
    else: st.info("You have not submitted any reports yet.")

elif page in ("My claims","Claims & verification"):
    st.markdown('<div class="hero"><h1>Claims & verification</h1><p>Transparent review of ownership submissions.</p></div>', unsafe_allow_html=True)
    if is_admin:
        claim_rows=rows("""SELECT c.*,i.item_name,i.report_type,i.location,u.name claimant,u.email
                           FROM claims c JOIN items i ON c.item_id=i.id JOIN users u ON c.claimant_id=u.id
                           ORDER BY CASE c.status WHEN 'Pending' THEN 0 ELSE 1 END,c.created_at DESC""")
    else:
        claim_rows=rows("""SELECT c.*,i.item_name,i.report_type,i.location,u.name claimant
                           FROM claims c JOIN items i ON c.item_id=i.id JOIN users u ON u.id=c.claimant_id
                           WHERE c.claimant_id=? ORDER BY c.created_at DESC""",(uid,))
    if not claim_rows: st.info("No claims to display.")
    for r in claim_rows:
        with st.container(border=True):
            st.markdown(f"**Claim #{r['id']} · {r['item_name']}**")
            st.caption(f"Item #{r['item_id']} • {r['location']} • {r['status']}")
            st.write(r["ownership_details"])
            if is_admin and r["status"]=="Pending":
                note=st.text_input("Review note (optional)",key=f"note_{r['id']}")
                x,y=st.columns(2)
                with x:
                    if st.button("Approve claim",key=f"approve_{r['id']}",type="primary",use_container_width=True):
                        with get_conn() as c:
                            c.execute("UPDATE claims SET status='Approved',admin_note=? WHERE id=?",(note,r["id"]))
                            c.execute("UPDATE items SET status='Resolved' WHERE id=?",(r["item_id"],))
                        log_action(uid,"CLAIM_APPROVED",f"Claim #{r['id']}")
                        st.rerun()
                with y:
                    if st.button("Reject claim",key=f"reject_{r['id']}",use_container_width=True):
                        with get_conn() as c: c.execute("UPDATE claims SET status='Rejected',admin_note=? WHERE id=?",(note,r["id"]))
                        log_action(uid,"CLAIM_REJECTED",f"Claim #{r['id']}")
                        st.rerun()
            elif r["status"]!="Pending" and r["admin_note"]:
                st.caption(f"Administrator note: {r['admin_note']}")

elif page == "User directory" and is_admin:
    st.markdown('<div class="hero"><h1>User directory</h1><p>Registered students, faculty and administrators.</p></div>', unsafe_allow_html=True)
    directory = rows("SELECT id,name,email,role,created_at FROM users ORDER BY created_at DESC")
    st.caption(f"{len(directory)} registered accounts")
    if directory:
        st.dataframe(pd.DataFrame([dict(r) for r in directory]),use_container_width=True,hide_index=True)
    else:
        st.info("No registered accounts yet.")

elif page == "Audit log" and is_admin:
    st.markdown('<div class="hero"><h1>Audit log</h1><p>Recent administrative and account activity.</p></div>', unsafe_allow_html=True)
    audit = rows("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 100")
    if audit:
        st.dataframe(pd.DataFrame([dict(r) for r in audit]),use_container_width=True,hide_index=True)
    else:
        st.info("No activity recorded yet.")
