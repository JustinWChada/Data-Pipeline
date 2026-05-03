from datetime import datetime, timezone
from pathlib import Path, PurePath

import re
import pickle
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker,declarative_base 

from config import *
from utils.logger import LOGGER_FUNCTION
from utils.hashing import HASHING_FUNCTION

# Cache directory for storing dataframes of unchanged files
CACHE_DIR = Path("data/registry")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DB_ENGINE = create_engine(DB_CONN_STRING)
SessionLocal = sessionmaker(bind = DB_ENGINE)
base = declarative_base()

class Registry(base):
    __tablename__ = 'registry'
    id = Column(Integer, primary_key = True)
    filename = Column(String)
    filepath = Column(String)
    sha256_hash = Column(String)
    processed_at = Column(DateTime)
    status = Column(String)

#creating table is not exists
base.metadata.create_all(bind=DB_ENGINE)

def fetch_registry_record(filename):
    #fetch the record for the given filename from the registry
    session = SessionLocal()
    filename = str(filename)
    record = session.query(Registry).filter(Registry.filename == filename).first()

    session.close()

    return record

def store_registry_record(filename, file_path,sha256_hash, status):
    #a basic record will contain: file_name, file_path, sha256_hash, processed_at, status
    file_path = str(Path(file_path).resolve())
    session = SessionLocal()

    try:
        record = Registry(
            filename=filename,
            filepath=file_path,
            sha256_hash=sha256_hash,
            processed_at=datetime.now(timezone.utc),
            status=status
        )
        session.add(record)
        session.commit()
        LOGGER_FUNCTION("info", f"Stored registry record for {filename} with status '{status}'.")
    except Exception as e:
        session.rollback()
        LOGGER_FUNCTION("error", f"Failed to store registry record for {filename}: {e}")
    finally:
        session.close()

def update_registry_record(filename, file_path, sha256_hash, status):
    #updating the file path and sha256_hash in the registry
    file_path = str(Path(file_path).resolve())
    session = SessionLocal()

    record = session.query(Registry).filter(Registry.filename == filename).first()

    try:

        if record:
            record.filepath = file_path
            record.sha256_hash = sha256_hash
            record.processed_at = datetime.utcnow()
            record.status = status
            session.commit()
            LOGGER_FUNCTION("info", f"Updated registry record for {filename} with status '{status}'.")
        else:
            # Optional: handle case where record doesn't exist
            LOGGER_FUNCTION('warning', f"No existing record found for filename: {filename}. Consider creating a new record instead.")
    
    except Exception as e:
        session.rollback()
        LOGGER_FUNCTION('error', f"Error updating registry record for filename: {filename}. Error: {str(e)}")

    finally:
        session.close()
    
def check_registry_status(filename,sha256_hash):# file_path, 
    record = fetch_registry_record(filename)

    if record is None:
        return 'new'

    if record.sha256_hash == sha256_hash:
        return 'unchanged'
    
    return 'modified'

def save_dataframe_cache(filename, df):
    """Save a dataframe to cache for later retrieval if file remains unchanged."""
    cache_file = CACHE_DIR / f"{filename}.pkl"
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(df, f)
        LOGGER_FUNCTION('info', f"Cached dataframe for {filename}")
    except Exception as e:
        LOGGER_FUNCTION('warning', f"Failed to cache dataframe for {filename}: {e}")

def load_dataframe_cache(filename):
    """Load a cached dataframe if it exists."""
    cache_file = CACHE_DIR / f"{filename}.pkl"
    try:
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                df = pickle.load(f)
            LOGGER_FUNCTION('info', f"Loaded cached dataframe for {filename} ({len(df)} rows)")
            return df
    except Exception as e:
        LOGGER_FUNCTION('warning', f"Failed to load cached dataframe for {filename}: {e}")
    
    return None

# def get_all_files():
#     raw_files = [path for path in RAW_DIR.glob('**/*') if path.is_file()]
    
#     if not raw_files:
#         LOGGER_FUNCTION('warning', f"No files found in the raw directory: {RAW_DIR}. Please check the directory and try again.")
#         return
    
#     for path in raw_files:
#         filename = path.name
#         file_path = str(path.resolve())
        
#         LOGGER_FUNCTION('info', f"\n--------------------------------------------------------------------------")
#         LOGGER_FUNCTION('info', f"Discovered file: {filename}")

#         #res = HASHING_FUNCTION(path)
    
#         # if res is None:
#         #     LOGGER_FUNCTION('warning', f"Skipping file {filename} because hashing failed.")
#         #     continue
        
#         # filename, file_path, digest = res

#         # check_registry_status(filename, file_path, digest)
#         # load_source_file(file_path, "none", "none")

def read_csv_file(file_path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path, sep=',', header=0, na_filter=True, na_values=['-', 'Ab(Ext)'], keep_default_na=True)
        return df
    except Exception as e:
        LOGGER_FUNCTION('error', f"Error reading CSV file {file_path}. Error: {str(e)}")
        return None

    #future changes
    # try:
    #     return pd.read_csv(file_path)
    # except FileNotFoundError:
    #     raise
    # except pd.errors.EmptyDataError:
    #     raise
    # except pd.errors.ParserError:
    #     raise

def normalize_columns(df):
    #the issue here is that is is removing commas but i want to keep the commas for list like columns
    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(r'[^\w\s\,]', '', regex = True) #replaces punctuation with _
        .str.replace(r'\s+', '_', regex = True) # replaces space with _
        .str.replace(r'_$', '', regex= True) 
    )
 
    return df

def validate_required_columns(df, required_columns, source_name):
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        LOGGER_FUNCTION('warning', f"File {source_name} is missing required columns: {', '.join(missing)}")
        #remove the line below after testing
        #raise ValueError(f"File {source_name} is missing required columns: {', '.join(missing)}")
        return False

    return True

def build_metadata(source_name: str, file_path: Path, sha256_hash: str, registry_status: str, df: pd.DataFrame) -> dict:
    return {
        "source_name": source_name,
        "filename": file_path.name,
        "file_path": str(file_path.resolve()),
        "sha256_hash": sha256_hash,
        "registry_status": registry_status,
        "rows_read": len(df),
        "columns": list(df.columns),
        "ingested_at": datetime.now(timezone.utc),
    }

def load_source_file(file_path, required_columns, source_name):
    LOGGER_FUNCTION('info', f"\n--------------------------------------------------------------------------")
    LOGGER_FUNCTION('info', f"Starting Ingestion for {source_name}: {file_path}")

    #for now hashing function is giving the file_path
    sha256_hash = HASHING_FUNCTION(file_path)

    if sha256_hash is None:
        LOGGER_FUNCTION('warning', f"Skipping file {source_name} because hashing failed.")
        return None
    
    filename = str(PurePath(file_path).name)

    #getting status of file
    registry_status = check_registry_status(filename,sha256_hash)

    if registry_status == "unchanged":
        LOGGER_FUNCTION("info", f"File is unchanged for {source_name}. Attempting to load from cache...")
        
        # Try to load from cache
        cached_df = load_dataframe_cache(filename)
        if cached_df is not None:
            return cached_df, sha256_hash, registry_status
        else:
            LOGGER_FUNCTION("warning", f"No cache found for {source_name}. Re-reading file...")
            # Fall through to read the file anyway

    #now reading the df if file new or modified
    df = read_csv_file(file_path)

    # future changes
    # try:
    #     df = read_csv_file(file_path)
    # except Exception as e:
    #     LOGGER_FUNCTION("error", f"Failed to read {source_name}: {e}")
    #     return None
    #normalizing column names
    

    if df is None:
        store_registry_record(filename, file_path, sha256_hash, "failed_read")
        LOGGER_FUNCTION('warning', f"Skipping file {source_name} because reading CSV failed.")
        return None

    df = normalize_columns(df)

    LOGGER_FUNCTION('info', f"Read {len(df)} rows from {source_name}")

    if not validate_required_columns(df, required_columns, source_name): 
        LOGGER_FUNCTION('warning', f"Skipping file {source_name} because required columns are missing.")
        return None 
    

    #deciding what to do after receiving status
    if registry_status == "new":
        store_registry_record(filename, file_path, sha256_hash, "processed")
    else:
        update_registry_record(filename, file_path, sha256_hash, "updated")
    
    # Cache the dataframe for future use if file is unchanged
    save_dataframe_cache(filename, df)
    
    LOGGER_FUNCTION("info", f"Read {len(df)} rows from {source_name}")
    LOGGER_FUNCTION("info", f"Schema validation passed for {source_name}")
    
    return df, sha256_hash, registry_status

def load_exam_data():
    filename = PurePath(RAW_EXAM_PATH).name

    res = load_source_file(
        file_path= RAW_EXAM_PATH,
        required_columns = EXAM_COLUMNS,
        source_name = f"Exam Data ({filename})"
    )

    if res is not None:
        exam_df, sha256_hash, registry_status = res
        exam_metadata = build_metadata("Exam Data", RAW_EXAM_PATH, sha256_hash, registry_status, exam_df)

        return exam_df, exam_metadata
    else:
        return pd.DataFrame(), {}

def load_student_details_data():
    filename = PurePath(RAW_STUDENT_DETAILS_PATH).name

    res = load_source_file(
        file_path=RAW_STUDENT_DETAILS_PATH,
        required_columns= STUDENT_DETAILS_COLUMNS,
        source_name= f"Student Details Data ({filename})"
    )

    if res is not None:
        student_details_df, sha256_hash, registry_status = res
        student_details_metadata = build_metadata("Student Details Data", RAW_STUDENT_DETAILS_PATH, sha256_hash, registry_status, student_details_df)

        return student_details_df, student_details_metadata
    else:
        return pd.DataFrame(), {}

def load_attendance_data():
    filename = str(PurePath(RAW_ATTENDANCE_PATH).name)

    res = load_source_file(file_path=RAW_ATTENDANCE_PATH, required_columns=ATTENDANCE_COLUMNS, source_name=f"Attendance Data ({filename})")

    if res is not None:
        attendance_df, sha256_hash, registry_status = res

        attendance_metadata = build_metadata(source_name='Attendance Data', file_path=RAW_ATTENDANCE_PATH, sha256_hash=sha256_hash, registry_status=registry_status, df= attendance_df)

        return attendance_df, attendance_metadata
    else:
        return pd.DataFrame(), {}

def load_skills_data():
    filename = str(PurePath(RAW_SKILLS_PATH).name)

    res = load_source_file(
        file_path=RAW_SKILLS_PATH, required_columns=SKILLS_COLUMNS, source_name=f"Skills Data ({filename})"
    )

    if res is not None:
        skills_df, sha256_hash, registry_status = res

        skills_metadata = build_metadata(source_name="Skills Data", file_path=RAW_SKILLS_PATH, sha256_hash=sha256_hash, registry_status=registry_status, df=skills_df)

        return skills_df, skills_metadata
    else:
        return pd.DataFrame(), {}

def load_company_rules_data():
    filename = str(PurePath(RAW_COMPANY_RULES_PATH).name)

    res = load_source_file(
        file_path= RAW_COMPANY_RULES_PATH,
        required_columns= COMPANY_RULES_COLUMNS,
        source_name=f"Company Rules Data ({filename})"
    )

    if res is not None:
        company_rules_df, sha256_hash, registry_status = res

        company_rules_metadata = build_metadata(source_name="Company Rules Data", file_path=RAW_COMPANY_RULES_PATH, sha256_hash=sha256_hash, registry_status=registry_status, df=company_rules_df)

        return company_rules_df, company_rules_metadata
    else:
        return pd.DataFrame(), {}

def ingest_all_sources():
    LOGGER_FUNCTION('info', f"------------- Starting data ingestion... ------------- \n")
    exam_df, exam_metadata = load_exam_data()
    student_details_df, student_details_metadata = load_student_details_data()
    attendance_df, attendance_metadata = load_attendance_data()
    skills_df, skills_metadata = load_skills_data()
    company_rules_df, company_rules_metadata = load_company_rules_data()
    LOGGER_FUNCTION('info', f"------------- Finished data ingestion. ------------- \n")



    return {
        "exam_data": exam_df,
        "exam_metadata": exam_metadata,
        "student_details_data": student_details_df,
        "student_details_metadata": student_details_metadata,
        "attendance_data": attendance_df,
        "attendance_metadata": attendance_metadata,
        "skills_data": skills_df,
        "skills_metadata": skills_metadata,
        "company_rules_data": company_rules_df,
        "company_rules_metadata": company_rules_metadata
    }