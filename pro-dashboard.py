import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import openai

# ---------------- CONFIG ----------------
st.set_page_config(page_title="MERIT Pro Dashboard", layout="wide")

UPLOAD_DIR = "uploaded_excels"
SAMPLE_FILE = "sample_data.xlsx"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load environment variables (API key from .env)
load_dotenv()
openai.api_key = os.getenv("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

# ---------------- HEADER ----------------
col1, col2 = st.columns([1, 5])
with col1:
    if os.path.exists("merit_logo.png"):
        st.image("merit_logo.png", width=140)
with col2:
    st.title("MERIT Pro Dashboard")

# ---------------- ROLE SELECTION ----------------
st.sidebar.title("🔑 Role Selection")
role = st.sidebar.radio("Select Role", ["Client", "Admin"])

# ---------------- ADMIN MODE ----------------
if role == "Admin":
    st.header("📂 Admin Dashboard")

    # Simple password gate
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password != "admin123":
        st.warning("Please enter the correct Admin password to continue.")
        st.stop()

    # File uploader
    uploaded_file = st.file_uploader("Upload Excel/CSV File", type=["xlsx", "csv"])
    if uploaded_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"✅ File saved as {filename}")

    # Clear uploads option
    if st.button("🗑️ Clear Upload History"):
        for f in os.listdir(UPLOAD_DIR):
            os.remove(os.path.join(UPLOAD_DIR, f))
        st.success("Upload history cleared!")

    # List available files
    excel_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith((".xlsx", ".csv"))]
    excel_files.sort(reverse=True)

    if not excel_files and os.path.exists(SAMPLE_FILE):
        excel_files = [SAMPLE_FILE]

    if excel_files:
        selected_file = st.selectbox("📂 Select a file to preview", excel_files)
        file_path = os.path.join(UPLOAD_DIR, selected_file) if selected_file != SAMPLE_FILE else SAMPLE_FILE

        # Load file
        if selected_file.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            xls = pd.ExcelFile(file_path)
            sheet = st.sidebar.radio("📑 Choose a sheet", xls.sheet_names)
            df = pd.read_excel(xls, sheet_name=sheet, header=0)

        st.subheader("📋 Data Preview")
        st.dataframe(df.head(50), use_container_width=True)

    else:
        st.info("📂 No files uploaded yet. A sample file will be used for Clients.")

# ---------------- CLIENT MODE ----------------
else:
    st.header("📊 Client Dashboard")

    excel_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith((".xlsx", ".csv"))]
    excel_files.sort(reverse=True)

    if not excel_files and os.path.exists(SAMPLE_FILE):
        excel_files = [SAMPLE_FILE]

    if not excel_files:
        st.warning("⚠️ No data available. Please ask Admin to upload.")
        st.stop()

    selected_file = st.selectbox("📂 Select a file", excel_files)
    file_path = os.path.join(UPLOAD_DIR, selected_file) if selected_file != SAMPLE_FILE else SAMPLE_FILE

    # Load file
    if selected_file.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        xls = pd.ExcelFile(file_path)
        sheet = st.sidebar.radio("📑 Choose a sheet", xls.sheet_names)
        df = pd.read_excel(xls, sheet_name=sheet, header=0)

    st.subheader(f"📋 Data Preview: {selected_file}")

    # Search
    search_term = st.text_input("🔍 Search")
    if search_term:
        mask = df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
        df = df[mask]

    # Filters
    with st.expander("⚙️ Column Filters"):
        for col in df.columns:
            unique_vals = df[col].dropna().unique().tolist()
            if len(unique_vals) < 50:
                selected_vals = st.multiselect(f"Filter {col}", unique_vals)
                if selected_vals:
                    df = df[df[col].isin(selected_vals)]

    st.dataframe(df, use_container_width=True)

    # Charts
    with st.expander("📊 Charts & Insights"):
        chart_type = st.selectbox("Select chart type", ["Bar", "Line", "Pie"])
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        non_numeric_cols = df.select_dtypes(exclude="number").columns.tolist()

        if chart_type and numeric_cols and non_numeric_cols:
            x_axis = st.selectbox("X-axis", non_numeric_cols)
            y_axis = st.selectbox("Y-axis", numeric_cols)

            if chart_type == "Bar":
                fig, ax = plt.subplots()
                df.groupby(x_axis)[y_axis].sum().plot(kind="bar", ax=ax)
                st.pyplot(fig)

            elif chart_type == "Line":
                fig, ax = plt.subplots()
                df.groupby(x_axis)[y_axis].sum().plot(kind="line", marker="o", ax=ax)
                st.pyplot(fig)

            elif chart_type == "Pie":
                fig, ax = plt.subplots()
                df.groupby(x_axis)[y_axis].sum().plot(kind="pie", autopct="%1.1f%%", ax=ax)
                st.pyplot(fig)

    # AI Q&A
    with st.expander("🤖 Ask AI about this data"):
        question = st.text_input("Ask a question about the dataset")
        if question and not df.empty:
            try:
                response = openai.ChatCompletion.create(
                    model="mistralai/mistral-7b-instruct:free",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes tabular data."},
                        {"role": "user", "content": f"Here is the dataset:\n{df.head(50).to_csv(index=False)}"},
                        {"role": "user", "content": question},
                    ],
                )
                st.success(response["choices"][0]["message"]["content"])
            except Exception as e:
                st.error(f"AI request failed: {e}")
