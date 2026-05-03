"""
This stage stores the cleaned outputs and final views as well as in SQL db.

It should:
-> Save processed CSVs ✅
-> Save final eligibility table
-> Load data into PostgreSQL
-> Maintain timestamped snapshots
"""

import pandas as pd
import pathlib
from config import *
from utils.logger import LOGGER_FUNCTION
from sqlalchemy import create_engine, Column, Integer, DateTime, String, Float, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker 
from utils.config_log import CONFIG_LOGGER

# ========== STUDENTS TABLE ==========
# Columns: ['student_id', 'full_name', 'department', 'batch', 'current_semester', 'cgpa', 'latest_sgpa', 'active_backlogs', 'has_backlog_history', 'attendance_percentage', 'technical_skills', 'soft_skills', 'project_titles', 'project_count']
# Shape: (20, 14)
engine = create_engine(DB_CONN_STRING)
SessionLocal = sessionmaker(bind = engine)
Base = declarative_base()
# Base.metadata.create_all(bind = engine)

class StudentsTable(Base):
    __tablename__ = "students_table"
    student_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    department = Column(String)
    batch = Column(String)
    current_semester = Column(String)
    cgpa = Column(Float)
    latest_sgpa = Column(Float)
    active_backlogs = Column(Integer)
    has_backlog_history = Column(Boolean)
    attendance_percentage = Column(Float)
    technical_skills = Column(ARRAY(String))
    soft_skills = Column(ARRAY(String))
    project_titles = Column(ARRAY(String))


# ========== STUDENT_COMPANY_MATCH TABLE ==========
# Columns: ['student_id', 'company_name', 'tech_skills_count', 'tech_skills_percentage', 'soft_skills_count', 'soft_skills_percentage', 'eligible', 'readiness_score']
# Shape: (200, 8)

class StudentCompanyMatchTable(Base):
    __tablename__ = "student_company_match_table"
    id = Column(Integer, primary_key = True, index = True)
    student_id = Column(Integer)
    company_name = Column(String)
    tech_skills_count = Column(Integer)
    tech_skills_percentage = Column(Float)
    soft_skills_count = Column(Integer)
    soft_skills_percentage = Column(Float)
    eligible = Column(Integer)
    readiness_score = Column(Float)


#SAVING TO CSV FILES
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def save_to_csv(students_df, student_company_match_df):
    students_df.to_csv(SNAPSHOT_DIR / "students_tables.csv", index = False)
    student_company_match_df.to_csv(SNAPSHOT_DIR / "student_company_match_table.csv", index = False)

    LOGGER_FUNCTION("info","Saved processed dataframes snapshots to CSV files in the outputs directory.")

def load_to_postgresql(students_df, student_company_match_df):
    LOGGER_FUNCTION("info","Loading data into PostgreSQL database...")
    # Create tables if they don't exist
    
    session = SessionLocal()
    # Load students_df into StudentsTable

    # Load students_df into StudentsTable
    # index=False means that pandas will not write row indices into the SQL table.
    # method="multi" means that pandas will execute multiple INSERT statements to write the data into the SQL table, which can be faster than the default single INSERT statement per row.
    students_df.to_sql(StudentsTable.__tablename__, con = engine, if_exists = "replace", index = False, method = "multi",)
    LOGGER_FUNCTION("info","Loaded students_df into StudentsTable.")

    # Load student_company_match_df into StudentCompanyMatchTable
    student_company_match_df.to_sql(StudentCompanyMatchTable.__tablename__, con = engine, if_exists = "replace", index = False, method = "multi",)
    LOGGER_FUNCTION("info","Loaded student_company_match_df into StudentCompanyMatchTable.")

    LOGGER_FUNCTION("info","Data loading into PostgreSQL completed successfully.")

    session.commit()
    session.close()

def run_storage_stage(student_df, student_company_match_df):
    LOGGER_FUNCTION("info","\n------------------------------------ STARTING STORAGE STAGE --------------------------------------")

    save_to_csv(student_df, student_company_match_df)
    load_to_postgresql(student_df, student_company_match_df)
    LOGGER_FUNCTION("info","Storage stage completed successfully.\n------------------------------------ END OF STORAGE STAGE --------------------------------------\n")