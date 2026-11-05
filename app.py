"""Campus Lost & Found — Streamlit pilot application."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import date, datetime
import hashlib
import hmac
import secrets

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DB_PATH = ROOT / "lost_found.db"
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Campus Lost & Found", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")

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

def inject_css(theme):
    if theme == "Dark":
        bg, panel, text, muted, border, accent = "#0b1220", "#111c30", "#edf3ff", "#9aabc4", "#253550", "#67a8ff"
    else:
        bg, panel, text, muted, border, accent = "#f4f7fb", "#ffffff", "#17233b", "#66758d", "#e2e8f0", "#2563eb"
    st.markdown(f"""
    <style>
    .stApp {{background:{bg}; color:{text};}}
    [data-testid="stSidebar"] {{background:{panel}; border-right:1px solid {border};}}
    .block-container {{padding-top:2rem; max-width:1400px;}}
    .hero {{padding:1.5rem 1.7rem; border:1px solid {border}; border-radius:18px;
      background:linear-gradient(120deg,{panel},{bg}); margin-bottom:1.2rem;}}
    .hero h1 {{font-size:2.15rem; margin:0 0 .35rem 0; color:{text};}}
    .hero p {{color:{muted}; margin:0; font-size:1.02rem;}}
    .metric-card {{background:{panel}; border:1px solid {border}; border-radius:15px; padding:1rem 1.1rem;}}
    .metric-label {{font-size:.83rem;color:{muted};}}
    .metric-value {{font-size:1.85rem;font-weight:700;color:{text};}}
    .muted {{color:{muted};}}
    div[data-testid="stForm"] {{border:1px solid {border}; border-radius:14px; padding:1rem;}}
    .stButton>button[kind="primary"] {{background:{accent}; border:0;}}
    </style>
    """, unsafe_allow_html=True)

def metric(label, value, note=""):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-label">{note}</div></div>', unsafe_allow_html=True)

def create_account(name,email,password):
    salt = secrets.token_hex(16)
    digest = hash_password(password,salt)
    try:
        with get_conn() as c:
            c.execute("INSERT INTO users(name,email,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)",
                      (name,email.lower().strip(),digest,salt,"student",datetime.now().isoformat(timespec="seconds")))
        return True
    except sqlite3.IntegrityError:
        return False

init_db()
if "user" not in st.session_state:
    st.session_state.user = None
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"
inject_css(st.session_state.theme)

with st.sidebar:
    st.markdown("## 🔎 Campus Connect")
    st.caption("LOST & FOUND • MUJ PILOT")
    st.session_state.theme = st.selectbox("Appearance", ["Dark","Light"], index=0 if st.session_state.theme=="Dark" else 1)
    inject_css(st.session_state.theme)
    st.divider()
    if st.session_state.user:
        u = st.session_state.user
        st.markdown(f"**{u['name']}**")
        st.caption(u["role"].title())
        nav_options = ["Overview","Browse items","Report an item","My activity","Claims & verification"] if u["role"]=="admin" else ["Overview","Browse items","Report an item","My activity","My claims"]
        page = st.radio("NAVIGATION", nav_options, label_visibility="collapsed")
        if st.button("Log out", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    else:
        page = "Sign in"

if not st.session_state.user:
    st.markdown('<div class="hero"><h1>Lost something on campus?</h1><p>A single place to report, discover and reunite belongings with their owners.</p></div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.subheader("Campus Lost & Found")
        st.write("A proposed digital service for the university community. Search listings, report an item and submit an ownership claim through one transparent workflow.")
        st.markdown("- Verified student accounts and administrator review\n- Searchable lost and found listings\n- Claim tracking and status updates\n- Designed for a future SLCM integration")
        st.info("Pilot note: This is a prototype. It is not currently connected to MUJ SLCM or an official university identity provider.")
    with right:
        signin, signup = st.tabs(["Sign in","Create account"])
        with signin:
            with st.form("login_form"):
                email = st.text_input("University email / account email")
                password = st.text_input("Password", type="password")
                go = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if go:
                user = one("SELECT * FROM users WHERE email=?", (email.lower().strip(),))
                if user and verify_password(password,user["salt"],user["password_hash"]):
                    st.session_state.user = dict(user)
                    log_action(user["id"],"LOGIN","Successful sign in")
                    st.rerun()
                else:
                    st.error("Email or password is incorrect.")
            st.caption("Initial demo admin: admin@campus.local / ChangeMe-Admin123! — change this immediately before any real deployment.")
        with signup:
            with st.form("signup_form"):
                name = st.text_input("Full name")
                email2 = st.text_input("Email address")
                password2 = st.text_input("Create password", type="password")
                confirm = st.text_input("Confirm password", type="password")
                ok = st.form_submit_button("Create student account", type="primary", use_container_width=True)
            if ok:
                if not name.strip() or "@" not in email2 or len(password2)<10 or password2!=confirm:
                    st.error("Enter a name and valid email; use at least 10 characters and make passwords match.")
                elif create_account(name.strip(),email2,password2):
                    st.success("Account created. Sign in to continue.")
                    log_action(None,"ACCOUNT_CREATED",email2.lower().strip())
                else:
                    st.error("An account with this email already exists.")
    st.stop()

user = st.session_state.user
uid = user["id"]
is_admin = user["role"]=="admin"

if page == "Overview":
    st.markdown(f'<div class="hero"><h1>Good to see you, {user["name"].split()[0]}.</h1><p>Your campus lost and found workspace. Keep every report and claim in one place.</p></div>', unsafe_allow_html=True)
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
            location=st.text_input("Last seen / found at",placeholder="e.g. Central Library, Ground Floor")
        with b:
            event_date=st.date_input("Date",value=date.today(),max_value=date.today())
            image_file=st.file_uploader("Item image (optional)",type=["png","jpg","jpeg"])
            description=st.text_area("Description and identifying details",height=150,placeholder="Colour, brand, distinguishing marks, contents (avoid exposing sensitive information)...")
        submit=st.form_submit_button("Submit report",type="primary")
    if submit:
        if not name.strip() or not location.strip() or len(description.strip())<15:
            st.error("Please provide an item name, location and a description of at least 15 characters.")
        else:
            image_path=None
            if image_file:
                suffix=Path(image_file.name).suffix.lower()
                image_path=str(UPLOAD_DIR/f"{secrets.token_hex(12)}{suffix}")
                Path(image_path).write_bytes(image_file.getbuffer())
            with get_conn() as c:
                cur=c.execute("""INSERT INTO items(user_id,report_type,item_name,category,description,location,event_date,image_path,created_at)
                                 VALUES(?,?,?,?,?,?,?,?,?)""",
                              (uid,typ,name.strip(),category,description.strip(),location.strip(),event_date.isoformat(),image_path,datetime.now().isoformat(timespec="seconds")))
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

if is_admin:
    st.sidebar.divider()
    st.sidebar.caption("ADMINISTRATION")
    with st.sidebar:
        if st.button("User directory",use_container_width=True):
            st.session_state.show_users=True
        if st.button("Audit log",use_container_width=True):
            st.session_state.show_audit=True
    if st.session_state.get("show_users"):
        with st.expander("User directory",expanded=True):
            st.dataframe(pd.DataFrame([dict(r) for r in rows("SELECT id,name,email,role,created_at FROM users ORDER BY created_at DESC")]),use_container_width=True,hide_index=True)
    if st.session_state.get("show_audit"):
        with st.expander("Recent audit activity",expanded=True):
            st.dataframe(pd.DataFrame([dict(r) for r in rows("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 100")]),use_container_width=True,hide_index=True)
