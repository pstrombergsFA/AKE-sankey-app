import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="AKE Sankey", layout="wide")

CSV_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/ake-sankey-app/main/data/financials.csv"

# -----------------------
# AUTH
# -----------------------
def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    users = st.secrets["auth"]["users"]

    if st.button("Login"):
        if username in users and password == users[username]:
            st.session_state["authenticated"] = True
        else:
            st.error("Invalid credentials")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# -----------------------
# LOAD DATA
# -----------------------
df = pd.read_csv(CSV_URL)

# normalize columns just in case
df.columns = df.columns.str.strip().str.lower()

# -----------------------
# UI CONTROLS
# -----------------------
month = st.selectbox("Select month", sorted(df["month"].unique()))
year = st.selectbox("Select year", sorted(df["year"].unique()))

df_filtered = df[(df["month"] == month) & (df["year"] == year)]

# -----------------------
# SANKEY LOGIC
# -----------------------
# ⬇⬇⬇ PASTE YOUR SANKEY CONSTRUCTION CODE HERE ⬇⬇⬇
# it should use df_filtered
# and end with fig = go.Figure(...)

st.plotly_chart(fig, use_container_width=True)
