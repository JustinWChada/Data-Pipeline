#All settings in one place, paths, column name, thresholds
from pathlib import Path

#paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR /"data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
REGISTRY_DIR = DATA_DIR / "registry"
TEXTFILES_DIR = DATA_DIR / "textfiles"
LOG_DIR = BASE_DIR / "logs"

#specified files
RAW_STUDENT_DETAILS_PATH = RAW_DIR / "student_details.csv"
RAW_EXAM_PATH = RAW_DIR /"exam_cell.csv"
# RAW_BACKLOG_PATH = RAW_DIR / "backlogs.csv"
RAW_SKILLS_PATH = RAW_DIR / "skills_portal.csv"
RAW_ATTENDANCE_PATH = RAW_DIR / "attendance.csv"
RAW_COMPANY_RULES_PATH = RAW_DIR / "company_rules.csv"

DB_CONN_STRING = "postgresql+psycopg2://postgres:12345@localhost:5432/pipeline"


#if needed comment
#SOFTWARE_SKILLS = ["Python", "Java", "SQL", "React"]


#threshold
TIMEOUT_THRESHOLD = 2.0
CGPA_THRESHOLD  = 7.5
MISSING_VALUE_STRATEGY = 'drop'

DEPARTMENTS = ['CSE', 'ME', 'CE', 'BCA']

DEPARTMENTS_MAPPING = {
    "cse": "CSE",
    "computer science": "CSE",
    "computer science and engineering": "CSE",
    "me": "ME",
    "mechanical": "ME",
    "mechanical engineering": "ME",
    "ce": "CE",
    "civil": "CE",
    "civil engineering": "CE",
    'MECH': 'ME',
    'CIVIL': 'CE',
    "bca": "BCA",
    'Computer Applications': 'BCA'
}

#required columns
STUDENT_DETAILS_COLUMNS = [
    'student_id',
    'first_name',
    'last_name',
    'department',
    'batch',
    'current_semester'
]

EXAM_COLUMNS = [
    'student_id',
    'cgpa',
    'latest_sgpa',
    'active_backlogs',
    'has_backlog_history'
]

ATTENDANCE_COLUMNS = [
    'student_id',
    'attendance_percentage'
]

SKILLS_COLUMNS = [
    'student_id',
    'technical_skills',
    'soft_skills',
    'project_titles'
]

COMPANY_RULES_COLUMNS = [
    'company_name',
    'minimum_cgpa',
    'allowed_departments',
    'allows_backlog_history',
    'max_active_backlogs',
    'required_technical_skills',
    'required_soft_skills'
]

PREPROCESSED_SCHEMA = [
    "student_id",
    "full_name",
    "department",
    "batch",
    "current_semester",
    "cgpa",
    "latest_sgpa",
    "active_backlogs",
    "has_backlog_history",
    "attendance_percentage",
    "technical_skills",
    "soft_skills",
    "project_titles",
    "project_count"
]

OUTPUT_SCHEMA = [
    'student_id',
    'full_name',
    'department',
    'batch',
    'current_semester',
    'cgpa',
    'latest_sgpa',
    'active_backlogs',
    'has_backlog_history',
    'attendance_percentage',
    'technical_skills',
    'soft_skills',
    'project_titles',
    'project_count',
    'placement_category',
    'eligibility_status',
    'readiness_score'
]


#required columns
COLUMN_TYPE_MAPPING = {
    'student_id': int,
    'first_name': str,
    'last_name': str,
    'department': str,
    'batch': str,
    'current_semester': int,
    'cgpa': float,
    'latest_sgpa': float,
    'active_backlogs': int,
    'has_backlog_history': bool,
    'attendance_percentage': float,
    'technical_skills': str,
    'soft_skills': str,
    'project_titles': str,
    'company_name': str,
    'minimum_cgpa': float,
    'allowed_departments': str,
    'allows_backlog_history': bool,
    'max_active_backlogs': int,
    'required_technical_skills': str,
    'required_soft_skills': str,
    'project_count': int,
    'placement_category': str,
    'eligibility_status': str,
    'readiness_score': float
}