#the one file that ties everything together
"""
this file ties the entire flow together. the clean flow:
--> ingests all source files
--> clean the raw
--> preprocess and derive standard fields
--> displays eligibility views
--> stores outputs in mysql and csv snapshots
--> visialze on the dashboard
"""

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

all_data = ingest_all_sources()

with open("ingested_data.txt", "w") as f:
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

with open("cleaned_data.txt", "w") as f:
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

with open("preprocessed_data.txt", "w") as f:
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

with open("eligibility_data.txt", "w") as f:
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

with open("predictions_data.txt", "w") as f:
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
    

#correct the raise error thing: itse better the pipeline break.

# get_all_files()

# one, two, three = HASHING_FUNCTION('exam_cell.csv')
 
# two = PurePath(two)
# print(one, two, three)