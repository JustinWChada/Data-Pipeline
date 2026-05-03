"""
It should generate the Unified Eligibility View from the cleaned and processed data.

----criteria----
A student is eligible if CGPA meets threshold
A student must have no active backlogs
A student may qualify for more than one category
Electronics students with Python/SQL/DSA can be tagged for software roles too:

output columns:
- student id, name, department, cgpa, active_backlogs
- skills, core_skills_eligibility,
- software_eligibility, overall_eligibility, 
- matched_companies
"""

import pandas as pd
from utils.logger import LOGGER_FUNCTION
from config import *

# dept_dummies = pd.get_dummies(df["department"], prefix="dept", dtype=int)
# df = df.join(dept_dummies)

"""
A better match is on:
- department match: 20%,
- core skill match: 25%,
- project count (score): 15%,
- attendance percentage:10%,
- academic score: 30%.
"""

def parse_skills_string(skills_str):
    """
    Parse skills from string format (comma-separated or similar).
    Handle both string and list formats.
    """
    if isinstance(skills_str, list):
        return [skill.strip() for skill in skills_str if skill]
    elif isinstance(skills_str, str):
        return [skill.strip() for skill in skills_str.split(',') if skill.strip()]
    return []


def count_skill_matches(student_skills, required_skills):
    """
    Count how many required skills the student has.
    Returns (count, total_required, percentage).
    """
    student_skills_list = parse_skills_string(student_skills)
    
    required_skills_list = parse_skills_string(required_skills)
    

    if not required_skills_list:
        return 0, 0, 0.0
    
    count = sum(1 for skill in required_skills_list if skill.lower() in [s.lower() for s in student_skills_list])
    total = len(required_skills_list)
    percentage = (count / total * 100) if total > 0 else 0.0

    
    return count, total, round(percentage, 2)


def compute_skills_eligibility(df, company_df):
    """
    For each student, compute skill matches against all companies' requirements.
    Adds columns for each company showing:
    - technical_skills_count_{company}
    - technical_skills_percentage_{company}
    - soft_skills_count_{company}
    - soft_skills_percentage_{company}
    - eligible_{company} (boolean)
    """
    df = df.copy()
    
    LOGGER_FUNCTION('info', f"\nComputing skills eligibility for each company...")
    # Iterate through each company in company_df
    for idx, company_row in company_df.iterrows():
        company_name = company_row['company_name']
        required_tech_skills = company_row.get('required_technical_skills', '')
        required_soft_skills = company_row.get('required_soft_skills', '')
        
        # Count technical skills matches for this company
        tech_counts = df['technical_skills'].apply(
            lambda x: count_skill_matches(x, required_tech_skills)
        )
        df[f'tech_skills_count_{company_name}'] = tech_counts.apply(lambda x: x[0])
        df[f'tech_skills_percentage_{company_name}'] = tech_counts.apply(lambda x: x[2])
        
        # Count soft skills matches for this company
        soft_counts = df['soft_skills'].apply(
            lambda x: count_skill_matches(x, required_soft_skills)
        )
        df[f'soft_skills_count_{company_name}'] = soft_counts.apply(lambda x: x[0])
        df[f'soft_skills_percentage_{company_name}'] = soft_counts.apply(lambda x: x[2])
        
        # Student is eligible if they have at least one technical AND one soft skill match
        df[f'eligible_{company_name}'] = (
            (df[f'tech_skills_count_{company_name}'] > 0) & 
            (df[f'soft_skills_count_{company_name}'] > 0)
        ).astype(int)
    
    LOGGER_FUNCTION('info', f"Completed computing skills eligibility for all companies.")
    return df

def compute_placement_readiness_score(df, company_df):
    """
    Calculate placement readiness score for each student against each company.
    Score is based on:
    - Academic (CGPA): 40%
    - Attendance: 20%
    - Skills match: 25%
    - Projects: 15%
    
    Creates columns: readiness_score_{company_name}
    """
    df = df.copy()

    LOGGER_FUNCTION('info', f"\nComputing placement readiness score for each company...")
    
    # Normalize academic score
    academic = df["cgpa"].clip(0, 10) / 10
    
    # Normalize attendance
    attendance = df["attendance_percentage"].clip(0, 100) / 100
    
    # Normalize projects
    projects = df["project_count"].clip(0, 5) / 5
    
    # For each company, calculate readiness score using that company's skill match percentage
    for idx, company_row in company_df.iterrows():
        company_name = company_row['company_name']
        
        # Get the average of technical and soft skills percentages for this company
        tech_skills_pct = df[f'tech_skills_percentage_{company_name}'] / 100
        soft_skills_pct = df[f'soft_skills_percentage_{company_name}'] / 100
        skills = (tech_skills_pct + soft_skills_pct) / 2
        
        # Calculate weighted readiness score (0-100)
        df[f'readiness_score_{company_name}'] = (
            0.40 * academic +
            0.20 * attendance +
            0.25 * skills +
            0.15 * projects
        ).mul(100).round(2)
    
    LOGGER_FUNCTION('info', f"Completed computing placement readiness score for all companies.")

    return df

#why this code here because i have been facing issues with student id being string in some dataframes and int in others, this ensures it's consistent for merging
def convert_numeric_columns(df, columns):
    for col in columns:
        if col not in df.columns:
            continue

        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def build_eligibility_view(ingested_data):
    """
    Build two normalized dataframes:
    1. students_df: Core student information (non-redundant)
    2. student_company_match_df: Student-company matching details
    
    Now handles mixed empty/non-empty dataframes gracefully.
    """

    LOGGER_FUNCTION('info', f"\n------------------------------------ ELIGIBILITY VIEW --------------------------------------")
    student_details_df = ingested_data["student_details_data"]
    exams_df = ingested_data["exam_data"]
    attendance_df = ingested_data["attendance_data"]
    skills_df = ingested_data["skills_data"]
    company_rules_df = ingested_data["company_rules_data"]

    # Map dataframes with their names for logging
    df_mapping = {
        "student_details": student_details_df,
        "exam": exams_df,
        "attendance": attendance_df,
        "skills": skills_df,
        "company_rules": company_rules_df
    }
    
    # Check which dataframes are empty and log them
    empty_dfs = [name for name, df in df_mapping.items() if df.empty]
    non_empty_dfs = [name for name, df in df_mapping.items() if not df.empty]
    
    if empty_dfs:
        LOGGER_FUNCTION('warning', f"Found empty dataframes: {empty_dfs}")
    
    LOGGER_FUNCTION('info', f"Non-empty dataframes available: {non_empty_dfs}")
    
    # Validation: At least student details and one other dataset must exist for meaningful processing
    if student_details_df.empty:
        raise ValueError("Cannot proceed: Student details dataframe is empty. This is the core dataset.")
    
    if not non_empty_dfs or (empty_dfs and len(non_empty_dfs) <= 1):
        LOGGER_FUNCTION('warning', f"Limited data available. Only {non_empty_dfs} are available. Consider checking if files were properly ingested.")

    #make sure student_id is numeric in all non-empty dataframes for merging
    if not student_details_df.empty:
        student_details_df = convert_numeric_columns(student_details_df, ["student_id"])
    if not exams_df.empty:
        exams_df = convert_numeric_columns(exams_df, ["student_id"])
    if not attendance_df.empty:
        attendance_df = convert_numeric_columns(attendance_df, ["student_id"])
    if not skills_df.empty:
        skills_df = convert_numeric_columns(skills_df, ["student_id"])
    if not company_rules_df.empty:
        company_rules_df = convert_numeric_columns(company_rules_df, ["student_id"])

    LOGGER_FUNCTION('info', f"\nMerging the datasets based on the student_id (skipping empty dataframes)...")
    
    # Start with student details as the base (required)
    df = student_details_df.copy()
    
    # Merge exam data if available
    if not exams_df.empty:
        LOGGER_FUNCTION('info', f"Merging student details with exam data...")
        df = df.merge(exams_df, on="student_id", how="left")
    else:
        LOGGER_FUNCTION('info', f"Skipping exam data merge (empty dataframe)")
    
    # Merge attendance data if available
    if not attendance_df.empty:
        LOGGER_FUNCTION('info', f"Merging with attendance data...")
        df = df.merge(attendance_df, on="student_id", how="left")
    else:
        LOGGER_FUNCTION('info', f"Skipping attendance data merge (empty dataframe)")
    
    # Merge skills data if available
    if not skills_df.empty:
        LOGGER_FUNCTION('info', f"Merging with skills data...")
        df = df.merge(skills_df, on="student_id", how="left")
    else:
        LOGGER_FUNCTION('info', f"Skipping skills data merge (empty dataframe)")
    
    # Remove duplicate department columns if they exist (keep only department)
    if "department_x" in df.columns and "department_y" in df.columns:
        df = df.drop(columns=["department_y"])
        df = df.rename(columns={"department_x": "department"})
    elif "first_name" in df.columns and "last_name" in df.columns:
        # Remove first_name and last_name if they appear (we already have full_name)
        df = df.drop(columns=["first_name", "last_name"], errors="ignore")

    # Compute skills eligibility for each company (if company rules available)
    if not company_rules_df.empty:
        df = compute_skills_eligibility(df, company_rules_df)
        
        # Compute placement readiness score for each company
        df = compute_placement_readiness_score(df, company_rules_df)
    else:
        LOGGER_FUNCTION('warning', f"Skipping skills eligibility computation (company rules dataframe is empty)")

    # ---- Create normalized dataframes ----
    
    # 1. STUDENTS TABLE: Core student info - only include columns that exist in the merged dataframe
    LOGGER_FUNCTION('info', f"\nCreating students table view...")
    
    # Define all potential student columns, but only include those that exist
    potential_student_cols = [
        'student_id', 'full_name', 'department', 'batch', 'current_semester',
        'cgpa', 'latest_sgpa', 'active_backlogs', 'has_backlog_history',
        'attendance_percentage', 'technical_skills', 'soft_skills',
        'project_titles', 'project_count'
    ]
    
    # Only select columns that exist in df
    available_cols = [col for col in potential_student_cols if col in df.columns]
    students_df = df[available_cols].copy()
    
    # Log which columns were missing
    missing_cols = [col for col in potential_student_cols if col not in df.columns]
    if missing_cols:
        LOGGER_FUNCTION('info', f"Note: Following columns not available in merged data (source dataframes were empty): {missing_cols}")
    
    # 2. STUDENT_COMPANY_MATCH TABLE: Company matching details
    LOGGER_FUNCTION('info', f"\nCreating student-company match table view...")
    
    if not company_rules_df.empty:
        company_match_records = []
        
        for idx, company_row in company_rules_df.iterrows():
            company_name = company_row['company_name']
            
            # Create a record for each student-company combination
            match_df = pd.DataFrame({
                'student_id': df['student_id'],
                'company_name': company_name,
                'tech_skills_count': df[f'tech_skills_count_{company_name}'],
                'tech_skills_percentage': df[f'tech_skills_percentage_{company_name}'],
                'soft_skills_count': df[f'soft_skills_count_{company_name}'],
                'soft_skills_percentage': df[f'soft_skills_percentage_{company_name}'],
                'eligible': df[f'eligible_{company_name}'],
                'readiness_score': df[f'readiness_score_{company_name}']
            })
            
            company_match_records.append(match_df)
        
        LOGGER_FUNCTION('info', f"Created student-company match records view for all companies.")
        # Concatenate all company matches into one table
        student_company_match_df = pd.concat(company_match_records, ignore_index=True)
    else:
        LOGGER_FUNCTION('warning', f"Company rules dataframe is empty. Creating empty student-company match table.")
        # Create an empty dataframe with the expected schema
        student_company_match_df = pd.DataFrame(columns=[
            'student_id', 'company_name', 'tech_skills_count', 'tech_skills_percentage',
            'soft_skills_count', 'soft_skills_percentage', 'eligible', 'readiness_score'
        ])
    
    LOGGER_FUNCTION('info', f"\nFinal students table shape: {students_df.shape}")
    LOGGER_FUNCTION('info', f"\nFinal student-company match table shape: {student_company_match_df.shape}")
    LOGGER_FUNCTION('info', f"\n------------------------------------ ELIGIBILITY VIEW BUILT --------------------------------------")
    
    return {
        'students': students_df,
        'student_company_match': student_company_match_df
    }