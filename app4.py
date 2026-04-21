import streamlit as st
import pyodbc
import pandas as pd
from datetime import datetime

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="Supply Chain Management", layout="wide")

# =============================
# 🎨 CSS (UNCHANGED)
# =============================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2f7, #dfe9f3);
    font-family: 'Segoe UI';
}
h1, h2, h3 {
    color: #1f4e79;
    font-weight: 700;
}
.tile {
    background: linear-gradient(135deg, #ffffff, #f4f7fb);
    padding: 30px;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.1);
}
.tile-icon {
    font-size: 50px;
}
.stButton>button {
    width: 100%;
    background: linear-gradient(90deg, #1f77b4, #4facfe);
    color: white;
    border-radius: 10px;
    padding: 8px;
}
[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)
# =============================
# LOGIN SESSION INIT
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "login_error" not in st.session_state:
    st.session_state.login_error = ""

# Dummy users (you can later move to DB)
users = {
    "admin": "admin123",
    "user": "user123"
}

# =============================
# LOGIN PAGE (FINAL VERSION)
# =============================
def login_page():

    # ---------- GLASS STYLE ----------
    st.markdown("""
        <style>
        .glass {
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(8px);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0px 8px 20px rgba(0,0,0,0.15);
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------- TITLE ----------
    st.markdown("""
        <h1 style='text-align:center; color:#1f4e79;'>
            🏭 Supply Chain Management 
        </h1>
      
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- CENTERED LOGIN ----------
    col1, col2, col3 = st.columns([3,2,3])

    with col2:

        st.markdown("<h3 style='text-align:center;'>🔐 Login</h3>", unsafe_allow_html=True)

        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Login", key="login_btn"):

            if username.strip() == "" or password.strip() == "":
                st.session_state.login_error = "⚠️ Please enter both fields"

            elif username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.login_error = ""
                st.success("Login Successful ✅")
                st.rerun()

            else:
                st.session_state.login_error = "❌ Invalid Username or Password"

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        st.markdown('</div>', unsafe_allow_html=True)
# DB CONNECTION
# =============================
@st.cache_resource
def get_connection():
    return pyodbc.connect(
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=C:\Users\bolla\PycharmProjects\supplychainmanagement\SCM.accdb;'
    )

conn = get_connection()
cursor = conn.cursor()

# =============================
# SESSION STATE
# =============================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "history" not in st.session_state:
    st.session_state.history = []

def go(page):
    st.session_state.history.append(st.session_state.page)
    st.session_state.page = page

def back():
    if st.session_state.history:
        st.session_state.page = st.session_state.history.pop()

# =============================
# HEADER
# =============================
def header(title):
    col1, col2, col3 = st.columns([1,6,2])

    with col1:
        if st.button("⬅ Back"):
            back()

    with col2:
        st.title(title)

    with col3:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "home"
            st.session_state.history = []
            st.rerun()
# =============================
# STOCK FUNCTION
# =============================
def get_stock(material):
    cursor.execute("""
        SELECT 
        SUM(IIF(Movement_Type=101,Quantity,0)) -
        SUM(IIF(Movement_Type IN (201,261),Quantity,0))
        FROM Inventory_Transactions WHERE Material=?
    """,(material,))
    r = cursor.fetchone()
    return r[0] if r and r[0] else 0

# =============================
# DOC NUMBER
# =============================
def generate_doc_number(movement):
    if movement == 101:
        prefix = 5100000000
        cursor.execute("SELECT MAX(Material_Document) FROM User_Transactions WHERE Movement_Type=101")
    else:
        prefix = 4920000000
        cursor.execute("SELECT MAX(Material_Document) FROM User_Transactions WHERE Movement_Type IN (201,261)")
    last = cursor.fetchone()[0]
    return str(int(last)+1) if last else str(prefix+1)

# =============================
# CONFIRM POST
# =============================
@st.dialog("Confirm Transaction")
def confirm_post(material, movement, plant, qty, amt):
    doc = generate_doc_number(movement)

    if st.button("Confirm"):
        cursor.execute("""
            INSERT INTO User_Transactions
            (Material, Movement_Type, Plant, Quantity, Amount, Material_Document, Posting_Date, Del_Indicator)
            VALUES (?,?,?,?,?,?,?,?)
        """,(material, movement, plant, qty, amt, doc, datetime.now(), "No"))

        cursor.execute("""
            INSERT INTO Inventory_Transactions
            (Material, Plant, Movement_Type, Quantity, Amount)
            VALUES (?,?,?,?,?)
        """,(material, plant, movement, qty, amt))

        conn.commit()
        st.success(f"Posted Doc: {doc}")
        st.rerun()
# =============================
# LOGIN ROUTING (ADD THIS BLOCK)
# =============================
if not st.session_state.logged_in:
    login_page()
    st.stop()
# =============================
# HOME (FINAL CLEAN VERSION)
# =============================
if st.session_state.page == "home":

    # ---------- TITLE ----------
    st.markdown(
        "<h1 style='text-align:center;'>📊 SUPPLY CHAIN MANAGEMENT</h1>",
        unsafe_allow_html=True
    )

    # -------- TOP ROW (3 tiles centered) --------
    c1, c2, c3, c4, c5 = st.columns([1,2,2,2,1])

    with c2:
        st.markdown(
            '<div class="tile"><div class="tile-icon">📦</div></div>',
            unsafe_allow_html=True
        )
        if st.button("Material Master"):
            go("material")

    with c3:
        st.markdown(
            '<div class="tile"><div class="tile-icon">📊</div></div>',
            unsafe_allow_html=True
        )
        if st.button("Stock Position"):
            go("stock")

    with c4:
        st.markdown(
            '<div class="tile"><div class="tile-icon">🔄</div></div>',
            unsafe_allow_html=True
        )
        if st.button("Transactions"):
            go("transaction")

    # spacing
    st.markdown("<br><br>", unsafe_allow_html=True)

    # -------- BOTTOM ROW (2 tiles centered) --------
    c6, c7, c8, c9 = st.columns([2,2,2,2])

    with c7:
        st.markdown(
            '<div class="tile"><div class="tile-icon">📑</div></div>',
            unsafe_allow_html=True
        )
        if st.button("Reports"):
            go("reports")

    with c8:
        st.markdown(
            '<div class="tile"><div class="tile-icon">📈</div></div>',
            unsafe_allow_html=True
        )
        if st.button("Dashboard"):
            go("dashboard")

    # -------- LOGOUT SECTION (BOTTOM CENTER) --------
    st.markdown("<br><br><hr>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3,2,3])

    with col2:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.page = "home"
            st.session_state.history = []
            st.rerun()
# =============================
# MATERIAL MASTER (UNCHANGED)
# =============================
elif st.session_state.page == "material":
    header("📦 Material Master")

    df = pd.read_sql("SELECT * FROM Dim_Material", conn)
    action = st.selectbox("Action", ["Create","Update","Delete","Display"])

    if action == "Create":
        mat = st.text_input("Material")
        desc = st.text_input("Description")
        uom = st.selectbox("UOM", ["EA","KG","L","M","NOS"])

        if st.button("Create"):
            if mat and desc:
                cursor.execute("INSERT INTO Dim_Material VALUES (?,?,?)",(mat,desc,uom))
                conn.commit()
                st.success("Created")
            else:
                st.error("All fields required")

    elif action == "Update":
        df["disp"] = df["Material"] + " - " + df["Material_Desc"]
        sel = st.selectbox("Material", df["disp"])
        mat = sel.split(" - ")[0]

        desc = st.text_input("Description")
        uom = st.selectbox("UOM", ["EA","KG","L","M","NOS"])

        if st.button("Update"):
            cursor.execute("""
                UPDATE Dim_Material
                SET Material_Desc=?, BaseUOM=?
                WHERE Material=?
            """,(desc,uom,mat))
            conn.commit()
            st.success("Updated")

    elif action == "Delete":
        df["disp"] = df["Material"] + " - " + df["Material_Desc"]
        sel = st.selectbox("Material", df["disp"])
        mat = sel.split(" - ")[0]

        if st.button("Delete"):
            cursor.execute("DELETE FROM Dim_Material WHERE Material=?",(mat,))
            conn.commit()
            st.success("Deleted")

    st.dataframe(df)

# =============================
# STOCK POSITION (FIXED)
# =============================
elif st.session_state.page == "stock":
    header("📦 Stock Position")

    mat_df = pd.read_sql("SELECT * FROM Dim_Material", conn)
    material = st.selectbox("Material", mat_df["Material"] + " - " + mat_df["Material_Desc"]).split(" - ")[0]

    plant_df = pd.read_sql("SELECT * FROM Plant_Master", conn)
    plant = st.selectbox("Plant", plant_df["Plant"] + " - " + plant_df["Plant_Desc"]).split(" - ")[0]

    df = pd.read_sql("SELECT * FROM Inventory_Transactions", conn)
    f = df[(df["Material"] == material) & (df["Plant"] == plant)]

    if f.empty:
        st.warning("No data found")
        st.stop()

    gr = f[f["Movement_Type"] == 101]["Quantity"].sum()
    cons = f[f["Movement_Type"].isin([201,261])]["Quantity"].sum()
    stock = gr - cons

    c1, c2, c3 = st.columns(3)
    c1.metric("GR", gr)
    c2.metric("Consumption", cons)
    c3.metric("Stock", stock)

    st.dataframe(f)

# =============================
# TRANSACTIONS (FIXED)
# =============================
elif st.session_state.page == "transaction":
    header("🔄 Transactions")

    tab1, tab2 = st.tabs(["Create Transaction", "Delete Transaction"])

    with tab1:
        mat_df = pd.read_sql("SELECT * FROM Dim_Material", conn)
        material = st.selectbox("Material", mat_df["Material"] + " - " + mat_df["Material_Desc"]).split(" - ")[0]

        st.info(f"Stock: {get_stock(material)}")

        movement = int(st.selectbox("Movement", ["101","201","261"]))

        plant_df = pd.read_sql("SELECT * FROM Plant_Master", conn)
        plant = st.selectbox("Plant", plant_df["Plant"] + " - " + plant_df["Plant_Desc"]).split(" - ")[0]

        qty = st.number_input("Quantity")
        amt = st.number_input("Amount")

        if st.button("Post"):
            confirm_post(material, movement, plant, qty, amt)

    with tab2:
        doc = st.text_input("Document Number")
        if st.button("Delete Transaction"):
            cursor.execute("""
                UPDATE User_Transactions
                SET Del_Indicator='Yes'
                WHERE Material_Document=?
            """,(doc,))
            conn.commit()
            st.success("Deleted")

# =============================
# REPORTS (FIXED)
# =============================
elif st.session_state.page == "reports":
    header("📑 Reports")

    df = pd.read_sql("SELECT * FROM User_Transactions", conn)
    df["Posting_Date"] = pd.to_datetime(df["Posting_Date"])

    st.metric("Transactions", len(df))
    st.metric("Quantity", df["Quantity"].sum())
    st.metric("Value", df["Amount"].sum())

    st.line_chart(df.groupby(df["Posting_Date"].dt.to_period("M").dt.to_timestamp())["Quantity"].sum())
    st.bar_chart(df.groupby("Material")["Quantity"].sum().sort_values(ascending=False).head(10))

    st.dataframe(df)
# =============================
# DASHBOARD (UPGRADED)
# =============================
elif st.session_state.page == "dashboard":
    header("📊 Dashboard")

    df = pd.read_sql("""
      SELECT u.*, m.Material_Desc
      FROM User_Transactions u
      LEFT JOIN Dim_Material m
      ON u.Material = m.Material
      """, conn)

    df["Posting_Date"] = pd.to_datetime(df["Posting_Date"])
    today = pd.Timestamp.now()

    # =============================
    # 🔹 KPIs
    # =============================
    st.subheader("📌 Key Performance Indicators")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Transactions", len(df))
    c2.metric("Total Quantity", int(df["Quantity"].sum()))
    c3.metric("Total Value", int(df["Amount"].sum()))

    # =============================
    # 🔹 Monthly Trend
    # =============================
    st.subheader("📈 Monthly Consumption Trend")

    monthly = df.groupby(
        df["Posting_Date"].dt.to_period("M").dt.to_timestamp()
    )["Quantity"].sum()

    st.line_chart(monthly)

    # =============================
    # 🔹 Material Status
    # =============================
    st.subheader("📦 Material Status (Activity Based)")

    status = df.groupby("Material")["Posting_Date"].max().reset_index()
    status["Days"] = (today - status["Posting_Date"]).dt.days

    status["Status"] = status["Days"].apply(
        lambda x: "Active" if x <= 30 else "Slow Moving" if x <= 90 else "Dead Stock"
    )

    st.bar_chart(status["Status"].value_counts())

    # =============================
    # 🔹 TOP 20 MATERIALS
    # =============================
    cons = df[df["Movement_Type"].isin([201, 261])]

    top20 = cons.groupby("Material")["Quantity"].sum().nlargest(20).index
    cons_top = cons[cons["Material"].isin(top20)]

    # =============================
    # 🔹 Last Consumption
    # =============================
    st.subheader("⏳ Last Consumption (Top 20 Materials)")

    last = cons_top.groupby("Material")["Posting_Date"].max().reset_index()
    last["Days Since Last Use"] = (today - last["Posting_Date"]).dt.days

    last_sorted = last.sort_values("Days Since Last Use", ascending=False)

    st.bar_chart(last_sorted.set_index("Material")["Days Since Last Use"])

    # =============================
    # 🔹 Average Consumption
    # =============================
    st.subheader("📊 Average Consumption (Top 20 Materials)")

    avg = cons_top.groupby("Material")["Quantity"].mean().sort_values(ascending=False)

    st.bar_chart(avg)

    # =============================
    # 🔹 NEW: Top 10 Materials
    # =============================
    st.subheader("🏆 Top 10 Materials by Consumption")

    top10 = cons.groupby("Material")["Quantity"].sum().sort_values(ascending=False).head(10)

    st.bar_chart(top10)

    # =============================
    # 🔹 NEW: Plant-wise Consumption
    # =============================
    st.subheader("🏭 Plant-wise Consumption")

    plant = cons.groupby("Plant")["Quantity"].sum().sort_values(ascending=False)

    st.bar_chart(plant)

    # =============================
    # 🔽 DOWNLOAD REPORT
    # =============================
    st.subheader("⬇️ Download Dashboard Data")

    # Convert full dataset to CSV
    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download Full Report (CSV)",
        data=csv,
        file_name="SCM_Dashboard_Report.csv",
        mime="text/csv"
    )