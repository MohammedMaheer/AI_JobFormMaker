import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# Try importing psycopg2 for PostgreSQL support (Production)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

DATA_DIR = 'data'
DB_FILE = os.path.join(DATA_DIR, 'candidates.db')
JSON_FILE = os.path.join(DATA_DIR, 'candidates.json')

class StorageService:
    def __init__(self):
        # Check for DATABASE_URL environment variable (Vercel/Neon)
        self.db_url = os.environ.get('DATABASE_URL')
        self.is_postgres = bool(self.db_url) and HAS_POSTGRES
        
        if self.is_postgres:
            print("✅ STORAGE: Using PostgreSQL (Cloud Persistent)")
        else:
            self._ensure_data_dir()
            print(f"✅ STORAGE: Using SQLite at {DB_FILE} (Local Persistent)")
            
        self._init_db()
        
        # Only migrate from JSON if we are using local SQLite
        if not self.is_postgres:
            self._migrate_from_json_if_needed()
    
    def _ensure_data_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def _get_connection(self):
        if self.is_postgres:
            return psycopg2.connect(self.db_url)
        else:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Syntax is compatible for this simple table structure
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    resume_url TEXT,
                    job_description TEXT,
                    timestamp TEXT,
                    score REAL,
                    skills TEXT,
                    answers TEXT,
                    raw_data TEXT
                )
            ''')
            conn.commit()
        except Exception as e:
            # Handle Postgres race condition where type exists but table creation fails
            if "pg_type_typname_nsp_index" in str(e):
                print("⚠️ Table creation race condition ignored (type exists).")
                conn.rollback()
            else:
                print(f"❌ Database initialization error: {e}")
                # Don't raise, just log. If the table doesn't exist, subsequent queries will fail anyway.
        finally:
            conn.close()

    def _migrate_from_json_if_needed(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT count(*) FROM candidates')
        count = cursor.fetchone()[0]
        
        if count == 0 and os.path.exists(JSON_FILE):
            print("Migrating data from JSON to SQLite...")
            try:
                with open(JSON_FILE, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for candidate in data:
                            self.save_candidate(candidate)
                print("Migration complete.")
            except Exception as e:
                print(f"Migration failed: {e}")
        conn.close()

    def get_all_candidates(self) -> List[Dict]:
        conn = self._get_connection()
        
        if self.is_postgres:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
            
        cursor.execute('SELECT * FROM candidates ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        
        candidates = []
        for row in rows:
            cand = dict(row)
            if cand.get('skills'):
                try: cand['skills'] = json.loads(cand['skills'])
                except: cand['skills'] = {}
            if cand.get('answers'):
                try: cand['answers'] = json.loads(cand['answers'])
                except: cand['answers'] = {}
            if cand.get('raw_data'):
                try: 
                    cand['raw_data'] = json.loads(cand['raw_data'])
                    raw = cand['raw_data']
                    
                    # Promote fields from raw_data if missing in columns
                    if not cand.get('name') and raw.get('candidate_name'):
                        cand['name'] = raw['candidate_name']
                    if not cand.get('email') and raw.get('candidate_email'):
                        cand['email'] = raw['candidate_email']
                    if not cand.get('phone') and raw.get('candidate_phone'):
                        cand['phone'] = raw['candidate_phone']
                    if not cand.get('score') and raw.get('total_score'):
                        cand['total_score'] = raw['total_score']
                    elif cand.get('score'): # Map score col to total_score key
                        cand['total_score'] = cand['score']
                        
                    # Promote status from raw_data if not present
                    if 'status' not in cand and 'status' in raw:
                        cand['status'] = raw['status']

                    # Promote complex objects (breakdown, ai_analysis)
                    if 'breakdown' not in cand and 'breakdown' in raw:
                        cand['breakdown'] = raw['breakdown']
                    if 'ai_analysis' not in cand and 'ai_analysis' in raw:
                        cand['ai_analysis'] = raw['ai_analysis']
                        
                    # Ensure candidate_name is available as alias
                    cand['candidate_name'] = cand.get('name')
                    cand['candidate_email'] = cand.get('email')
                    cand['candidate_phone'] = cand.get('phone')
                    
                except Exception as e: 
                    print(f"Error parsing raw_data: {e}")
                    cand['raw_data'] = {}
            
            # Default status if missing
            if 'status' not in cand:
                cand['status'] = 'applied'
            
            # Ensure total_score is present
            if 'total_score' not in cand and cand.get('score'):
                cand['total_score'] = cand['score']
                
            candidates.append(cand)
        
        conn.close()
        return candidates
    
    def update_status(self, candidate_id: str, new_status: str) -> bool:
        """Update the status of a candidate in raw_data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Get current raw_data
        if self.is_postgres:
            cursor.execute('SELECT raw_data FROM candidates WHERE id = %s', (candidate_id,))
        else:
            cursor.execute('SELECT raw_data FROM candidates WHERE id = ?', (candidate_id,))
            
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
            
        try:
            raw_data_str = row[0] if self.is_postgres else row['raw_data']
            raw_data = json.loads(raw_data_str) if raw_data_str else {}
            
            # 2. Update status
            raw_data['status'] = new_status
            
            # 3. Save back
            if self.is_postgres:
                cursor.execute('UPDATE candidates SET raw_data = %s WHERE id = %s', (json.dumps(raw_data), candidate_id))
            else:
                cursor.execute('UPDATE candidates SET raw_data = ? WHERE id = ?', (json.dumps(raw_data), candidate_id))
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            conn.close()
            return False

    def save_candidate(self, candidate_data: Dict) -> Dict:
        if 'id' not in candidate_data:
            candidate_data['id'] = f"cand_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}"
        if 'timestamp' not in candidate_data:
            candidate_data['timestamp'] = datetime.now().isoformat()
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        skills_json = json.dumps(candidate_data.get('skills', {}))
        answers_json = json.dumps(candidate_data.get('answers', {}))
        raw_data_json = json.dumps(candidate_data)
        
        values = (
            candidate_data['id'],
            candidate_data.get('name') or candidate_data.get('candidate_name'),
            candidate_data.get('email') or candidate_data.get('candidate_email'),
            candidate_data.get('phone') or candidate_data.get('candidate_phone'),
            candidate_data.get('resume_url') or candidate_data.get('file_url'),
            candidate_data.get('job_description'),
            candidate_data['timestamp'],
            candidate_data.get('total_score', 0),
            skills_json,
            answers_json,
            raw_data_json
        )
        
        if self.is_postgres:
            cursor.execute('''
                INSERT INTO candidates (id, name, email, phone, resume_url, job_description, timestamp, score, skills, answers, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    resume_url = EXCLUDED.resume_url,
                    job_description = EXCLUDED.job_description,
                    timestamp = EXCLUDED.timestamp,
                    score = EXCLUDED.score,
                    skills = EXCLUDED.skills,
                    answers = EXCLUDED.answers,
                    raw_data = EXCLUDED.raw_data
            ''', values)
        else:
            cursor.execute('''
                INSERT OR REPLACE INTO candidates (id, name, email, phone, resume_url, job_description, timestamp, score, skills, answers, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)
            
        conn.commit()
        conn.close()
        return candidate_data

    def get_recent_candidate_by_email(self, email: str, minutes: int = 10) -> Optional[Dict]:
        """Check if a candidate with this email was added recently"""
        if not email:
            return None
            
        conn = self._get_connection()
        if self.is_postgres:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            # Postgres timestamp comparison
            cursor.execute('''
                SELECT * FROM candidates 
                WHERE email = %s 
                AND timestamp > (NOW() - INTERVAL '%s minutes')
            ''', (email, minutes))
        else:
            cursor = conn.cursor()
            # SQLite timestamp comparison (assuming ISO format strings)
            # We'll fetch matches by email and filter in python to be safe with string formats
            cursor.execute('SELECT * FROM candidates WHERE email = ?', (email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
            
        # Filter for recency (especially for SQLite)
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        
        for row in rows:
            row_dict = dict(row)
            try:
                # Parse ISO timestamp
                ts_str = row_dict['timestamp']
                # Handle various formats
                if 'T' in ts_str:
                    ts = datetime.fromisoformat(ts_str).timestamp()
                else:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f").timestamp()
                
                if ts > cutoff_time:
                    return row_dict
            except Exception as e:
                print(f"Error parsing timestamp {ts_str}: {e}")
                continue
                
        return None

    def clear_candidates(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM candidates')
        conn.commit()
        conn.close()
