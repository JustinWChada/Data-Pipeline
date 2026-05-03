"""
This stage should fix messy school data before merging it. It should:​
--> Standardize column names
--> Remove duplicates
--> Fix missing registration numbers
--> Normalize department names like ECE, 
--> Electronics, Electronics and Communication
--> Normalize skill names like python, Python, PYTHON
"""

"""
STEPS:
1. Copy the raw dataframe.
2. Standardize column names.
3. Normalize text values.
4. Fix data types.
5. Handle missing values.
6. Remove duplicates.
7. Apply source-specific validation checks.
8. Return cleaned dataframe plus cleaning metadata.
"""
import re
import pandas as pd
from utils.missing_values_log import MISSING_VALUES_LOGGER
from utils.logger import LOGGER_FUNCTION

STOP_WORDS = {"this", "is", "in"}

def normalize_text_columns(df, columns):
  
    for col in columns:
        if col in df.columns:
            # This line of code applies a lambda function to each element in the specified column of the dataframe. The lambda function takes a string as input, converts it to lowercase, removes any characters that are not alphanumeric or whitespace using a regular expression, and then strips any leading or trailing whitespace. The resulting string is then returned as the new value for that element in the dataframe. If the element is not a string, it is left unchanged.
            df[col] = df[col].apply(
                lambda s: re.sub(r"[^\w\s,]", "", s.lower()).strip()
                if isinstance(s, str) else s
            )
            # Remove this one: may accidentally change valid values
            # df[col] = df[col].apply(
            #     lambda s: " ".join(word for word in s.split() if word not in STOP_WORDS)
            #     if isinstance(s, str) else s
            # )
    
    return df

def convert_numeric_columns(df, columns):
    for col in columns:
        if col not in df.columns:
            continue

        if col == "current_semester":
            df[col] = df[col].astype(str).str.extract(r"(\d+)", expand=False)

        if col == "attendance_percentage":
            df[col] = df[col].astype(str).str.extract(r"(\d+(?:\.\d+)?)", expand=False)

        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def convert_boolean_columns(df, columns):
    true_values = {"true", "yes", "1", "y"}
    false_values = {"false", "no", "0", "n"}

    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: True if str(x).strip().lower() in true_values
                else False if str(x).strip().lower() in false_values
                else pd.NA
            )

    return df

def drop_duplicate_rows(df, subset):
    df = df.drop_duplicates(subset=subset)
    return df

def handle_missing_values(df, columns, value_type, filename):
    if "student_id" in df.columns:
        missing_student = df["student_id"].isna() | (df["student_id"].astype(str).str.strip() == "")
        if missing_student.any():
            MISSING_VALUES_LOGGER.warning(f"{filename}: missing student_id rows dropped")
            df = df.loc[~missing_student].copy()
    
    count_like_columns = ['active_backglogs','max_active_backlogs']
    count_like_columns_mode = ['current_semester']


    existing_cols = [col for col in columns if col in df.columns]
    if not existing_cols:
        MISSING_VALUES_LOGGER.warning(f"{filename}: missing values found in {columns}")
        return df


    if value_type == "numeric":
        for col in existing_cols:
            if col in count_like_columns:
                df[col] = df[col].fillna(0)
                continue
            
            if col in count_like_columns_mode:
                df[col] =  df[col].fillna(df[col].mode())
                continue

            df[col] = df[col].fillna(df[col].mean())

    elif value_type == "string":
        for col in existing_cols:
            df[col] = df[col].fillna("unknown")

    elif value_type == "boolean":
        for col in existing_cols:
            df[col] = df[col].fillna(False)

    return df

def validate_column_values(df, required_columns):
    if "cgpa" in required_columns and "cgpa" in df.columns:
        mean_value = df.loc[df["cgpa"].between(0, 10), "cgpa"].mean()
        df.loc[~df["cgpa"].between(0, 10), "cgpa"] = mean_value

    if "latest_sgpa" in required_columns and "latest_sgpa" in df.columns:
        mean_value = df.loc[df["latest_sgpa"].between(0, 10), "latest_sgpa"].mean()
        df.loc[~df["latest_sgpa"].between(0, 10), "latest_sgpa"] = mean_value

    if "active_backlogs" in required_columns and "active_backlogs" in df.columns:
        df.loc[~df["active_backlogs"].between(0, 20), "active_backlogs"] = 0

    if "attendance_percentage" in required_columns and "attendance_percentage" in df.columns:
        mean_value = df.loc[df["attendance_percentage"].between(0, 100), "attendance_percentage"].mean()
        df.loc[~df["attendance_percentage"].between(0, 100), "attendance_percentage"] = mean_value

    if "minimum_cgpa" in required_columns and "minimum_cgpa" in df.columns:
        mean_value = df.loc[df["minimum_cgpa"].between(0, 10), "minimum_cgpa"].mean()
        df.loc[~df["minimum_cgpa"].between(0, 10), "minimum_cgpa"] = mean_value

    if "current_semester" in required_columns and "current_semester" in df.columns:
        df.loc[~df["current_semester"].between(1,8), "current_semester"] = df["current_semester"].mode()

    list_like_columns = [
        "technical_skills",
        "soft_skills",
        "project_titles",
        "required_technical_skills",
        "required_soft_skills",
        "allowed_departments"
    ]

    for col in list_like_columns:
        if col in required_columns and col in df.columns:
            df[col] = df[col].fillna("")
            df[col] = df[col].apply(
                lambda x: [item.strip() for item in x.split(",") if item.strip()]
                if isinstance(x, str) else x
            )

    return df


#now using the generic functions in specific datasets
def clean_student_details_data(df):
    df = df.copy()
    LOGGER_FUNCTION('info', f"Cleaning student details data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Clean student details data: empty dataframe")
        return df
  
    df = normalize_text_columns(df, ["first_name", "last_name", "department", "batch"])
    df = convert_numeric_columns(df, ["current_semester"])
    df = drop_duplicate_rows(df, ["student_id"])
    df = handle_missing_values(df, ["first_name", "last_name", "department", "batch"], "string", "student_details.csv")
    df = handle_missing_values(df, ["current_semester"], "numeric", "student_details.csv")
    LOGGER_FUNCTION('info', f"Cleaned student details data...")
    return df

def clean_exam_data(df):
    df = df.copy()
    LOGGER_FUNCTION('info', f"Cleaning exam data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Clean exam data: empty dataframe")
        return df

    df = convert_numeric_columns(df, ["cgpa", "latest_sgpa", "active_backlogs"])
    df = convert_boolean_columns(df, ["has_backlog_history"])
    df = drop_duplicate_rows(df, ["student_id"])
    df = validate_column_values(df, ["cgpa", "latest_sgpa", "active_backlogs"])
    df = handle_missing_values(df, ["cgpa", "latest_sgpa", "active_backlogs"], "numeric", "exam.csv")
    df = handle_missing_values(df, ["has_backlog_history"], "boolean", "exam.csv")
    LOGGER_FUNCTION('info', f"Cleaned exam data...")
    return df

def clean_attendance_data(df):
    df = df.copy()
    LOGGER_FUNCTION('info', f"Cleaning attendance data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Clean attendance data: empty dataframe")
        return df
    
    df = convert_numeric_columns(df, ["attendance_percentage"])
    df = drop_duplicate_rows(df, ["student_id"])
    df = validate_column_values(df, ["attendance_percentage"])
    df = handle_missing_values(df, ["attendance_percentage"], "numeric", "attendance.csv")
    LOGGER_FUNCTION('info', f"Cleaned attendance data...")
    return df

def clean_skills_data(df):
    df = df.copy()
    LOGGER_FUNCTION('info', f"Cleaning skills data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Clean skills data: empty dataframe")
        return df

    df = normalize_text_columns(df, ["technical_skills", "soft_skills", "project_titles"])
    df = drop_duplicate_rows(df, ["student_id"])
    df = handle_missing_values(df, ["technical_skills", "soft_skills", "project_titles"], "string", "skills.csv")
    df = validate_column_values(df, ["technical_skills", "soft_skills", "project_titles"])
    LOGGER_FUNCTION('info', f"Cleaned skills data...")
    return df

def clean_company_rules_data(df):
    df = df.copy()
    LOGGER_FUNCTION('info', f"Cleaning company rules data...")

    if len(df) == 0:
        LOGGER_FUNCTION('warning', f"Clean company rules data: empty dataframe")
        return df

    df = convert_numeric_columns(df, ["minimum_cgpa", "max_active_backlogs"])
    df = convert_boolean_columns(df, ["allows_backlog_history"])
    df = normalize_text_columns(df, [
        "company_name",
        #why commented: Because it would remove the , delimiter
        # "allowed_departments",
        # "required_technical_skills",
        # "required_soft_skills"
    ])
    df = drop_duplicate_rows(df, ["company_name"])
    df = handle_missing_values(df, ["minimum_cgpa", "max_active_backlogs"], "numeric", "company_rules.csv")
    df = handle_missing_values(df, ["allowed_departments", "required_technical_skills", "required_soft_skills"], "string", "company_rules.csv")
    df = handle_missing_values(df, ["allows_backlog_history"], "boolean", "company_rules.csv")
    df = validate_column_values(df, [
        "minimum_cgpa",
        "max_active_backlogs",
        "allowed_departments",
        "required_technical_skills",
        "required_soft_skills"
    ])
    LOGGER_FUNCTION('info', f"Cleaned company rules data...")
    return df

def clean_all_sources(ingested_data):
    LOGGER_FUNCTION('info', f"\n--------------------------------------------------------------------------")
    LOGGER_FUNCTION('info', f"--------------- Cleaning all sources... ---------------\n")
    ingested_data["student_details_data"] = clean_student_details_data(ingested_data["student_details_data"])
    ingested_data["exam_data"] = clean_exam_data(ingested_data["exam_data"])
    ingested_data["attendance_data"] = clean_attendance_data(ingested_data["attendance_data"])
    ingested_data["skills_data"] = clean_skills_data(ingested_data["skills_data"])
    ingested_data["company_rules_data"] = clean_company_rules_data(ingested_data["company_rules_data"])
    LOGGER_FUNCTION('info', f"--------------- Cleaned all sources ---------------\n")
    return ingested_data