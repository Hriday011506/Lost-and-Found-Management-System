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
    """Use the local SQLite database for this demonstration deployment."""
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
        CREATE TABLE IF NOT EXISTS claim_comments (
          id INTEGER PRIMARY KEY AUTOINCREMENT, claim_id INTEGER NOT NULL,
          author_id INTEGER NOT NULL, comment TEXT NOT NULL, created_at TEXT NOT NULL,
          FOREIGN KEY(claim_id) REFERENCES claims(id),
          FOREIGN KEY(author_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS audit_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id INTEGER,
          action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
        );
        """)
        item_columns = {row[1] for row in c.execute("PRAGMA table_info(items)").fetchall()}
        if "identification_mark" not in item_columns:
            c.execute("ALTER TABLE items ADD COLUMN identification_mark TEXT DEFAULT ''")

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
        linear-gradient(90deg,rgba(36,20,9,.08),rgba(36,20,9,.02) 58%,rgba(36,20,9,.05)),
        url('https://raw.githubusercontent.com/Hriday011506/Lost-and-Found-Management-System/main/static/campus_bg.jpg') center center/cover no-repeat,
        linear-gradient(125deg,#8B431D,#F0A13F);
    }
    .stApp:has(.login-shell) [data-testid="stMain"],
    .stApp:has(.login-shell) [data-testid="stMainBlockContainer"] {background:transparent !important; position:relative; z-index:1;}
    .stApp:has(.login-shell) .block-container {max-width:none !important; padding:2.5rem 0 2rem 10.2% !important;}
    .stApp:has(.login-shell) [data-testid="stHorizontalBlock"] {align-items:flex-start !important;}
    .login-shell {max-width:430px; margin:0 0 1.1rem 0; position:relative; z-index:2;}
    .login-brand {display:flex; align-items:center; gap:.8rem; margin:0 0 1rem .1rem; color:#fff;
      text-shadow:0 1px 8px rgba(0,0,0,.35);}
    .login-brand-mark {width:42px; height:42px; display:grid; place-items:center; border-radius:12px;
      background:var(--o600); color:#fff; font-size:1.35rem; font-weight:800;}
    .login-brand-name {font-size:1.1rem; font-weight:800; color:#fff; letter-spacing:-.02em;}
    .login-brand-sub {font-size:.7rem; color:rgba(255,255,255,.95); letter-spacing:.12em; font-weight:700;}
    .login-visual {display:none;}
    .stApp:has(.login-shell) [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTabs"]) {
      background:#fff !important; border:1px solid rgba(255,255,255,.9) !important;
      border-radius:24px !important; padding:1.25rem 1.45rem 1rem !important;
      width:100%; max-width:430px; min-height:0;
      box-shadow:0 18px 55px rgba(45,25,12,.22) !important;
    }
    .stApp:has(.login-shell) [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTabs"]):hover {
      border-color:#fff !important; box-shadow:0 18px 55px rgba(45,25,12,.22) !important;
    }
    /* Keep the complete login choice and validation area readable over the photo. */
    .stApp:has(.login-shell) [data-testid="stVerticalBlockBorderWrapper"]:has(.login-eyebrow):has([data-testid="stButton"]) {
      background:rgba(255,255,255,.98) !important;
      border:1px solid #fff !important;
      border-radius:22px !important;
      padding:1.35rem 1.45rem 1.15rem !important;
      box-shadow:0 18px 55px rgba(45,25,12,.24) !important;
      max-width:570px !important;
    }
    .stApp:has(.login-shell) [data-testid="stVerticalBlockBorderWrapper"]:has(.login-eyebrow):has([data-testid="stButton"]) > div {
      background:transparent !important;
    }
    .stApp:has(.login-shell) [data-testid="stAlert"] {
      background:#FFF4EC !important;
      border:1px solid #D9541E !important;
      border-left:5px solid #B8430F !important;
      border-radius:10px !important;
      color:#702B12 !important;
      box-shadow:0 4px 14px rgba(45,25,12,.12) !important;
    }
    .stApp:has(.login-shell) [data-testid="stAlert"] *,
    .stApp:has(.login-shell) [data-testid="stAlert"] p {
      color:#702B12 !important;
      -webkit-text-fill-color:#702B12 !important;
      font-weight:600 !important;
    }
    .stApp:has(.login-shell) [data-testid="stButton"] button[kind="primary"] {
      background:#0874BE !important; border:1px solid #0874BE !important; color:#fff !important;
      -webkit-text-fill-color:#fff !important; font-size:.88rem !important; font-weight:750 !important;
      min-height:3.1rem !important; padding:.55rem .65rem !important; border-radius:7px !important;
      box-shadow:none !important; white-space:normal !important;
    }
    .stApp:has(.login-shell) [data-testid="stButton"] button[kind="primary"]:hover {
      background:#075F9D !important; border-color:#075F9D !important;
    }
    .login-separator {height:1px; background:#DDE5EB; margin:1.25rem 0;}
    .selected-login-label {font-size:.95rem; font-weight:750; color:var(--ink); margin:.8rem 0 .25rem;}
    .stApp:has(.login-shell) [data-testid="stExpander"] {border:0 !important; border-radius:8px !important;}
    .stApp:has(.login-shell) [data-testid="stExpander"] summary {font-weight:750; font-size:1rem;}
    .login-panel h2 {font-size:1.42rem; margin:.1rem 0 .3rem; color:var(--ink);}
    .login-panel-intro {color:var(--muted); margin:0 0 .9rem; font-size:.88rem;}
    .login-eyebrow {font-size:.7rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:var(--o700); margin-bottom:.55rem;}
    .login-footnote {font-size:.74rem; color:var(--muted); text-align:center; margin-top:.85rem;}
    .stApp:has(.login-shell) [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stForm"] {
      border:0 !important; padding:.55rem 0 0 !important; box-shadow:none !important; background:transparent !important;
    }
    .stApp:has(.login-shell) [data-testid="stTabs"] [role="tab"] {font-size:.88rem !important; padding:.6rem .8rem !important;}
    @media (max-width:900px) {
      .stApp:has(.login-shell) .block-container {padding:1.5rem 1rem !important;}
      .stApp:has(.login-shell) [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTabs"]) {max-width:100%;}
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
    if "login_mode" not in st.session_state:
        st.session_state.login_mode = None

    left, empty_space = st.columns([0.43, 0.57], gap="small")
    with left:
        st.markdown('<div class="login-shell"><div class="login-brand"><div class="login-brand-mark">⌕</div><div><div class="login-brand-name">MUJ Lost &amp; Found</div><div class="login-brand-sub">MANIPAL UNIVERSITY JAIPUR</div></div></div></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="login-eyebrow">WELCOME TO MUJ LOST &amp; FOUND</div><h2>Find what matters. Return what belongs.</h2><p class="login-panel-intro">Choose your university account type to continue.</p>', unsafe_allow_html=True)

            faculty_col, student_col, admin_col = st.columns(3, gap="small")
            with faculty_col:
                if st.button("Login – Faculty", key="faculty_login_choice", type="primary", use_container_width=True):
                    st.session_state.login_mode = "faculty"
            with student_col:
                if st.button("Login – Student", key="student_login_choice", type="primary", use_container_width=True):
                    st.session_state.login_mode = "student"
            with admin_col:
                if st.button("Admin Login", key="admin_login_choice", type="primary", use_container_width=True):
                    st.session_state.login_mode = "admin"

            st.markdown('<div class="login-separator"></div>', unsafe_allow_html=True)

            if st.session_state.login_mode in ("student", "faculty", "admin"):
                selected_role = st.session_state.login_mode
                selected_label = {"student": "MUJ Student", "faculty": "MUJ Faculty", "admin": "Administrator"}[selected_role]
                placeholder = "Administrator email" if selected_role == "admin" else ("name@muj.manipal.edu" if selected_role == "student" else "name@jaipur.manipal.edu")
                st.markdown(f'<div class="selected-login-label">{selected_label} sign in</div>', unsafe_allow_html=True)
                with st.form(f"{selected_role}_login_form"):
                    email = st.text_input("Email address", placeholder=placeholder, key=f"{selected_role}_email")
                    password = st.text_input("Password", type="password", key=f"{selected_role}_password")
                    go = st.form_submit_button(f"Continue as {selected_label}", type="primary", use_container_width=True)
                if go:
                    login_user = one("SELECT * FROM users WHERE email=?", (email.lower().strip(),))
                    permitted_role = institutional_role(email)
                    role_valid = (
                        login_user is not None
                        and login_user["role"] == selected_role
                        and (selected_role == "admin" or permitted_role == selected_role)
                    )
                    if role_valid and verify_password(password, login_user["salt"], login_user["password_hash"]):
                        st.session_state.user = dict(login_user)
                        log_action(login_user["id"], "LOGIN", f"{selected_label} sign in")
                        st.rerun()
                    elif selected_role == "admin":
                        st.error("Administrator sign-in failed. Check the provisioned admin email and password.")
                    else:
                        expected_domain = "@muj.manipal.edu" if selected_role == "student" else "@jaipur.manipal.edu"
                        st.error(f"Please use a registered {selected_label} account ending in {expected_domain} and its correct password.")

            with st.expander("Create a new student or faculty account"):
                with st.form("signup_form"):
                    name = st.text_input("Full name", key="signup_name")
                    email2 = st.text_input("University email address", key="signup_email")
                    password2 = st.text_input("Create password", type="password", key="signup_password")
                    confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
                    ok = st.form_submit_button("Create account", type="primary", use_container_width=True)
                if ok:
                    detected_role = institutional_role(email2)
                    if not name.strip() or detected_role is None:
                        st.error("Registration is restricted to @muj.manipal.edu student accounts and @jaipur.manipal.edu faculty accounts.")
                    elif len(password2)<10 or password2!=confirm:
                        st.error("Use a password of at least 10 characters and make both passwords match.")
                    elif create_account(name.strip(),email2,password2):
                        st.success(f"{'Student' if detected_role == 'student' else 'Faculty'} account created. You can now sign in.")
                        log_action(None,"ACCOUNT_CREATED",f"{detected_role}: {email2.lower().strip()}")
                    else:
                        st.error("An account with this email already exists.")
            st.markdown('<div class="login-footnote">For MUJ students and faculty · Secure campus access</div>', unsafe_allow_html=True)
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
            description=st.text_area("Description (optional)",height=100,placeholder="Add any extra details that may help identify the item...")
        submit=st.form_submit_button("Submit report",type="primary")
    if submit:
        if not name.strip() or not location.strip():
            st.error("Please provide the item name and the campus location.")
        else:
            image_path=None
            if image_file:
                suffix=Path(image_file.name).suffix.lower()
                image_path=str(UPLOAD_DIR/f"{secrets.token_hex(12)}{suffix}")
                Path(image_path).write_bytes(image_file.getbuffer())
            with get_conn() as c:
                if st.secrets.get("DATABASE_URL", ""):
                    cur=c.execute("""INSERT INTO items(user_id,report_type,item_name,category,description,location,event_date,image_path,identification_mark,created_at)
                                     VALUES(?,?,?,?,?,?,?,?,?,?) RETURNING id""",
                                  (uid,typ,name.strip(),category,description.strip(),location.strip(),event_date.isoformat(),image_path,identification_mark.strip(),datetime.now().isoformat(timespec="seconds")))
                    item_id=cur.fetchone()["id"]
                else:
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
                if is_admin:
                    if st.button("Mark resolved / closed",key=f"close_{r['id']}"):
                        with get_conn() as c: c.execute("UPDATE items SET status='Resolved' WHERE id=? AND user_id=?",(r["id"],uid))
                        log_action(uid,"ITEM_RESOLVED",f"Item #{r['id']}")
                        st.rerun()
    else: st.info("You have not submitted any reports yet.")

elif page in ("My claims","Claims & verification"):
    st.markdown('<div class="hero"><h1>Claims & verification</h1><p>Review ownership claims, exchange additional information and track decisions.</p></div>', unsafe_allow_html=True)
    if is_admin:
        claim_rows=rows("""SELECT c.*,i.item_name,i.report_type,i.location,u.name claimant,u.email
                           FROM claims c JOIN items i ON c.item_id=i.id JOIN users u ON i.user_id<>-1 AND u.id=c.claimant_id
                           ORDER BY CASE c.status WHEN 'Pending' THEN 0 ELSE 1 END,c.created_at DESC""")
    else:
        claim_rows=rows("""SELECT c.*,i.item_name,i.report_type,i.location,u.name claimant
                           FROM claims c JOIN items i ON i.id=c.item_id JOIN users u ON u.id=c.claimant_id
                           WHERE c.claimant_id=? ORDER BY c.created_at DESC""",(uid,))
    if not claim_rows:
        st.info("No claims to display.")
    for r in claim_rows:
        with st.container(border=True):
            st.markdown(f"**Claim #{r['id']} · {r['item_name']}**")
            st.caption(f"Item #{r['item_id']} • {r['location']} • Status: {r['status']}")
            st.write("**Original ownership details**")
            st.write(r["ownership_details"])
            if r["admin_note"]:
                st.info(f"Administrator decision note: {r['admin_note']}")
            conversation=rows("""SELECT cc.comment,cc.created_at,u.name,u.role
                                 FROM claim_comments cc JOIN users u ON u.id=cc.author_id
                                 WHERE cc.claim_id=? ORDER BY cc.created_at""",(r["id"],))
            if conversation:
                st.markdown("**Follow-up discussion**")
                for msg in conversation:
                    st.caption(f"{msg['name']} · {msg['role'].title()} · {msg['created_at']}")
                    comment_text=msg["comment"]
                    photo_marker="[Supporting photograph: "
                    if photo_marker in comment_text:
                        before,photo_part=comment_text.split(photo_marker,1)
                        photo_path=photo_part.split("]",1)[0]
                        if before.strip():
                            st.write(before.strip())
                        if Path(photo_path).exists():
                            st.image(photo_path,caption="Student-provided claim evidence",width=320)
                        else:
                            st.caption("Supporting photograph is unavailable on this server.")
                    else:
                        st.write(comment_text)
            if not is_admin and r["status"]=="Needs info":
                with st.form(f"followup_{r['id']}"):
                    reply=st.text_area("Additional information requested by the administrator",placeholder="Add ownership details or explain the evidence...")
                    evidence_photo=st.file_uploader("Upload supporting photograph (optional)",type=["png","jpg","jpeg"],key=f"claim_evidence_{r['id']}",help="Upload a photo that supports your ownership claim.")
                    send=st.form_submit_button("Submit information",type="primary")
                if send:
                    if len(reply.strip())<10 and not evidence_photo:
                        st.error("Please provide written details or upload a supporting photograph.")
                    else:
                        evidence_path=None
                        if evidence_photo:
                            suffix=Path(evidence_photo.name).suffix.lower()
                            evidence_path=str(UPLOAD_DIR/f"claim_{r['id']}_{secrets.token_hex(10)}{suffix}")
                            Path(evidence_path).write_bytes(evidence_photo.getbuffer())
                        message=reply.strip() or "Supporting photograph uploaded."
                        if evidence_path:
                            message += f"\n[Supporting photograph: {evidence_path}]"
                        with get_conn() as c:
                            c.execute("INSERT INTO claim_comments(claim_id,author_id,comment,created_at) VALUES(?,?,?,?)",
                                      (r["id"],uid,message,datetime.now().isoformat(timespec="seconds")))
                            c.execute("UPDATE claims SET status='Pending',admin_note='' WHERE id=?",(r["id"],))
                        log_action(uid,"CLAIM_FOLLOWUP",f"Requested information submitted for claim #{r['id']}")
                        st.success("Your information and evidence have been sent to the administrator for review.")
                        st.rerun()
            if is_admin and r["status"]=="Pending":
                note=st.text_area("Administrator comment (required)",key=f"note_{r['id']}",placeholder="Explain the decision or specify what information is needed...")
                x,y,z=st.columns(3)
                with x:
                    if st.button("Approve",key=f"approve_{r['id']}",type="primary",use_container_width=True):
                        if not note.strip():
                            st.error("Please add a comment before approving.")
                        else:
                            with get_conn() as c:
                                c.execute("UPDATE claims SET status='Approved',admin_note=? WHERE id=?",(note.strip(),r["id"]))
                                c.execute("UPDATE items SET status='Resolved' WHERE id=?",(r["item_id"],))
                                c.execute("INSERT INTO claim_comments(claim_id,author_id,comment,created_at) VALUES(?,?,?,?)",
                                          (r["id"],uid,note.strip(),datetime.now().isoformat(timespec="seconds")))
                            log_action(uid,"CLAIM_APPROVED",f"Claim #{r['id']}")
                            st.rerun()
                with y:
                    if st.button("Request info",key=f"request_info_{r['id']}",use_container_width=True):
                        if not note.strip():
                            st.error("Please explain what information the student must provide.")
                        else:
                            with get_conn() as c:
                                c.execute("UPDATE claims SET status='Needs info',admin_note=? WHERE id=?",(note.strip(),r["id"]))
                                c.execute("INSERT INTO claim_comments(claim_id,author_id,comment,created_at) VALUES(?,?,?,?)",
                                          (r["id"],uid,note.strip(),datetime.now().isoformat(timespec="seconds")))
                            log_action(uid,"CLAIM_INFO_REQUESTED",f"Additional information requested for claim #{r['id']}")
                            st.rerun()
                with z:
                    if st.button("Reject",key=f"reject_{r['id']}",use_container_width=True):
                        if not note.strip():
                            st.error("Please explain why the claim is being rejected.")
                        else:
                            with get_conn() as c:
                                c.execute("UPDATE claims SET status='Rejected',admin_note=? WHERE id=?",(note.strip(),r["id"]))
                                c.execute("INSERT INTO claim_comments(claim_id,author_id,comment,created_at) VALUES(?,?,?,?)",
                                          (r["id"],uid,note.strip(),datetime.now().isoformat(timespec="seconds")))
                            log_action(uid,"CLAIM_REJECTED",f"Claim #{r['id']}")
                            st.rerun()

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
