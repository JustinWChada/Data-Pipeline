"""
This file is used for
- readiness scoring for each student
- probability of improvement
- skill-gap suggestions 

just simple analytics not extended precitions
"""

#ACTUALLY: IT IS NOW FOR:
"""
the prediction stage can rank opportunities, estimate placement likelihood, and recommend actions 
from these features. In other words, this stage should answer: Which companies should this student 
target first, and which students are strongest for each company?
"""

#IT SHOULD:
"""
Student recommendations: top 3 companies per student based on eligibility and readiness score
Company shortlists: top students per company ranked by readiness score
Placement risk buckets: classify each student-company row as High / Medium / Low likelihood using 
score thresholds derived from readiness_score and eligible
"""


#SOME METRICS:
"""
If eligible == 0, prediction = "Low"
If eligible == 1 and readiness_score >= 75, prediction = "High"
If eligible == 1 and readiness_score >= 60, prediction = "Medium"
Else prediction = "Low"
"""

from config import *
import pandas as pd
from utils.logger import LOGGER_FUNCTION

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(DB_CONN_STRING)
SessionLocal = sessionmaker(bind = engine)
Base = declarative_base()


SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True) 

#--------HELPER FUNCTIONS------
def assign_prediction_label(row):
    if row["eligible"] == 0:
        return "Low"
    elif row["readiness_score"] >= 75:
        return "High"
    elif row["readiness_score"] >= 60:
        return "Medium"
    return "Low"

def bucket_readiness_score(score): 
    #Convert numeric readiness score into interpretable score bands.
    # High: readiness_score >= 75
    # Medium: readiness_score >= 60
    # Low: readiness_score < 60

    if score >= 75:
        return "High"
    elif score >= 60:
        return "Medium"

    return "Low"
    pass

def filter_eligible_matches(predictions_df): 
    #Keep only rows where the student is worth considering for 
    # recommendation output.
    predictions_df = predictions_df.copy()
    predictions_df = predictions_df[(predictions_df["eligible"] == 1) & (predictions_df["readiness_score"] >= 60)]
    return predictions_df

def rank_company_matches(predictions_df): 
    #Apply final sorting logic across student-company matches before 
    # extracting top recommendations.
    predictions_df = predictions_df.copy()
    predictions_df = predictions_df.sort_values(by = ["readiness_score", "eligible"], ascending=[False, False])
    predictions_df = predictions_df.reset_index(drop=True)
    return predictions_df 

def log_prediction_summary(predictions_df): 
    #Log counts like total High, Medium, and Low predictions for 
    # debugging and review.
    summary = predictions_df["prediction"].value_counts()

    LOGGER_FUNCTION("info",f"Prediction Summary:\n{summary}")

#-------MAIN FUNCTIONS---------

def generate_prediction_scores(student_company_match_df): 
    #Create the main predictions dataframe by adding prediction labels or final recommendation 
    # scores to each student-company row.
    student_company_match_df["prediction"] = student_company_match_df.apply(assign_prediction_label, axis=1)
    return student_company_match_df

def get_top_company_recommendations(predictions_df, top_n=5): 
    #Return the best company recommendations for each student using readiness score and 
    # eligibility as ranking signals.
    df = predictions_df.copy()
    df = filter_eligible_matches(df)
    return df.groupby("student_id").head(top_n).reset_index(drop=True)

def get_top_student_shortlists(predictions_df, top_n=10): 
    #Return the best student shortlist for each company based on prediction strength and 
    # readiness score.
    df = predictions_df.copy()
    df = filter_eligible_matches(df)
    return df.groupby("company_name").head(top_n).reset_index(drop=True)
    
def build_student_prediction_summary(predictions_df, students_df): 
    #Create a student-level summary that merges prediction outcomes with student profile details 
    # from the students table.
    df = students_df.merge(predictions_df, on = "student_id", how="left")
    return df

def save_predictions_to_csv(predictions_df, student_recommendations_df, company_shortlists_df): 
    #Save the outputs of the prediction stage as CSV snapshots, similar to your storage stage 
    # pattern.
    predictions_df.to_csv(SNAPSHOT_DIR / "predictions_df.csv", index=False)
    student_recommendations_df.to_csv(SNAPSHOT_DIR / "student_recommendations.csv", index=False)
    company_shortlists_df.to_csv(SNAPSHOT_DIR / "company_shortlists.csv", index=False)
    LOGGER_FUNCTION("info", "Saved prediction outputs to CSV files in the outputs directory.")

def load_predictions_to_postgresql(predictions_df, student_recommendations_df, company_shortlists_df): 
    #Persist the prediction outputs into PostgreSQL as final downstream tables, matching your 
    # storage-stage design approach.
    LOGGER_FUNCTION("info", "Loading prediction outputs into PostgreSQL...")
    session = SessionLocal()
    predictions_df.to_sql("predictions_table",  con = engine, if_exists = "replace", index = False, method = "multi",)
    student_recommendations_df.to_sql("student_recommendations_table", con = engine, if_exists = "replace", index = False, method = "multi",)
    company_shortlists_df.to_sql("company_shortlists_table", con = engine, if_exists = "replace", index = False, method = "multi",)
    LOGGER_FUNCTION("info", "Loaded prediction outputs into PostgreSQL tables.")
    session.commit()
    session.close()


def run_predictions_stage(predictions_df, students_df): 
    #Main orchestration function that calls load, validate, prepare, predict, rank, save, 
    # and store in sequence.
    LOGGER_FUNCTION("info","\n------------------------------------ STARTING PREDICTION STAGE --------------------------------------")
    predictions_df = generate_prediction_scores(predictions_df)
    student_recommendations_df = get_top_company_recommendations(predictions_df)
    company_shortlists_df = get_top_student_shortlists(predictions_df)
    save_predictions_to_csv(predictions_df, student_recommendations_df, company_shortlists_df)
    load_predictions_to_postgresql(predictions_df, student_recommendations_df, company_shortlists_df)
    students_merged_df = build_student_prediction_summary(predictions_df, students_df)
    #also save it
    students_merged_df.to_csv(SNAPSHOT_DIR / "students_merged_predictions.csv", index = False)
    log_prediction_summary(predictions_df)

    LOGGER_FUNCTION("info","\n------------------------------------ ENDING PREDICTION STAGE --------------------------------------")
    return predictions_df, student_recommendations_df, company_shortlists_df, students_merged_df

