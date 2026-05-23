"""
Interactive Placement Dashboard
Displays prediction results, recommendations, and analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import shutil

from config import (
    SNAPSHOT_DIR, DB_CONN_STRING, TEXTFILES_DIR, RAW_DIR,
    RAW_STUDENT_DETAILS_PATH, RAW_EXAM_PATH, RAW_SKILLS_PATH,
    RAW_ATTENDANCE_PATH, RAW_COMPANY_RULES_PATH
)
from sqlalchemy import create_engine
import warnings

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
TEXTFILES_DIR.mkdir(parents=True, exist_ok=True)

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Placement Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        text-align: center;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 1em;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5em;
        border-radius: 0.5em;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ===================== FILE UPLOAD FUNCTIONS =====================
def save_uploaded_file(uploaded_file, destination_path):
    """Save uploaded CSV file to raw directory"""
    try:
        # Read the uploaded file
        df = pd.read_csv(uploaded_file)
        
        # Save to destination
        df.to_csv(destination_path, index=False)
        return True, "File uploaded successfully!"
    except Exception as e:
        return False, f"Error uploading file: {str(e)}"

def show_file_upload_section():
    """Display file upload interface"""
    st.subheader("📤 Upload Data Files")
    st.info("Upload CSV files to replace existing data. The pipeline will process these files when you run it.")
    
    # Create columns for file uploads
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Student Details**")
        student_details_file = st.file_uploader(
            "Upload student_details.csv",
            type="csv",
            key="student_details_upload"
        )
        if student_details_file is not None:
            success, message = save_uploaded_file(student_details_file, RAW_STUDENT_DETAILS_PATH)
            if success:
                st.success("✓ " + message)
            else:
                st.error(message)
    
    with col2:
        st.write("**Exam Data**")
        exam_file = st.file_uploader(
            "Upload exam_cell.csv",
            type="csv",
            key="exam_upload"
        )
        if exam_file is not None:
            success, message = save_uploaded_file(exam_file, RAW_EXAM_PATH)
            if success:
                st.success("✓ " + message)
            else:
                st.error(message)
    
    with col3:
        st.write("**Skills Portal**")
        skills_file = st.file_uploader(
            "Upload skills_portal.csv",
            type="csv",
            key="skills_upload"
        )
        if skills_file is not None:
            success, message = save_uploaded_file(skills_file, RAW_SKILLS_PATH)
            if success:
                st.success("✓ " + message)
            else:
                st.error(message)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Attendance**")
        attendance_file = st.file_uploader(
            "Upload attendance.csv",
            type="csv",
            key="attendance_upload"
        )
        if attendance_file is not None:
            success, message = save_uploaded_file(attendance_file, RAW_ATTENDANCE_PATH)
            if success:
                st.success("✓ " + message)
            else:
                st.error(message)
    
    with col2:
        st.write("**Company Rules**")
        company_rules_file = st.file_uploader(
            "Upload company_rules.csv",
            type="csv",
            key="company_rules_upload"
        )
        if company_rules_file is not None:
            success, message = save_uploaded_file(company_rules_file, RAW_COMPANY_RULES_PATH)
            if success:
                st.success("✓ " + message)
            else:
                st.error(message)
    
    with col3:
        st.write("**Backlogs (Optional)**")
        st.markdown("*Currently not included in pipeline*")
    
    st.divider()

# ===================== DATA LOADING =====================
@st.cache_data
def load_data():
    """Load all prediction data from CSV files"""
    try:
        predictions_df = pd.read_csv(SNAPSHOT_DIR / "predictions_df.csv")
        student_recs = pd.read_csv(SNAPSHOT_DIR / "student_recommendations.csv")
        company_shortlists = pd.read_csv(SNAPSHOT_DIR / "company_shortlists.csv")
        students_merged_predictions = pd.read_csv(SNAPSHOT_DIR / "students_tables.csv")
        return predictions_df, student_recs, company_shortlists, students_merged_predictions
    except FileNotFoundError:
        return None, None, None, None
    except Exception as e:
        return None, None, None, None

def check_data_exists():
    """Check if prediction data files exist"""
    required_files = [
        SNAPSHOT_DIR / "predictions_df.csv",
        SNAPSHOT_DIR / "student_recommendations.csv",
        SNAPSHOT_DIR / "company_shortlists.csv",
        SNAPSHOT_DIR / "students_tables.csv"
    ]
    return all(f.exists() for f in required_files)

def start_pipeline_job():
    import logging
    from utils.config_log import CONFIG_LOGGER
    from utils.logger import LOGGER_FUNCTION
    from utils.hashing import HASHING_FUNCTION
    from pathlib import Path, PurePath

    from pipeline.p_1_ingestion import ingest_all_sources
    from pipeline.p_2_cleaning import clean_all_sources
    from pipeline.p_3_preprocessing import preprocess_all_sources
    from pipeline.p_4_eligibility import build_eligibility_view
    from pipeline.p_5_storage import run_storage_stage
    from pipeline.p_6_prediction import run_predictions_stage

    try:
        all_data = ingest_all_sources()

        TEXTFILES_DIR.mkdir(parents=True, exist_ok=True)

        with open(TEXTFILES_DIR / "ingested_data.txt", "w") as f:
            student_details_data = all_data["student_details_data"]
            exam_data = all_data["exam_data"]
            skills_data = all_data["skills_data"]
            attendance_data = all_data["attendance_data"]
            company_rules_data = all_data["company_rules_data"]

            f.writelines(f"student details data: {student_details_data.to_string()}\n\n")
            f.writelines(f"exam data: {exam_data.to_string()}\n\n")
            f.writelines(f"skills data: {skills_data.to_string()}\n\n")
            f.writelines(f"attendance data: {attendance_data.to_string()}\n\n")
            f.writelines(f"company rules data: {company_rules_data.to_string()}\n\n")
            
        cleaned_data = clean_all_sources(all_data)

        with open(TEXTFILES_DIR /"cleaned_data.txt", "w") as f:
            student_details_data = cleaned_data["student_details_data"]
            exam_data = cleaned_data["exam_data"]
            skills_data = cleaned_data["skills_data"]
            attendance_data = cleaned_data["attendance_data"]
            company_rules_data = cleaned_data["company_rules_data"]

            f.writelines(f"student details data: {student_details_data.to_string()}\n\n")
            f.writelines(f"exam data: {exam_data.to_string()}\n\n")
            f.writelines(f"skills data: {skills_data.to_string()}\n\n")
            f.writelines(f"attendance data: {attendance_data.to_string()}\n\n")
            f.writelines(f"company rules data: {company_rules_data.to_string()}\n\n")
        preprocessed_data = preprocess_all_sources(cleaned_data)

        with open(TEXTFILES_DIR /"preprocessed_data.txt", "w") as f:
            student_details_data = preprocessed_data["student_details_data"]
            exam_data = preprocessed_data["exam_data"]
            skills_data = preprocessed_data["skills_data"]
            attendance_data = preprocessed_data["attendance_data"]
            company_rules_data = preprocessed_data["company_rules_data"]

            f.writelines(f"student details data: {student_details_data.to_string()}\n\n")
            f.writelines(f"exam data: {exam_data.to_string()}\n\n")
            f.writelines(f"skills data: {skills_data.to_string()}\n\n")
            f.writelines(f"attendance data: {attendance_data.to_string()}\n\n")
            f.writelines(f"company rules data: {company_rules_data.to_string()}\n\n")

        eligibility_data = build_eligibility_view(preprocessed_data)

        # Extract the two dataframes
        students_df = eligibility_data['students']
        student_company_match_df = eligibility_data['student_company_match']

        with open(TEXTFILES_DIR / "eligibility_data.txt", "w") as f:
            f.writelines(f"========== STUDENTS TABLE ==========\n")
            f.writelines(f"Columns: {list(students_df.columns)}\n")
            f.writelines(f"Shape: {students_df.shape}\n\n")
            f.writelines(f"{students_df.to_string()}\n\n")
            
            f.writelines(f"\n========== STUDENT_COMPANY_MATCH TABLE ==========\n")
            f.writelines(f"Columns: {list(student_company_match_df.columns)}\n")
            f.writelines(f"Shape: {student_company_match_df.shape}\n\n")
            f.writelines(f"{student_company_match_df.to_string()}\n\n")


        run_storage_stage(students_df, student_company_match_df)

        predictions_df, student_recommendations_df, company_shortlists_df, students_merged_df = run_predictions_stage(student_company_match_df, students_df)

        with open(TEXTFILES_DIR / "predictions_data.txt", "w") as f:
            f.writelines(f"========== PREDICTIONS TABLE ==========\n")
            f.writelines(f"Columns: {list(predictions_df.columns)}\n")
            f.writelines(f"Shape: {predictions_df.shape}\n\n")
            f.writelines(f"{predictions_df.to_string()}\n\n")

            f.writelines(f"\n========== STUDENT_RECOMMENDATIONS TABLE ==========\n")
            f.writelines(f"Columns: {list(student_recommendations_df.columns)}\n")
            f.writelines(f"Shape: {student_recommendations_df.shape}\n\n")
            f.writelines(f"{student_recommendations_df.to_string()}\n\n")

            f.writelines(f"\n========== COMPANY_SHORTLISTS TABLE ==========\n")
            f.writelines(f"Columns: {list(company_shortlists_df.columns)}\n")
            f.writelines(f"Shape: {company_shortlists_df.shape}\n\n")
            f.writelines(f"{company_shortlists_df.to_string()}\n\n")

            f.writelines(f"\n========== STUDENTS_MERGED TABLE ==========\n")
            f.writelines(f"Columns: {list(students_merged_df.columns)}\n")
            f.writelines(f"Shape: {students_merged_df.shape}\n\n")
            f.writelines(f"{students_merged_df.to_string()}\n\n")
        
        return True
    except Exception as e:
        return e


def run_pipeline():
    """Execute the entire data pipeline"""
    import subprocess
    import sys
    
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔄 Starting pipeline execution...")
        progress_bar.progress(10)
        #run function instead
        result = start_pipeline_job()
        # Run the main pipeline script
        # result = subprocess.run(
        #     [sys.executable, "Data Pipeline/main.py"],
        #     cwd=str(Path(__file__).resolve().parent.parent),
        #     capture_output=True,
        #     text=True,
        #     timeout=300
        # )
        
        if result:#.returncode == 0
            progress_bar.progress(100)
            status_text.text(f"✅ Pipeline completed successfully! ")#{result.stdout}
            st.success("Pipeline executed successfully! Please refresh the page to see the data.")
            # Clear cache to reload data
            st.cache_data.clear()
            return True
        else:
            st.error(f"Pipeline execution failed: {result}")#\n{result.stderr}
            return False
    except subprocess.TimeoutExpired:
        st.error("Pipeline execution timed out after 5 minutes.")
        return False
    except Exception as e:
        st.error(f"Error running pipeline: {e}")
        return False

# ===================== HELPER FUNCTIONS =====================
def get_prediction_color(pred):
    """Return color based on prediction level"""
    colors = {"High": "#2ecc71", "Medium": "#f39c12", "Low": "#e74c3c"}
    return colors.get(pred, "#95a5a6")

def get_top_companies_by_prediction(predictions_df):
    """Get companies with most 'High' predictions"""
    high_pred = predictions_df[predictions_df["prediction"] == "High"]
    company_counts = high_pred["company_name"].value_counts().head(10)
    return company_counts

def get_student_readiness_distribution(predictions_df):
    """Get distribution of readiness scores"""
    return predictions_df.groupby("student_id")["readiness_score"].mean()

# ===================== MAIN DASHBOARD =====================

# Load data
predictions_df, student_recs, company_shortlists, students_merged_predictions = load_data()

if predictions_df is None:
    # Data doesn't exist - show initialization screen
    st.markdown('<h1 class="main-header">📊 Placement Prediction Dashboard</h1>', unsafe_allow_html=True)
    
    st.warning("⚠️ No prediction data found. Upload source files and run the pipeline to generate data.")
    
    # Show file upload section
    show_file_upload_section()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Next Steps")
        st.markdown("""
        1. **Upload CSV Files**: Upload your source data files above (student details, exam scores, attendance, skills, and company rules)
        2. **Run Pipeline**: Click the button below to execute the entire data pipeline from ingestion through prediction
        3. **View Analytics**: Once complete, the dashboard will display comprehensive analytics
        
        **First run may take a few minutes.**
        """)
        
        if st.button("▶️ Run Pipeline Now", key="run_pipeline_button", use_container_width=True):
            run_pipeline()
    
    st.stop()

# Header
st.markdown('<h1 class="main-header">📊 Placement Prediction Dashboard</h1>', unsafe_allow_html=True)

# Pipeline control in sidebar
st.sidebar.title("⚙️ Controls")

# Expandable section for file uploads in sidebar
with st.sidebar.expander("📤 Upload New Files"):
    st.write("Replace data files and rerun the pipeline")
    
    if st.button("Show Upload Interface", key="show_upload_btn"):
        st.session_state.show_upload = True
    
    if st.session_state.get("show_upload", False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Student Details**")
            student_file = st.file_uploader("student_details.csv", type="csv", key="sb_student")
            if student_file:
                save_uploaded_file(student_file, RAW_STUDENT_DETAILS_PATH)
                st.success("✓ Uploaded")
        
        with col2:
            st.write("**Exam Data**")
            exam_file = st.file_uploader("exam_cell.csv", type="csv", key="sb_exam")
            if exam_file:
                save_uploaded_file(exam_file, RAW_EXAM_PATH)
                st.success("✓ Uploaded")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Skills Portal**")
            skills_file = st.file_uploader("skills_portal.csv", type="csv", key="sb_skills")
            if skills_file:
                save_uploaded_file(skills_file, RAW_SKILLS_PATH)
                st.success("✓ Uploaded")
        
        with col2:
            st.write("**Attendance**")
            attendance_file = st.file_uploader("attendance.csv", type="csv", key="sb_attendance")
            if attendance_file:
                save_uploaded_file(attendance_file, RAW_ATTENDANCE_PATH)
                st.success("✓ Uploaded")
        
        st.write("**Company Rules**")
        company_file = st.file_uploader("company_rules.csv", type="csv", key="sb_company")
        if company_file:
            save_uploaded_file(company_file, RAW_COMPANY_RULES_PATH)
            st.success("✓ Uploaded")

if st.sidebar.button("🔄 Refresh Pipeline Data", key="refresh_pipeline", help="Re-run the entire pipeline with current data"):
    with st.spinner("Running pipeline..."):
        run_pipeline()
        st.rerun()

# ===================== SIDEBAR FILTERS =====================
st.sidebar.title("🔍 Filters")

# Prediction filter
selected_prediction = st.sidebar.multiselect(
    "Prediction Level",
    options=predictions_df["prediction"].unique(),
    default=predictions_df["prediction"].unique()
)

# Eligibility filter
show_eligible_only = st.sidebar.checkbox("Show Eligible Only", value=False)

# Readiness score range
min_readiness, max_readiness = st.sidebar.slider(
    "Readiness Score Range",
    min_value=int(predictions_df["readiness_score"].min()),
    max_value=int(predictions_df["readiness_score"].max()),
    value=(int(predictions_df["readiness_score"].min()), int(predictions_df["readiness_score"].max()))
)

# Apply filters
filtered_df = predictions_df[
    (predictions_df["prediction"].isin(selected_prediction)) &
    (predictions_df["readiness_score"] >= min_readiness) &
    (predictions_df["readiness_score"] <= max_readiness)
]

if show_eligible_only:
    filtered_df = filtered_df[filtered_df["eligible"] == 1]

# ===================== KEY METRICS =====================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Student-Company Pairs", len(filtered_df))

with col2:
    eligible_count = len(filtered_df[filtered_df["eligible"] == 1])
    st.metric("Eligible Pairs", eligible_count)

with col3:
    high_pred_count = len(filtered_df[filtered_df["prediction"] == "High"])
    st.metric("High Placement Likelihood", high_pred_count)

with col4:
    avg_readiness = filtered_df["readiness_score"].mean()
    st.metric("Avg Readiness Score", f"{avg_readiness:.1f}", delta=f"{avg_readiness - predictions_df['readiness_score'].mean():.1f}")

# ===================== TAB NAVIGATION =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview",
    "👤 Student Analysis",
    "🏢 Company Analysis",
    "📋 Recommendations",
    "🔍 Search & Details"
])

# ===================== TAB 1: OVERVIEW =====================
with tab1:
    col1, col2 = st.columns(2)
    
    # Prediction distribution pie chart
    with col1:
        pred_counts = filtered_df["prediction"].value_counts()
        fig_pred = px.pie(
            values=pred_counts.values,
            names=pred_counts.index,
            title="Prediction Distribution",
            color_discrete_map={"High": "#2ecc71", "Medium": "#f39c12", "Low": "#e74c3c"}
        )
        st.plotly_chart(fig_pred, use_container_width=True)
    
    # Eligibility vs Prediction
    with col2:
        eligibility_pred = pd.crosstab(filtered_df["eligible"], filtered_df["prediction"])
        fig_elig = go.Figure()
        for col in eligibility_pred.columns:
            fig_elig.add_trace(go.Bar(
                x=eligibility_pred.index,
                y=eligibility_pred[col],
                name=col
            ))
        fig_elig.update_layout(
            title="Eligibility vs Prediction",
            xaxis_title="Eligible (0=No, 1=Yes)",
            yaxis_title="Count",
            barmode="group"
        )
        st.plotly_chart(fig_elig, use_container_width=True)
    
    # Readiness score histogram
    col1, col2 = st.columns(2)
    with col1:
        fig_hist = px.histogram(
            filtered_df,
            x="readiness_score",
            nbins=30,
            title="Readiness Score Distribution",
            labels={"readiness_score": "Readiness Score", "count": "Frequency"}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Top 10 companies by high predictions
    with col2:
        top_companies = get_top_companies_by_prediction(filtered_df)
        fig_top_comp = px.bar(
            x=top_companies.values,
            y=top_companies.index,
            orientation='h',
            title="Top 10 Companies (High Predictions)",
            labels={"x": "Count", "y": "Company ID"}
        )
        st.plotly_chart(fig_top_comp, use_container_width=True)

# ===================== TAB 2: STUDENT ANALYSIS =====================
with tab2:
    col1, col2 = st.columns([1, 1])
    
    # Student distribution across predictions
    with col1:
        students_per_pred = filtered_df.groupby("student_id")["prediction"].apply(
            lambda x: (x == "High").sum()
        )
        fig_student_dist = px.histogram(
            students_per_pred.values,
            nbins=20,
            title="Students by Number of High Predictions",
            labels={"value": "High Predictions Count", "count": "Number of Students"}
        )
        st.plotly_chart(fig_student_dist, use_container_width=True)
    
    # Average readiness by prediction
    with col2:
        avg_readiness_by_pred = filtered_df.groupby("prediction")["readiness_score"].mean().sort_values(ascending=False)
        fig_avg_readiness = px.bar(
            x=avg_readiness_by_pred.index,
            y=avg_readiness_by_pred.values,
            title="Average Readiness Score by Prediction",
            color=avg_readiness_by_pred.index,
            color_discrete_map={"High": "#2ecc71", "Medium": "#f39c12", "Low": "#e74c3c"}
        )
        st.plotly_chart(fig_avg_readiness, use_container_width=True)
    
    # Top students by average readiness
    st.subheader("Top 15 Students by Average Readiness Score")
    top_students = filtered_df.groupby("student_id").agg({
        "readiness_score": "mean",
        "eligible": "first",
        "prediction": lambda x: (x == "High").sum()
    }).rename(columns={"prediction": "high_predictions"}).sort_values("readiness_score", ascending=False).head(15)
    
    st.dataframe(top_students, use_container_width=True)

# ===================== TAB 3: COMPANY ANALYSIS =====================
with tab3:
    col1, col2 = st.columns(2)
    
    # Students per company
    with col1:
        students_per_company = filtered_df.groupby("company_name").size().sort_values(ascending=False).head(15)
        fig_students_comp = px.bar(
            x=students_per_company.values,
            y=students_per_company.index,
            orientation='h',
            title="Top 15 Companies by Student Interest",
            labels={"x": "Number of Students", "y": "Company ID"}
        )
        st.plotly_chart(fig_students_comp, use_container_width=True)
    
    # Average readiness per company
    with col2:
        avg_readiness_comp = filtered_df.groupby("company_name")["readiness_score"].mean().sort_values(ascending=False).head(15)
        fig_readiness_comp = px.bar(
            x=avg_readiness_comp.values,
            y=avg_readiness_comp.index,
            orientation='h',
            title="Top 15 Companies by Avg Student Readiness",
            labels={"x": "Avg Readiness Score", "y": "Company ID"}
        )
        st.plotly_chart(fig_readiness_comp, use_container_width=True)
    
    # Company shortlist summary
    st.subheader("Company Shortlist Summary")
    company_summary = company_shortlists.groupby("company_name").agg({
        "student_id": "count",
        "readiness_score": "mean",
        "eligible": "sum"
    }).rename(columns={
        "student_id": "total_candidates",
        "readiness_score": "avg_readiness",
        "eligible": "eligible_count"
    }).sort_values("avg_readiness", ascending=False).head(20)
    
    st.dataframe(company_summary, use_container_width=True)

# ===================== TAB 4: RECOMMENDATIONS =====================
with tab4:
    st.subheader("Student Company Recommendations")
    
    # Select a student
    student_list = sorted(student_recs["student_id"].unique())
    selected_student = st.selectbox("Select Student ID", student_list)
    
    if selected_student:
        student_data = student_recs[student_recs["student_id"] == selected_student].sort_values(
            "readiness_score", ascending=False
        )
        
        if len(student_data) > 0:
            st.write(f"### Top {len(student_data)} Company Recommendations for Student {selected_student}")
            
            for idx, row in student_data.iterrows():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Company", row["company_name"])
                with col2:
                    st.metric("Readiness Score", f"{row['readiness_score']:.1f}")
                with col3:
                    st.metric("Eligible", "✓ Yes" if row["eligible"] == 1 else "✗ No")
                with col4:
                    pred_color = get_prediction_color(row["prediction"])
                    st.markdown(f"<div style='background-color: {pred_color}; padding: 10px; border-radius: 5px; text-align: center; color: white; font-weight: bold;'>{row['prediction']}</div>", unsafe_allow_html=True)
        else:
            st.info("No recommendations available for this student.")
    
    # Comparison across students
    st.subheader("Top Students Comparison")
    num_students = st.slider("Number of students to compare", 5, 20, 10)
    
    top_students_recs = student_recs.groupby("student_id").agg({
        "readiness_score": "mean",
        "eligible": "first"
    }).sort_values("readiness_score", ascending=False).head(num_students).index.tolist()
    
    comparison_data = student_recs[student_recs["student_id"].isin(top_students_recs)].groupby("student_id").agg({
        "readiness_score": "mean",
        "eligible": "first",
        "company_name": "count"
    }).rename(columns={"company_name": "num_recommendations"}).sort_values("readiness_score", ascending=False)
    
    st.dataframe(comparison_data, use_container_width=True)

# ===================== TAB 5: SEARCH & DETAILS =====================
with tab5:
    st.subheader("🔍 Search & Filter Data")
    
    # Search mode
    search_mode = st.radio("Search by:", ["Student ID/Name", "Company Name", "Prediction Level"])
    
    if search_mode == "Student ID/Name":
        student_id = st.text_input("Enter Student ID or Name:")
        if student_id:
            # Use predictions_df which has readiness_score column
            if student_id.isdigit():
                student_matches = predictions_df[predictions_df["student_id"] == int(student_id)]
            else:
                # Search by name in students_merged_predictions, then filter predictions_df
                matching_students = students_merged_predictions[
                    students_merged_predictions["full_name"].str.contains(student_id, case=False, na=False)
                ]["student_id"].unique()
                student_matches = predictions_df[predictions_df["student_id"].isin(matching_students)]
            
            if len(student_matches) > 0:
                st.write(f"Found {len(student_matches)} records for Student {student_id}")
                st.dataframe(student_matches.sort_values("readiness_score", ascending=False), use_container_width=True)
            else:
                st.warning("No records found for this student ID/name.")
    
    elif search_mode == "Company Name":
        company_name = st.text_input("Enter Company Name:")
        if company_name:
            company_matches = predictions_df[predictions_df["company_name"] == company_name]
            if len(company_matches) > 0:
                st.write(f"Found {len(company_matches)} students interested in Company {company_name}")
                st.dataframe(company_matches.sort_values("readiness_score", ascending=False), use_container_width=True)
            else:
                st.warning("No records found for this company name.")
    
    elif search_mode == "Prediction Level":
        pred_level = st.selectbox("Select Prediction Level", ["High", "Medium", "Low"])
        pred_data = predictions_df[predictions_df["prediction"] == pred_level].sort_values(
            "readiness_score", ascending=False
        )
        st.write(f"Found {len(pred_data)} records with '{pred_level}' prediction")
        st.dataframe(pred_data, use_container_width=True)
    
    # Export functionality
    st.subheader("📥 Export Data")
    if st.button("Export Filtered Data to CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="filtered_predictions.csv",
            mime="text/csv"
        )

# ===================== FOOTER =====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>
    <p>Placement Prediction Dashboard | Data Pipeline v1.0</p>
    <p>Last Updated: {}</p>
</div>
""".format(pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)