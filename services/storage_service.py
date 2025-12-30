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
        
        # Determine if we should use Postgres
        # We use Postgres if DATABASE_URL is present AND:
        # 1. We are in a cloud environment (VERCEL or RAILWAY_ENVIRONMENT)
        # 2. OR the user explicitly sets FORCE_POSTGRES=1
        is_cloud = os.environ.get('VERCEL') or os.environ.get('RAILWAY_ENVIRONMENT')
        force_postgres = os.environ.get('FORCE_POSTGRES')
        
        self.is_postgres = bool(self.db_url) and HAS_POSTGRES and (is_cloud or force_postgres)
        
        if self.is_postgres:
            print("✅ STORAGE: Using PostgreSQL (Cloud Persistent)")
        else:
            self._ensure_data_dir()
            if self.db_url and HAS_POSTGRES and not is_cloud:
                print("ℹ️  STORAGE: DATABASE_URL detected but using SQLite for local development.")
                print("            (Set FORCE_POSTGRES=1 in .env to override)")
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
            # Add timeout for concurrent access (wait up to 30 seconds for lock)
            conn = sqlite3.connect(DB_FILE, timeout=30.0)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent read/write performance
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=30000')  # 30 second timeout
            return conn

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Create jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    created_at TEXT,
                    status TEXT,
                    form_url TEXT,
                    raw_data TEXT
                )
            ''')

            # Syntax is compatible for this simple table structure
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id TEXT PRIMARY KEY,
                    job_id TEXT,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    resume_url TEXT,
                    linkedin_url TEXT,
                    job_description TEXT,
                    timestamp TEXT,
                    score REAL,
                    skills TEXT,
                    answers TEXT,
                    raw_data TEXT
                )
            ''')
            
            # Check if job_id column exists in candidates (for migration)
            try:
                if self.is_postgres:
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='candidates' AND column_name='job_id'")
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE candidates ADD COLUMN job_id TEXT")
                    
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='candidates' AND column_name='linkedin_url'")
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE candidates ADD COLUMN linkedin_url TEXT")
                    
                    # Add notes column
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='candidates' AND column_name='notes'")
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE candidates ADD COLUMN notes TEXT")
                    
                    # Add tags column
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='candidates' AND column_name='tags'")
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE candidates ADD COLUMN tags TEXT")
                    
                    # Check for edit_url in jobs
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='jobs' AND column_name='edit_url'")
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE jobs ADD COLUMN edit_url TEXT")
                else:
                    # SQLite check
                    cursor.execute("PRAGMA table_info(candidates)")
                    columns = [info[1] for info in cursor.fetchall()]
                    if 'job_id' not in columns:
                        cursor.execute("ALTER TABLE candidates ADD COLUMN job_id TEXT")
                    if 'linkedin_url' not in columns:
                        cursor.execute("ALTER TABLE candidates ADD COLUMN linkedin_url TEXT")
                    if 'notes' not in columns:
                        cursor.execute("ALTER TABLE candidates ADD COLUMN notes TEXT")
                    if 'tags' not in columns:
                        cursor.execute("ALTER TABLE candidates ADD COLUMN tags TEXT")
                        
                    # Check for edit_url in jobs
                    cursor.execute("PRAGMA table_info(jobs)")
                    columns = [info[1] for info in cursor.fetchall()]
                    if 'edit_url' not in columns:
                        cursor.execute("ALTER TABLE jobs ADD COLUMN edit_url TEXT")
            except Exception as e:
                print(f"⚠️ Error checking/adding columns: {e}")

            # Create indexes for performance
            try:
                if self.is_postgres:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_job_id ON candidates(job_id)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_score ON candidates(score DESC)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_timestamp ON candidates(timestamp DESC)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)")
                else:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_job_id ON candidates(job_id)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_score ON candidates(score DESC)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_timestamp ON candidates(timestamp DESC)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)")
                print("✅ Database indexes created/verified")
            except Exception as e:
                print(f"⚠️ Error creating indexes (non-critical): {e}")

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

    def create_job(self, job_data: Dict) -> Dict:
        if 'id' not in job_data:
            job_data['id'] = f"job_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}"
        if 'created_at' not in job_data:
            job_data['created_at'] = datetime.now().isoformat()
        if 'status' not in job_data:
            job_data['status'] = 'active'
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        raw_data_json = json.dumps(job_data)
        
        values = (
            job_data['id'],
            job_data.get('title', 'Untitled Job'),
            job_data.get('description', ''),
            job_data['created_at'],
            job_data['status'],
            job_data.get('form_url', ''),
            job_data.get('edit_url', ''),
            raw_data_json
        )
        
        if self.is_postgres:
            cursor.execute('''
                INSERT INTO jobs (id, title, description, created_at, status, form_url, edit_url, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', values)
        else:
            cursor.execute('''
                INSERT INTO jobs (id, title, description, created_at, status, form_url, edit_url, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)
            
        conn.commit()
        conn.close()
        return job_data

    def update_job_status(self, job_id: str, status: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if self.is_postgres:
                cursor.execute("UPDATE jobs SET status = %s WHERE id = %s", (status, job_id))
            else:
                cursor.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
            
            rows_affected = cursor.rowcount
            conn.commit()
            
            if rows_affected == 0:
                print(f"Warning: No job found with ID {job_id} to update status.")
                return False
                
            return True
        except Exception as e:
            print(f"Error updating job status: {e}")
            return False
        finally:
            conn.close()

    def delete_job(self, job_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Delete candidates associated with this job first
            if self.is_postgres:
                cursor.execute("DELETE FROM candidates WHERE job_id = %s", (job_id,))
                cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
            else:
                cursor.execute("DELETE FROM candidates WHERE job_id = ?", (job_id,))
                cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting job: {e}")
            return False
        finally:
            conn.close()

    def get_all_jobs(self) -> List[Dict]:
        conn = self._get_connection()
        if self.is_postgres:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
            
        cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        jobs = []
        for row in rows:
            job = dict(row)
            if job.get('raw_data'):
                try:
                    raw = json.loads(job['raw_data'])
                    # Merge raw data, but prioritize column values (e.g. status)
                    for k, v in raw.items():
                        if k not in job:
                            job[k] = v
                except: pass
            jobs.append(job)
            
        conn.close()
        return jobs

    def get_job(self, job_id: str) -> Optional[Dict]:
        conn = self._get_connection()
        if self.is_postgres:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM jobs WHERE id = %s', (job_id,))
        else:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
            
        row = cursor.fetchone()
        conn.close()
        
        if row:
            job = dict(row)
            if job.get('raw_data'):
                try:
                    raw = json.loads(job['raw_data'])
                    # Merge raw data, but prioritize column values
                    for k, v in raw.items():
                        if k not in job:
                            job[k] = v
                except: pass
            return job
        return None

    def get_all_candidates(self, job_id: str = None) -> List[Dict]:
        conn = self._get_connection()
        
        if self.is_postgres:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
        
        # JOIN with jobs table to get job_title
        query = '''
            SELECT c.*, j.title as job_title 
            FROM candidates c 
            LEFT JOIN jobs j ON c.job_id = j.id
        '''
        params = []
        
        if job_id:
            query += ' WHERE c.job_id = %s' if self.is_postgres else ' WHERE c.job_id = ?'
            params.append(job_id)
            
        query += ' ORDER BY c.timestamp DESC'
        
        cursor.execute(query, tuple(params))
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
            
            # Parse tags JSON if present
            if cand.get('tags'):
                try:
                    cand['tags'] = json.loads(cand['tags'])
                except:
                    cand['tags'] = []
            else:
                cand['tags'] = []
            
            # Notes is already a string, just ensure it exists
            if not cand.get('notes'):
                cand['notes'] = ''
                
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
            candidate_data.get('job_id'),
            candidate_data.get('name') or candidate_data.get('candidate_name'),
            candidate_data.get('email') or candidate_data.get('candidate_email'),
            candidate_data.get('phone') or candidate_data.get('candidate_phone'),
            candidate_data.get('resume_url') or candidate_data.get('file_url'),
            candidate_data.get('linkedin_url', ''),
            candidate_data.get('job_description'),
            candidate_data['timestamp'],
            candidate_data.get('total_score', 0),
            skills_json,
            answers_json,
            raw_data_json
        )
        
        if self.is_postgres:
            cursor.execute('''
                INSERT INTO candidates (id, job_id, name, email, phone, resume_url, linkedin_url, job_description, timestamp, score, skills, answers, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    job_id = EXCLUDED.job_id,
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    resume_url = EXCLUDED.resume_url,
                    linkedin_url = EXCLUDED.linkedin_url,
                    job_description = EXCLUDED.job_description,
                    timestamp = EXCLUDED.timestamp,
                    score = EXCLUDED.score,
                    skills = EXCLUDED.skills,
                    answers = EXCLUDED.answers,
                    raw_data = EXCLUDED.raw_data
            ''', values)
        else:
            cursor.execute('''
                INSERT OR REPLACE INTO candidates (id, job_id, name, email, phone, resume_url, linkedin_url, job_description, timestamp, score, skills, answers, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)
            
        conn.commit()
        conn.close()
        return candidate_data

    def get_recent_candidate_by_email(self, email: str, job_id: str = None, minutes: int = 10) -> Optional[Dict]:
        """Check if a candidate with this email (and optionally job_id) was added recently"""
        if not email:
            return None
            
        conn = self._get_connection()
        if self.is_postgres:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            if job_id:
                cursor.execute('''
                    SELECT * FROM candidates 
                    WHERE email = %s AND job_id = %s
                    AND timestamp::timestamp > (NOW() - make_interval(mins := %s))
                ''', (email, job_id, minutes))
            else:
                cursor.execute('''
                    SELECT * FROM candidates 
                    WHERE email = %s 
                    AND timestamp::timestamp > (NOW() - make_interval(mins := %s))
                ''', (email, minutes))
        else:
            cursor = conn.cursor()
            # SQLite: Fetch and filter in Python for safety
            if job_id:
                cursor.execute('SELECT * FROM candidates WHERE email = ? AND job_id = ?', (email, job_id))
            else:
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

    def delete_candidate(self, candidate_id: str) -> bool:
        """Delete a single candidate by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if self.is_postgres:
                cursor.execute('DELETE FROM candidates WHERE id = %s', (candidate_id,))
            else:
                cursor.execute('DELETE FROM candidates WHERE id = ?', (candidate_id,))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            return rows_affected > 0
        except Exception as e:
            print(f"Error deleting candidate: {e}")
            conn.close()
            return False

    def fix_orphan_candidates(self, target_job_id: str = None) -> Dict:
        """
        Fix candidates with no job_id by assigning them to a job.
        If target_job_id is provided, assign to that job.
        If only one active job exists, auto-assign to it.
        Returns stats about what was fixed.
        """
        jobs = self.get_all_jobs()
        candidates = self.get_all_candidates()
        
        orphans = [c for c in candidates if not c.get('job_id')]
        
        if not orphans:
            return {'fixed': 0, 'message': 'No orphan candidates found'}
        
        # Determine target job
        if target_job_id:
            target_job = next((j for j in jobs if j['id'] == target_job_id), None)
            if not target_job:
                return {'fixed': 0, 'error': f'Job {target_job_id} not found'}
        else:
            active_jobs = [j for j in jobs if j.get('status') == 'active']
            if len(active_jobs) == 1:
                target_job = active_jobs[0]
            elif len(active_jobs) == 0:
                return {'fixed': 0, 'error': 'No active jobs found'}
            else:
                return {
                    'fixed': 0, 
                    'error': 'Multiple active jobs - specify target_job_id',
                    'jobs': [{'id': j['id'], 'title': j['title']} for j in active_jobs]
                }
        
        # Fix orphans
        conn = self._get_connection()
        cursor = conn.cursor()
        
        fixed_count = 0
        for c in orphans:
            try:
                if self.is_postgres:
                    cursor.execute('UPDATE candidates SET job_id = %s WHERE id = %s', 
                                   (target_job['id'], c['id']))
                else:
                    cursor.execute('UPDATE candidates SET job_id = ? WHERE id = ?', 
                                   (target_job['id'], c['id']))
                
                # Also update raw_data
                raw_data = c.get('raw_data') or {}
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)
                raw_data['job_id'] = target_job['id']
                
                if self.is_postgres:
                    cursor.execute('UPDATE candidates SET raw_data = %s WHERE id = %s', 
                                   (json.dumps(raw_data), c['id']))
                else:
                    cursor.execute('UPDATE candidates SET raw_data = ? WHERE id = ?', 
                                   (json.dumps(raw_data), c['id']))
                
                fixed_count += 1
            except Exception as e:
                print(f"Error fixing candidate {c['id']}: {e}")
        
        conn.commit()
        conn.close()
        
        return {
            'fixed': fixed_count,
            'target_job': target_job['title'],
            'target_job_id': target_job['id'],
            'message': f'Fixed {fixed_count} orphan candidates'
        }

    def update_candidate_notes(self, candidate_id: str, notes: str) -> bool:
        """Update notes for a candidate"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if self.is_postgres:
                cursor.execute('UPDATE candidates SET notes = %s WHERE id = %s', (notes, candidate_id))
            else:
                cursor.execute('UPDATE candidates SET notes = ? WHERE id = ?', (notes, candidate_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating notes: {e}")
            conn.close()
            return False

    def update_candidate_tags(self, candidate_id: str, tags: list) -> bool:
        """Update tags for a candidate"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            tags_json = json.dumps(tags)
            if self.is_postgres:
                cursor.execute('UPDATE candidates SET tags = %s WHERE id = %s', (tags_json, candidate_id))
            else:
                cursor.execute('UPDATE candidates SET tags = ? WHERE id = ?', (tags_json, candidate_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating tags: {e}")
            conn.close()
            return False

    def get_analytics(self) -> Dict:
        """Get analytics data for dashboard"""
        conn = self._get_connection()
        if self.is_postgres:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
        
        analytics = {
            'total_candidates': 0,
            'total_jobs': 0,
            'active_jobs': 0,
            'candidates_by_status': {},
            'candidates_by_job': [],
            'score_distribution': {'0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0},
            'applications_over_time': [],
            'avg_score': 0,
            'top_skills': []
        }
        
        try:
            # Total candidates
            cursor.execute('SELECT COUNT(*) as count FROM candidates')
            row = cursor.fetchone()
            analytics['total_candidates'] = dict(row)['count'] if row else 0
            
            # Total jobs
            cursor.execute('SELECT COUNT(*) as count FROM jobs')
            row = cursor.fetchone()
            analytics['total_jobs'] = dict(row)['count'] if row else 0
            
            # Active jobs
            if self.is_postgres:
                cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE status = %s", ('active',))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE status = ?", ('active',))
            row = cursor.fetchone()
            analytics['active_jobs'] = dict(row)['count'] if row else 0
            
            # Average score
            cursor.execute('SELECT AVG(score) as avg FROM candidates WHERE score > 0')
            row = cursor.fetchone()
            analytics['avg_score'] = round(dict(row)['avg'] or 0, 1) if row else 0
            
            # Candidates by job
            cursor.execute('''
                SELECT j.title, COUNT(c.id) as count 
                FROM jobs j 
                LEFT JOIN candidates c ON j.id = c.job_id 
                GROUP BY j.id, j.title 
                ORDER BY count DESC
            ''')
            rows = cursor.fetchall()
            analytics['candidates_by_job'] = [dict(r) for r in rows]
            
            # Score distribution
            cursor.execute('SELECT score FROM candidates WHERE score IS NOT NULL')
            rows = cursor.fetchall()
            for row in rows:
                score = dict(row)['score'] or 0
                if score <= 20: analytics['score_distribution']['0-20'] += 1
                elif score <= 40: analytics['score_distribution']['21-40'] += 1
                elif score <= 60: analytics['score_distribution']['41-60'] += 1
                elif score <= 80: analytics['score_distribution']['61-80'] += 1
                else: analytics['score_distribution']['81-100'] += 1
            
            # Candidates by status (from raw_data)
            cursor.execute('SELECT raw_data FROM candidates')
            rows = cursor.fetchall()
            status_counts = {'applied': 0, 'interview_scheduled': 0, 'rejected': 0, 'pending': 0}
            for row in rows:
                try:
                    raw = json.loads(dict(row).get('raw_data', '{}'))
                    status = raw.get('status', 'applied')
                    if status in ['processed', 'pending']:
                        status = 'applied'
                    status_counts[status] = status_counts.get(status, 0) + 1
                except:
                    status_counts['applied'] += 1
            analytics['candidates_by_status'] = status_counts
            
            # Applications over time (last 30 days)
            cursor.execute('''
                SELECT DATE(timestamp) as date, COUNT(*) as count 
                FROM candidates 
                WHERE timestamp IS NOT NULL
                GROUP BY DATE(timestamp) 
                ORDER BY date DESC 
                LIMIT 30
            ''')
            rows = cursor.fetchall()
            analytics['applications_over_time'] = [dict(r) for r in rows][::-1]  # Reverse for chronological
            
        except Exception as e:
            print(f"Error getting analytics: {e}")
        finally:
            conn.close()
        
        return analytics

    def bulk_update_status(self, candidate_ids: List[str], new_status: str) -> int:
        """Update status for multiple candidates at once"""
        if not candidate_ids:
            return 0
            
        updated = 0
        for cid in candidate_ids:
            if self.update_status(cid, new_status):
                updated += 1
        return updated
