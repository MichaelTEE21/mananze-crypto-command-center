import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="MCCC Dashboard",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# SAMPLE DATA
# -----------------------------
projects = pd.DataFrame([
    {
        "Project": "FLOP",
        "Category": "AI",
        "Status": "Testnet",
        "Score": 92,
        "Potential": "$$$$",
    },
    {
        "Project": "DAC",
        "Category": "Blockchain",
        "Status": "Testnet",
        "Score": 88,
        "Potential": "$$$",
    },
    {
        "Project": "IOPN",
        "Category": "DePIN",
        "Status": "Mainnet Soon",
        "Score": 85,
        "Potential": "$$$",
    },
    {
        "Project": "Zenith",
        "Category": "DeFi",
        "Status": "Testnet",
        "Score": 81,
        "Potential": "$$$",
    },
    {
        "Project": "Stabilizer",
        "Category": "DeFi",
        "Status": "Testnet",
        "Score": 78,
        "Potential": "$$",
    },
])

# -----------------------------
# HEADER
# -----------------------------
st.title("🚀 MCCC")
st.caption("Mananze Crypto & Computing Command Center")

st.divider()

# -----------------------------
# KPI CARDS
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Projects Tracked", len(projects))
col2.metric("Average Score", f"{projects['Score'].mean():.0f}/100")
col3.metric("Testnets", len(projects[projects["Status"] == "Testnet"]))
col4.metric("High Potential", len(projects[projects["Potential"] == "$$$$"]))

st.divider()

# -----------------------------
# PROJECT TABLE
# -----------------------------
st.subheader("📋 Project Intelligence")

st.dataframe(
    projects,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# CHARTS
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Project Scores")

    fig = px.bar(
        projects,
        x="Project",
        y="Score",
        text="Score",
        title="Opportunity Score"
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🧠 Categories")

    category_counts = projects["Category"].value_counts().reset_index()
    category_counts.columns = ["Category", "Projects"]

    fig2 = px.pie(
        category_counts,
        names="Category",
        values="Projects",
        title="Projects by Category"
    )

    st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# PROJECT FILTER
# -----------------------------
st.divider()

st.subheader("🔎 Explore Projects")

category = st.selectbox(
    "Filter by category",
    ["All"] + sorted(projects["Category"].unique())
)

if category == "All":
    filtered = projects
else:
    filtered = projects[projects["Category"] == category]

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# API SECTION
# -----------------------------
st.divider()

st.subheader("🌐 API Intelligence")

st.info(
    "API connections will be added here. "
    "This section will eventually pull live blockchain, "
    "market, project and testnet data."
)

st.caption("MCCC v0.1 — Intelligence Layer")