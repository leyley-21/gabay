"""Idempotent schema and explicit reference-table migration; learner history is preserved."""
from pathlib import Path
from app.db import database_connection
from app.config import DB_PATH

def initialize_database(path=None):
    path = Path(path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with database_connection(path) as conn:
        cursor = conn.cursor()
        # 1. Raw Feedback Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_feedback_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                onet_code TEXT NOT NULL,
                user_goal TEXT,
                education_level TEXT,
                riasec_cluster TEXT,
                feedback_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, onet_code, feedback_type)
            )
        ''')
    
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_feedback_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                onet_code TEXT NOT NULL,
                riasec_cluster TEXT NOT NULL,
                user_goal TEXT NOT NULL,
                net_score_boost REAL DEFAULT 0.0,
                total_interactions INTEGER DEFAULT 0,
                UNIQUE(onet_code, riasec_cluster, user_goal)
            )
        ''')
    
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_goal TEXT,
                education_level TEXT,
                riasec_scores TEXT,
                top_skills TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    
        cursor.execute("""CREATE TABLE IF NOT EXISTS occupations (
            onet_code TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT,
            job_zone INTEGER, college_majors TEXT, tech_voc TEXT, wfh_info TEXT,
            salary TEXT, is_wfh_capable INTEGER,
            realistic REAL NOT NULL, investigative REAL NOT NULL, artistic REAL NOT NULL,
            social REAL NOT NULL, enterprising REAL NOT NULL, conventional REAL NOT NULL
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS legacy_feedback_archive (
            source_id INTEGER PRIMARY KEY, job_title TEXT, action TEXT,
            engagement_time INTEGER, timestamp TEXT
        )""")
        cursor.execute("CREATE INDEX IF NOT EXISTS feedback_profile ON raw_feedback_logs(user_goal, riasec_cluster)")
        cursor.execute("""CREATE TABLE IF NOT EXISTS college_programs (
            onet_code TEXT PRIMARY KEY REFERENCES occupations(onet_code), programs TEXT NOT NULL,
            country TEXT NOT NULL, data_status TEXT NOT NULL, source_url TEXT, reviewed_on TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS tesda_programs (
            onet_code TEXT PRIMARY KEY REFERENCES occupations(onet_code), qualifications TEXT NOT NULL,
            country TEXT NOT NULL, data_status TEXT NOT NULL, source_url TEXT, reviewed_on TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS salary_ranges (
            onet_code TEXT PRIMARY KEY REFERENCES occupations(onet_code), salary_display TEXT NOT NULL,
            country TEXT NOT NULL, data_status TEXT NOT NULL, source_url TEXT, reviewed_on TEXT,
            currency TEXT NOT NULL, period TEXT NOT NULL)""")
        # Explicit migration: the user removed the school-directory feature.
        # Keep occupation/program mappings and assessment/feedback history.
        for removed in ('school_programs','school_campuses','discovery_cache','program_catalog'):
            cursor.execute('DROP TABLE IF EXISTS '+removed)
        salary_columns = {row[1] for row in cursor.execute('PRAGMA table_info(salary_ranges)')}
        for name, kind in {
            'min_amount':'REAL','max_amount':'REAL','median_amount':'REAL',
            'source_occupation':"TEXT NOT NULL DEFAULT ''",'source_name':"TEXT NOT NULL DEFAULT ''",
            'reference_year':"TEXT NOT NULL DEFAULT ''",'measure':"TEXT NOT NULL DEFAULT 'legacy_estimate'",
            'match_type':"TEXT NOT NULL DEFAULT 'unreviewed'",'mapping_note':"TEXT NOT NULL DEFAULT ''",
            'source_count':'INTEGER NOT NULL DEFAULT 0'
        }.items():
            if name not in salary_columns:cursor.execute('ALTER TABLE salary_ranges ADD COLUMN '+name+' '+kind)
        columns = {row[1] for row in cursor.execute('PRAGMA table_info(quiz_attempts)')}
        if 'question_responses' not in columns:
            cursor.execute('ALTER TABLE quiz_attempts ADD COLUMN question_responses TEXT')
        cursor.execute("""CREATE TABLE IF NOT EXISTS assessment_submissions (
            session_id TEXT NOT NULL, submission_id TEXT NOT NULL,
            request_hash TEXT NOT NULL, response_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(session_id, submission_id))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS request_limits (
            scope TEXT NOT NULL, subject TEXT NOT NULL, bucket INTEGER NOT NULL,
            count INTEGER NOT NULL, PRIMARY KEY(scope, subject, bucket))""")
        cursor.execute("CREATE INDEX IF NOT EXISTS request_limit_expiry ON request_limits(bucket)")
        cursor.execute("CREATE INDEX IF NOT EXISTS feedback_group_lookup ON raw_feedback_logs(onet_code,riasec_cluster,user_goal)")
    return path
