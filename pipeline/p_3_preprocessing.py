"""
This stage prepares consistent structures for downstream use. It should:
--> Convert CGPA to numeric
--> Convert backlog counts to integer
--> Split multi-skill strings into lists
--> Create derived flags such as has_python, has_sql, eligible_no_backlogs
"""

"""TODO:
-> merge first_name and last_name to full_name
-> cgpa, latst_cgpa, attendance_percentage has been converted to numeric types
-> active_backlogs has been converted to integer
-> has_backlog_history has been converted to boolean
-> strings have been converted to lowercase
-> derive project count from project_title 
"""

import pandas as pd
from config import *
from utils.logger import LOGGER_FUNCTION

from config import DEPARTMENTS_MAPPING

# IMPORTANT_SKILLS = [
#     "python", "sql", "excel", "power bi", "pandas", "numpy",
#     "git", "html", "css", "javascript", "communication", "aptitude"
# ]

def preprocess_student_details(df):
    LOGGER_FUNCTION('info', "Preprocessing Student Details Data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Preprocessed Student details data: empty dataframe")
        return df

    df = df.copy()
    
    # Ensure student_id is integer
    df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce").astype('Int64')

    df["first_name"] = df["first_name"].str.title()
    df["last_name"] = df["last_name"].str.title()

    df["full_name"] = df[['first_name', 'last_name']].agg(' '.join, axis = 1)

    df = df.drop(columns = ["first_name", "last_name"])

    df['department'] = (df['department']
            .str.lower()
            .map(DEPARTMENTS_MAPPING)
            .fillna(df['department'].str.upper())
        )

    #semester already normalized
    LOGGER_FUNCTION('info', "Preprocessed Student Details Data.")

    return df[["student_id", "full_name", "department", "batch", "current_semester"]]

def preprocess_exam_data(df):
    LOGGER_FUNCTION('info', "Preprocessing Exam Data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Preprocessed Exam data: empty dataframe")
        return df

    #nothing to process, everything done in cleaning
    #no new columns to derive
    df = df.copy()
    
    # Ensure student_id is integer
    df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce").astype('Int64')

    df.columns = (
        df.columns
        .str.lower()
    )
    LOGGER_FUNCTION('info', "Preprocessed Exam Data.")

    return df

def preprocess_attendance_data(df):
    #no new columns to derive
    LOGGER_FUNCTION('info', "Preprocessing Attendance Data (No Preprocessing Needed)...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Preprocessed Attendance data: empty dataframe")
        return df
    
    df = df.copy()
    
    # Ensure student_id is integer
    df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce").astype('Int64')

    LOGGER_FUNCTION('info', "Preprocessed Attendance Data.")

    return df.copy()

def preprocess_skills_data(df):
    LOGGER_FUNCTION('info', "Preprocessing Skills Data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Preprocessed Skills data: empty dataframe")
        return df

    df = df.copy()
    
    # Ensure student_id is integer
    df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce").astype('Int64')

    # --- project count ---
    if "project_titles" in df.columns:
        df["project_count"] = df["project_titles"].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )

    """
    # --- normalize skill list ---
    if "skills" in df.columns:
        df["skills"] = df["skills"].fillna("")
        df["skill_list"] = df["skills"].apply(
            lambda x: sorted(set(
                skill.strip().lower()
                for skill in str(x).split(",")
                if skill.strip()
            ))
        )
        df["skill_count"] = df["skill_list"].apply(len)

    # --- encode fixed important skills ---
    for skill in IMPORTANT_SKILLS:
        col = f"skill_{skill.replace(' ', '_')}"
        df[col] = df["skill_list"].apply(
            lambda skills: int(skill in skills) if isinstance(skills, list) else 0
        )

    df["important_skill_count"] = df[
        [f"skill_{s.replace(' ', '_')}" for s in IMPORTANT_SKILLS]
    ].sum(axis=1)

    #FIX THE ERROR here
    # df["project_count"] = df["projects_titles"].apply(len)
    LOGGER_FUNCTION('info', "Preprocessed Skills Data.")
    """


    return df

def preprocess_company_data(df):
    LOGGER_FUNCTION('info', "Preprocessing Company Rules Data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Preprocessed Company rules data: empty dataframe")
        return df

    df = df.copy()

    LOGGER_FUNCTION('info', "Preprocessed Company Rules Data.")

    return df

def preprocess_all_sources(ingested_data):
    # LOGGER_FUNCTION('info', f"\n--------------------------------------------------------------------------")
    LOGGER_FUNCTION('info', f"--------------- Preprocessing ALL Sources... ---------------\n")
   
    ingested_data["student_details_data"] = preprocess_student_details(ingested_data["student_details_data"])
    ingested_data["exam_data"] = preprocess_exam_data(ingested_data["exam_data"])
    ingested_data["attendance_data"] = preprocess_attendance_data(ingested_data["attendance_data"])
    ingested_data["skills_data"] = preprocess_skills_data(ingested_data["skills_data"])
    ingested_data["company_rules_data"] = preprocess_company_data(ingested_data["company_rules_data"])
    LOGGER_FUNCTION('info', f"--------------- Preprocessed ALL Sources ---------------\n")
    return ingested_data
