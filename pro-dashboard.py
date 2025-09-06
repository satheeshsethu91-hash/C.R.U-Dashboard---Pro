import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Configure OpenRouter client
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

# Streamlit config
st.set_page_config(
    page_title="MERIT Pro Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---- Custom Theme & Logo ----
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #0F1E3C;
        }
        .stApp {
            background-color: #F7F9FB;
        }
        h1, h2, h3, h4, h5 {
            color: #0096fa;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.image("merit_logo.png", width=180)

# ---- Role Selection ----
role = st.sidebar.radio("Select Role", ["Admin", "Client"])

# ---- Data Storage ----
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "df" not in st.session_state:
    st.session_state.df = None

# ---- Admin Section ----
if role == "Admin":
    st.title("📂 Admin Panel")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls", "csv"])

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        if uploaded_file.name.endswith(".csv"):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.success("✅ File uploaded successfully!")

        # Preview
        st.subheader("Data Preview")
        st.dataframe(st.session_state.df.head())

    if st.button("Clear Uploaded Data"):
        st.session_state.uploaded_file = None
        st.session_state.df = None
        st.warning("History cleared!")

# ---- Client Section ----
if role == "Client":
    st.title("📊 Client Dashboard")

    if st.session_state.df is not None:
        df = st.session_state.df

        # Show data
        st.subheader("Data Table")
        st.dataframe(df)

        # Search & Filters
        st.subheader("🔎 Search & Filter")
        col = st.selectbox("Select Column", df.columns)
        search_val = st.text_input("Enter value to search")
        if search_val:
            filtered = df[df[col].astype(str).str.contains(search_val, case=False, na=False)]
            st.dataframe(filtered)

        # Charts
        st.subheader("📈 Charts")
        chart_col = st.selectbox("Select Column for Chart", df.columns)
        if df[chart_col].dtype in ["int64", "float64"]:
            st.bar_chart(df[chart_col])
        else:
            st.bar_chart(df[chart_col].value_counts())

        # AI Insights
        st.subheader("🤖 AI Insights")
        question = st.text_area("Ask a question about your data")
        if st.button("Get Answer") and question:
            # Send query to OpenRouter
            response = client.chat.completions.create(
                model="meta-llama/llama-3.1-8b-instruct",
                messages=[
                    {"role": "system", "content": "You are a data assistant. Answer questions based on the provided dataset."},
                    {"role": "user", "content": f"Here is the dataset:\n{df.head(20).to_string()}\n\nQuestion: {question}"}
                ]
            )
            st.markdown(f"**Answer:** {response.choices[0].message['content']}")

    else:
        st.warning("⚠️ No data available. Please ask Admin to upload a file.")
