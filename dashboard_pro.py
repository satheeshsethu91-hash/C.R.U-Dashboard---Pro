import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from pandasai import SmartDataframe
from pandasai.llm.local_llm import LocalLLM
from PIL import Image, ImageDraw, ImageFont
import plotly.express as px

# -----------------------------
# Custom Logo
# -----------------------------
def create_logo():
    width, height = 311, 117
    bg_color = (15, 30, 60)
    border_color = (255, 255, 255)
    text_color = (255, 255, 255)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    border_thickness = 7
    draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=border_thickness)

    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()

    text = "MERIT"
    text_width, text_height = draw.textsize(text, font=font)
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill=text_color, font=font)

    os.makedirs("assets", exist_ok=True)
    img_path = "assets/merit_logo.png"
    img.save(img_path)
    return img_path

logo_path = create_logo()
st.set_page_config(page_title="MERIT Pro Insights", layout="wide")
st.image(logo_path, width=200)
st.title("📊 MERIT Pro Insights")

# -----------------------------
# Upload Folder
# -----------------------------
UPLOAD_DIR = "uploaded_excels"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# Role Selection
# -----------------------------
role = st.sidebar.radio("Select Role", ["Admin", "Client"])

# -----------------------------
# Admin Mode
# -----------------------------
if role == "Admin":
    st.subheader("🔑 Admin Dashboard")

    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password != "admin123":
        st.warning("Please enter the correct Admin password.")
        st.stop()

    # Upload files
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ File saved as {filename}")

    # -----------------------------
    # Admin File Management
    # -----------------------------
    st.subheader("🗂️ Uploaded Files Management")
    excel_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith((".xlsx", ".csv"))]
    excel_files.sort(reverse=True)

    if excel_files:
        st.write("Currently uploaded files:")
        for f in excel_files:
            st.write(f)

        # Delete selected
        files_to_delete = st.multiselect("Select file(s) to delete", excel_files)
        if st.button("Delete Selected File(s)"):
            for f in files_to_delete:
                os.remove(os.path.join(UPLOAD_DIR, f))
            st.success(f"Deleted {len(files_to_delete)} file(s).")
            st.experimental_rerun()

        # Clear all
        if st.button("Clear All Uploaded Files"):
            for f in excel_files:
                os.remove(os.path.join(UPLOAD_DIR, f))
            st.success("All uploaded files cleared!")
            st.experimental_rerun()
    else:
        st.info("No files uploaded yet.")

# -----------------------------
# Client Mode
# -----------------------------
else:
    st.subheader("👤 Client Dashboard")

    # List uploaded files
    excel_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith((".xlsx", ".csv"))]
    excel_files.sort(reverse=True)

    if not excel_files:
        st.warning("⚠️ No files uploaded yet. Please ask Admin to upload.")
        st.stop()

    # Select file
    selected_file = st.selectbox("📂 Select a file", excel_files)
    file_path = os.path.join(UPLOAD_DIR, selected_file)

    # Load file
    if selected_file.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        xls = pd.ExcelFile(file_path)
        sheet = st.sidebar.radio("Choose a sheet", xls.sheet_names)
        df = pd.read_excel(file_path, sheet_name=sheet)

    # -----------------------------
    # Data Table + Search + Filters
    # -----------------------------
    st.subheader("📋 Data Preview")
    search_term = st.text_input("🔍 Search across all columns")
    display_df = df.copy()
    if search_term:
        mask = display_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
        display_df = display_df[mask]

    with st.expander("⚙️ Column Filters"):
        for col in display_df.columns:
            unique_vals = display_df[col].dropna().unique().tolist()
            if len(unique_vals) < 50:
                selected_vals = st.multiselect(f"Filter {col}", unique_vals)
                if selected_vals:
                    display_df = display_df[display_df[col].isin(selected_vals)]

    st.dataframe(display_df, use_container_width=True)

    # -----------------------------
    # Quick Charts
    # -----------------------------
    st.subheader("📈 Quick Charts")
    numeric_cols = display_df.select_dtypes(include="number").columns.tolist()
    categorical_cols = display_df.select_dtypes(include="object").columns.tolist()

    if numeric_cols and categorical_cols:
        x_axis = st.selectbox("Select X-axis (categorical)", categorical_cols)
        y_axis = st.selectbox("Select Y-axis (numeric)", numeric_cols)
        chart_type = st.selectbox("Select Chart Type", ["Bar", "Line", "Scatter", "Pie"])

        if chart_type == "Bar":
            fig = px.bar(display_df, x=x_axis, y=y_axis)
        elif chart_type == "Line":
            fig = px.line(display_df, x=x_axis, y=y_axis)
        elif chart_type == "Scatter":
            fig = px.scatter(display_df, x=x_axis, y=y_axis)
        elif chart_type == "Pie":
            fig = px.pie(display_df, names=x_axis, values=y_axis)
        st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # AI Q&A using Local LLM
    # -----------------------------
    st.subheader("🤖 Ask AI About Your Data")
    question = st.text_input("Type your question (e.g., 'Show me average sales by region')")

    if question:
        try:
            llm = LocalLLM(model="llama-2-7b-chat.ggmlv3.q4_0.bin")  # path to your downloaded model
            sdf = SmartDataframe(display_df, config={"llm": llm})
            answer = sdf.chat(question)
            st.write("### Answer:")
            st.write(answer)
        except Exception as e:
            st.error(f"Error running AI Q&A: {e}")

    # -----------------------------
    # Auto Insights
    # -----------------------------
    st.subheader("📝 Auto Insights")
    st.write(f"Dataset has **{display_df.shape[0]} rows** and **{display_df.shape[1]} columns**")
    st.write("Missing values per column:")
    st.dataframe(display_df.isna().sum())
    st.write("Basic statistics for numeric columns:")
    st.dataframe(display_df.describe())
