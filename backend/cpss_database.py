"""
CPSS Dashboard Database Schema
Manages pods, participants, sessions, and billing-related data
"""

import sqlite3
from datetime import datetime, timedelta
import json
import uuid

class CPSSDashboardDB:
    def __init__(self, db_path='cpss_dashboard.db'):
        self.db_path = db_path
        self.init_all_tables()

    def init_all_tables(self):
        """Initialize all CPSS dashboard tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # CPSS Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cpss_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                npi TEXT,
                organization TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        # CM Pods table (6-8 participants per pod)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cm_pods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pod_name TEXT NOT NULL,
                cpss_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_date DATE,
                end_date DATE,
                status TEXT DEFAULT 'active',
                max_participants INTEGER DEFAULT 8,
                meeting_schedule TEXT,
                notes TEXT,
                FOREIGN KEY (cpss_user_id) REFERENCES cpss_users(id)
            )
        ''')

        # Pod Participants (links enrollments to pods)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pod_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pod_id INTEGER NOT NULL,
                enrollment_id INTEGER NOT NULL,
                joined_date DATE NOT NULL,
                status TEXT DEFAULT 'active',
                progress_phase TEXT DEFAULT 'phase_1',
                total_sessions_attended INTEGER DEFAULT 0,
                total_tests_completed INTEGER DEFAULT 0,
                last_test_date DATE,
                last_session_date DATE,
                graduation_date DATE,
                notes TEXT,
                FOREIGN KEY (pod_id) REFERENCES cm_pods(id),
                FOREIGN KEY (enrollment_id) REFERENCES cm_enrollments(id)
            )
        ''')

        # Group Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pod_id INTEGER NOT NULL,
                session_uuid TEXT UNIQUE NOT NULL,
                scheduled_time TIMESTAMP NOT NULL,
                actual_start_time TIMESTAMP,
                actual_end_time TIMESTAMP,
                session_type TEXT NOT NULL, -- 'group_therapy', 'drug_test_observation', 'individual_checkin'
                video_room_id TEXT,
                recording_url TEXT,
                cpss_notes TEXT,
                billing_code TEXT, -- H0038, 98980, 98981, 99484
                billing_units INTEGER,
                billing_submitted BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'scheduled', -- scheduled, in_progress, completed, cancelled
                FOREIGN KEY (pod_id) REFERENCES cm_pods(id)
            )
        ''')

        # Session Attendance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                participant_id INTEGER NOT NULL,
                attendance_status TEXT NOT NULL, -- present, absent, late, excused
                join_time TIMESTAMP,
                leave_time TIMESTAMP,
                duration_minutes INTEGER,
                video_enabled BOOLEAN DEFAULT 0,
                audio_enabled BOOLEAN DEFAULT 0,
                participation_score INTEGER, -- 1-5 rating
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES group_sessions(id),
                FOREIGN KEY (participant_id) REFERENCES pod_participants(id)
            )
        ''')

        # Drug Tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drug_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL,
                session_id INTEGER,
                test_date TIMESTAMP NOT NULL,
                test_type TEXT NOT NULL, -- 'saliva', 'urine', 'breathalyzer'
                observed_by INTEGER, -- CPSS user id
                observation_method TEXT, -- 'in_person', 'video'
                substances_tested TEXT, -- JSON array of substances
                results TEXT, -- JSON object with substance:result pairs
                photo_url TEXT,
                video_url TEXT,
                verified BOOLEAN DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (participant_id) REFERENCES pod_participants(id),
                FOREIGN KEY (session_id) REFERENCES group_sessions(id),
                FOREIGN KEY (observed_by) REFERENCES cpss_users(id)
            )
        ''')

        # Behavioral Assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavioral_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL,
                assessment_type TEXT NOT NULL, -- 'PHQ-9', 'GAD-7', 'mood', 'craving', etc
                assessment_date TIMESTAMP NOT NULL,
                responses TEXT NOT NULL, -- JSON object with question:answer pairs
                total_score INTEGER,
                risk_level TEXT, -- 'low', 'moderate', 'high'
                administered_by INTEGER,
                notes TEXT,
                FOREIGN KEY (participant_id) REFERENCES pod_participants(id),
                FOREIGN KEY (administered_by) REFERENCES cpss_users(id)
            )
        ''')

        # Progress Milestones table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL,
                milestone_type TEXT NOT NULL, -- 'week_1', 'month_1', 'phase_complete', etc
                achieved_date DATE NOT NULL,
                milestone_data TEXT, -- JSON with specific milestone details
                reward_earned TEXT,
                notes TEXT,
                FOREIGN KEY (participant_id) REFERENCES pod_participants(id)
            )
        ''')

        # Billing Records table (for tracking billable events)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS billing_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL,
                session_id INTEGER,
                service_date DATE NOT NULL,
                cpt_code TEXT NOT NULL, -- H0038, 98980, 98981, 99484
                units INTEGER DEFAULT 1,
                duration_minutes INTEGER,
                provider_id INTEGER NOT NULL,
                documentation TEXT, -- Required documentation for billing
                claim_status TEXT DEFAULT 'pending', -- pending, submitted, accepted, denied
                claim_number TEXT,
                submitted_date DATE,
                payment_received BOOLEAN DEFAULT 0,
                payment_amount DECIMAL(10,2),
                notes TEXT,
                FOREIGN KEY (participant_id) REFERENCES pod_participants(id),
                FOREIGN KEY (session_id) REFERENCES group_sessions(id),
                FOREIGN KEY (provider_id) REFERENCES cpss_users(id)
            )
        ''')

        # Video Session Tokens (for secure video access)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                user_id INTEGER,
                participant_id INTEGER,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES group_sessions(id),
                FOREIGN KEY (user_id) REFERENCES cpss_users(id),
                FOREIGN KEY (participant_id) REFERENCES pod_participants(id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_pod(self, cpss_user_id, pod_name, start_date=None, max_participants=8):
        """Create a new CM pod"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO cm_pods (pod_name, cpss_user_id, start_date, max_participants)
            VALUES (?, ?, ?, ?)
        ''', (pod_name, cpss_user_id, start_date or datetime.now().date(), max_participants))

        pod_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return pod_id

    def add_participant_to_pod(self, pod_id, enrollment_id):
        """Add an enrolled participant to a pod"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check pod capacity
        cursor.execute('''
            SELECT COUNT(*) as current_count, p.max_participants
            FROM pod_participants pp
            JOIN cm_pods p ON pp.pod_id = p.id
            WHERE pp.pod_id = ? AND pp.status = 'active'
            GROUP BY p.max_participants
        ''', (pod_id,))

        result = cursor.fetchone()
        if result and result[0] >= result[1]:
            conn.close()
            raise ValueError(f"Pod {pod_id} is at maximum capacity")

        cursor.execute('''
            INSERT INTO pod_participants (pod_id, enrollment_id, joined_date)
            VALUES (?, ?, ?)
        ''', (pod_id, enrollment_id, datetime.now().date()))

        participant_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return participant_id

    def schedule_group_session(self, pod_id, scheduled_time, session_type, billing_code=None):
        """Schedule a group session for a pod"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        session_uuid = str(uuid.uuid4())

        cursor.execute('''
            INSERT INTO group_sessions (
                pod_id, session_uuid, scheduled_time, session_type, billing_code
            ) VALUES (?, ?, ?, ?, ?)
        ''', (pod_id, session_uuid, scheduled_time, session_type, billing_code))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return session_id, session_uuid

    def record_drug_test(self, participant_id, test_data):
        """Record a drug test result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO drug_tests (
                participant_id, session_id, test_date, test_type,
                observed_by, observation_method, substances_tested,
                results, photo_url, video_url, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            participant_id,
            test_data.get('session_id'),
            test_data.get('test_date', datetime.now()),
            test_data.get('test_type'),
            test_data.get('observed_by'),
            test_data.get('observation_method'),
            json.dumps(test_data.get('substances_tested', [])),
            json.dumps(test_data.get('results', {})),
            test_data.get('photo_url'),
            test_data.get('video_url'),
            test_data.get('notes')
        ))

        test_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return test_id

    def save_assessment(self, participant_id, assessment_data):
        """Save a behavioral assessment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO behavioral_assessments (
                participant_id, assessment_type, assessment_date,
                responses, total_score, risk_level, administered_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            participant_id,
            assessment_data.get('assessment_type'),
            assessment_data.get('assessment_date', datetime.now()),
            json.dumps(assessment_data.get('responses', {})),
            assessment_data.get('total_score'),
            assessment_data.get('risk_level'),
            assessment_data.get('administered_by'),
            assessment_data.get('notes')
        ))

        assessment_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return assessment_id

    def get_pod_participants(self, pod_id):
        """Get all participants in a pod with their details"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                pp.*,
                e.patient_first_name,
                e.patient_last_name,
                e.phone,
                e.medicaid_id
            FROM pod_participants pp
            JOIN cm_enrollments e ON pp.enrollment_id = e.id
            WHERE pp.pod_id = ? AND pp.status = 'active'
            ORDER BY pp.joined_date
        ''', (pod_id,))

        participants = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return participants

    def get_participant_progress(self, participant_id):
        """Get comprehensive progress data for a participant"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Basic participant info
        cursor.execute('''
            SELECT * FROM pod_participants WHERE id = ?
        ''', (participant_id,))
        participant = dict(cursor.fetchone())

        # Recent drug tests
        cursor.execute('''
            SELECT * FROM drug_tests
            WHERE participant_id = ?
            ORDER BY test_date DESC
            LIMIT 10
        ''', (participant_id,))
        participant['recent_tests'] = [dict(row) for row in cursor.fetchall()]

        # Recent assessments
        cursor.execute('''
            SELECT * FROM behavioral_assessments
            WHERE participant_id = ?
            ORDER BY assessment_date DESC
            LIMIT 5
        ''', (participant_id,))
        participant['recent_assessments'] = [dict(row) for row in cursor.fetchall()]

        # Session attendance
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN attendance_status = 'present' THEN 1 ELSE 0 END) as attended
            FROM session_attendance
            WHERE participant_id = ?
        ''', (participant_id,))
        attendance = cursor.fetchone()
        participant['attendance_rate'] = (attendance['attended'] / attendance['total'] * 100) if attendance['total'] > 0 else 0

        # Milestones
        cursor.execute('''
            SELECT * FROM progress_milestones
            WHERE participant_id = ?
            ORDER BY achieved_date DESC
        ''', (participant_id,))
        participant['milestones'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return participant

    def create_billing_record(self, billing_data):
        """Create a billing record for services rendered"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO billing_records (
                participant_id, session_id, service_date, cpt_code,
                units, duration_minutes, provider_id, documentation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            billing_data.get('participant_id'),
            billing_data.get('session_id'),
            billing_data.get('service_date'),
            billing_data.get('cpt_code'),
            billing_data.get('units', 1),
            billing_data.get('duration_minutes'),
            billing_data.get('provider_id'),
            billing_data.get('documentation')
        ))

        billing_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return billing_id

    def get_billing_summary(self, cpss_user_id, start_date, end_date):
        """Get billing summary for a CPSS user within date range"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                cpt_code,
                COUNT(*) as service_count,
                SUM(units) as total_units,
                SUM(duration_minutes) as total_minutes,
                claim_status
            FROM billing_records
            WHERE provider_id = ?
                AND service_date BETWEEN ? AND ?
            GROUP BY cpt_code, claim_status
        ''', (cpss_user_id, start_date, end_date))

        summary = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return summary