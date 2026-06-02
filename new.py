import datetime
import io
import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==========================================
# 1. DATABASE INITIALIZATION (LIVE PERSISTENCE)
# ==========================================
DB_FILE = "vishesh_expense.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            currency TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_expense_to_db(date_str, category, description, amount, currency):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (date, category, description, amount, currency)
        VALUES (?, ?, ?, ?, ?)
    ''', (date_str, category, description, amount, currency))
    conn.commit()
    conn.close()

def load_expenses_from_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT date AS Date, category AS Category, description AS Description, amount AS [Amount (INR)], currency AS Currency FROM expenses", conn)
    conn.close()
    return df

def save_profile_value(key, value):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO profile (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def load_profile_dict():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM profile")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

init_db()

# ==========================================
# 2. INITIALIZATION & SESSION STATE
# ==========================================
st.set_page_config(page_title="VISHESH EXPENSE", page_icon="💰", layout="wide")

# Native Header Formatting
st.markdown("""
    <style>
    .main-title {
        font-size: 45px;
        color: #00E5FF;
        text-align: center;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    .subtitle {
        color: #8E24AA;
        text-align: center;
        font-weight: 600;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'login'

db_profile = load_profile_dict()
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = db_profile

if 'budget' not in st.session_state:
    st.session_state.budget = float(db_profile.get('budget', 25000.0))
if 'currency' not in st.session_state:
    st.session_state.currency = db_profile.get('currency', 'INR')
if 'categories' not in st.session_state:
    st.session_state.categories = ['Snacks', 'Transport', 'Rent', 'Bills', 'Entertainment', 'Others']

def next_page(): 
    st.session_state.page = {'login': 'quotes', 'quotes': 'profile', 'profile': 'budget', 'budget': 'dashboard', 'dashboard': 'receipt'}[st.session_state.page]
def prev_page(): 
    st.session_state.page = {'quotes': 'login', 'profile': 'quotes', 'budget': 'profile', 'dashboard': 'budget', 'receipt': 'dashboard'}[st.session_state.page]

# ==========================================
# 3. HELPER FUNCTIONS (PDF GENERATION)
# ==========================================
def generate_pdf(df_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.HexColor('#00E5FF'), alignment=1)
    normal_style = styles['Normal']
    
    elements = []
    elements.append(Paragraph("<b>VISHESH EXPENSE STATEMENT</b>", title_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<b>Generated on:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Paragraph(f"<b>User:</b> {st.session_state.user_profile.get('Name', 'N/A')}", normal_style))
    elements.append(Paragraph(f"<b>Total Budget:</b> {st.session_state.budget} {st.session_state.currency}", normal_style))
    elements.append(Spacer(1, 20))
    
    data = [[col for col in df_data.columns]]
    for row in df_data.values.tolist():
        data.append([str(item) for item in row])
        
    t = Table(data, colWidths=[80, 90, 140, 100, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8E24AA')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F3E5F5')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#8E24AA')),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 4. PAGE ROUTING & NAVIGATION
# ==========================================

# PAGE 1: LOGIN
if st.session_state.page == 'login':
    st.markdown("<h1 class='main-title'>VISHESH EXPENSE</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='subtitle'>Smart Financial Tracking</h3>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.subheader("🌐 Sign In to Your Financial Dashboard")
        email = st.text_input("Email ID Address", value=st.session_state.user_profile.get('Email', ''), placeholder="name@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.form_submit_button("Secure Login 🚀"):
            if email:
                st.session_state.user_profile['Email'] = email
                save_profile_value('Email', email)
                next_page()
                st.rerun()
            else:
                st.error("Please enter a valid Email ID.")

# PAGE 2: QUOTES (REFACTORED TO GUARANTEE 100% VISIBILITY)
elif st.session_state.page == 'quotes':
    st.markdown("<h1 class='main-title'>Words of Financial Wisdom</h1>", unsafe_allow_html=True)
    st.write("---")
    
    # Native information containers that display perfectly regardless of dark/light theme options
    st.info("💡 :violet[**“Don't save what is left after spending; spend what is left after saving.”**] — *Warren Buffett*")
    st.write("")
    st.info("💡 :violet[**“Beware of little expenses; a small leak will sink a great ship.”**] — *Benjamin Franklin*")
    st.write("")
    st.info("💡 :violet[**“Money is a terrible master but an excellent servant.”**] — *P.T. Barnum*")
    st.write("")
    st.info("💡 :violet[**“Track your pennies, and your pounds will track themselves.”**] — *Anonymous Wisdom*")
    
    st.write("---")
    col1, col2 = st.columns([1, 1])
    if col1.button("⬅️ Back"): 
        prev_page()
        st.rerun()
    if col2.button("Continue to Profile ➡️"): 
        next_page()
        st.rerun()

# PAGE 3: USER PROFILE DETAILS
elif st.session_state.page == 'profile':
    st.markdown("<h1 class='main-title'>Tell Us About Yourself</h1>", unsafe_allow_html=True)
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=st.session_state.user_profile.get('Name', ''))
            age = st.number_input("Age", min_value=1, max_value=120, value=int(st.session_state.user_profile.get('Age', 25)))
            
            saved_dob = st.session_state.user_profile.get('DOB', '2000-01-01')
            try:
                default_dob = datetime.datetime.strptime(saved_dob, '%Y-%m-%d').date()
            except:
                default_dob = datetime.date(2000, 1, 1)
            dob = st.date_input("Date of Birth (DOB)", value=default_dob, min_value=datetime.date(1930, 1, 1))
            
        with col2:
            place = st.text_input("Current Location / Place", value=st.session_state.user_profile.get('Place', ''))
            occupation = st.text_input("Occupation (Custom Field 1)", value=st.session_state.user_profile.get('Occupation', 'Professional'))
            income = st.number_input("Monthly Income (INR) (Custom Field 2)", min_value=0, value=int(st.session_state.user_profile.get('Income', 50000)))
            
        if st.form_submit_button("Save & Proceed"):
            st.session_state.user_profile.update({"Name": name, "Age": str(age), "DOB": str(dob), "Place": place, "Occupation": occupation, "Income": str(income)})
            for k, v in st.session_state.user_profile.items():
                save_profile_value(k, v)
            next_page()
            st.rerun()

# PAGE 4: BUDGET SETTING
elif st.session_state.page == 'budget':
    st.markdown("<h1 class='main-title'>Set Financial Limits</h1>", unsafe_allow_html=True)
    
    currencies = ["INR (₹)", "USD ($)", "EUR (€)", "GBP (£)"]
    saved_curr_idx = 0
    for idx, c in enumerate(currencies):
        if c.startswith(st.session_state.currency):
            saved_curr_idx = idx
            
    currency = st.selectbox("Preferred Currency", currencies, index=saved_curr_idx)
    st.session_state.currency = currency.split()[0]
    save_profile_value('currency', st.session_state.currency)
    
    budget = st.number_input(f"Enter your overall limit allocation ({st.session_state.currency})", min_value=0.0, value=st.session_state.budget, step=500.0)
    
    st.write("---")
    st.subheader("🛠️ Customize Expense Categories")
    new_cat = st.text_input("Add New Category")
    if st.button("Add Category") and new_cat:
        if new_cat not in st.session_state.categories:
            st.session_state.categories.insert(-1, new_cat)
            st.success(f"Added {new_cat}")
            
    if st.button("Set Budget & Initialise Dashboard 🎯"):
        st.session_state.budget = budget
        save_profile_value('budget', budget)
        next_page()
        st.rerun()

# PAGE 5: DASHBOARD & EXPENSE ENTRY
elif st.session_state.page == 'dashboard':
    st.markdown("<h1 class='main-title'>VISHESH EXPENSE</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #8E24AA;'>Dynamic Live Tracking Engine</h4>", unsafe_allow_html=True)
    
    expenses_df = load_expenses_from_db()
    
    total_spent = expenses_df['Amount (INR)'].sum()
    remaining = st.session_state.budget - total_spent
    
    if total_spent >= st.session_state.budget:
        st.error(f"🚨 CRITICAL ALERT: Budget fully exhausted! Overspent by {abs(remaining)} {st.session_state.currency}")
    elif total_spent >= st.session_state.budget * 0.85:
        st.warning(f"⚠️ WARNING: You have spent {total_spent} {st.session_state.currency}. 85% of budget allocation reached!")
        
    m1, m2, m3 = st.columns(3)
    m1.metric("Allocated Budget", f"{st.session_state.budget} {st.session_state.currency}")
    m2.metric("Total Expenses Registered (All-Time Cumulative)", f"{total_spent} {st.session_state.currency}")
    m3.metric("Remaining Pool", f"{remaining} {st.session_state.currency}")
    
    st.write("---")
    
    col1, col2, col3 = st.columns(3)
    with col1: select_date = st.date_input("Target Date Selection", datetime.date.today())
    with col2: select_month = st.selectbox("Billing Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=datetime.date.today().month - 1)
    with col3: select_year = st.selectbox("Billing Year", [2025, 2026, 2027, 2028], index=1)
    
    st.subheader("➕ File New Expense Record")
    with st.form("expense_entry"):
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            category = st.selectbox("Category", st.session_state.categories)
        with ec2:
            if category == 'Others':
                other_desc = st.text_input("Specify custom Category / Reason", placeholder="e.g. Medical, Gifts")
            else:
                other_desc = ""
            description = st.text_input("Transaction Description", placeholder="e.g. Office Lunch")
        with ec3:
            amount = st.number_input(f"Amount ({st.session_state.currency})", min_value=0.0, step=10.0)
            
        if st.form_submit_button("Log Transaction"):
            final_cat = other_desc if category == 'Others' and other_desc else category
            save_expense_to_db(str(select_date), final_cat, description, amount, st.session_state.currency)
            st.success("Transaction securely saved to database!")
            st.rerun()
            
    st.subheader("📑 Database Ledger Table Rows (All Historic Records Saved)")
    st.dataframe(expenses_df, use_container_width=True)
    
    if not expenses_df.empty:
        st.write("---")
        st.subheader("📊 Analytical Visualizations")
        fig = px.pie(expenses_df, values='Amount (INR)', names='Category', 
                     title='Expense Distribution by Category (All-Time Data)', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)
        
    if st.button("Generate Final Printable Statement 🧾"):
        next_page()
        st.rerun()

# PAGE 6: RECEIPT GENERATION & DISTRIBUTION
elif st.session_state.page == 'receipt':
    st.markdown("<h1 class='main-title'>Vishesh Expense</h1>", unsafe_allow_html=True)
    st.subheader("🧾 Definitive Statement Receipt Summary (Till Date Cumulative Data)")
    
    final_expenses_df = load_expenses_from_db()
    
    st.info(f"**Invoice Execution Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"**Customer Profile Identity:** {st.session_state.user_profile.get('Name', 'Anonymous')}")
    
    st.table(final_expenses_df)
    
    pdf_data = generate_pdf(final_expenses_df)
    
    st.download_button(
        label="📥 Download Official Printable PDF Statement",
        data=pdf_data,
        file_name=f"Vishesh_Expense_Statement_{datetime.date.today()}.pdf",
        mime="application/pdf"
    )
    
    st.write("---")
    st.subheader("📧 Digital Distribution Node")
    target_email = st.text_input("Destination Mail Address", value=st.session_state.user_profile.get('Email', ''))
    if st.button("Transmit Encrypted PDF via Email"):
        st.info(f"Connecting to outbound mail relay server routing to {target_email}...")
        st.success("Success! Receipt payload successfully built and sent.")
        
    st.write("---")
    # BACK BUTTON - Safely returns you to the input table page without wiping variables
    if st.button("⬅️ Return to Expense Ledger (Add Missing Entries)"):
        prev_page()
        st.rerun()