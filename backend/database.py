import sqlite3
from datetime import datetime
import json

class Database:
    def __init__(self, db_path='eligibility.db'):
        self.db_path = db_path
        self.init_db()
        self.init_enrollment_table()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eligibility_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth DATE NOT NULL,
                qualified BOOLEAN NOT NULL,
                patient_info_json TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_check(self, first_name, last_name, dob, qualified, patient_info=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        patient_info_json = json.dumps(patient_info) if patient_info else None

        cursor.execute('''
            INSERT INTO eligibility_checks
            (first_name, last_name, date_of_birth, qualified, patient_info_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (first_name, last_name, dob, qualified, patient_info_json))

        conn.commit()
        conn.close()

    def get_recent_checks(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT first_name, last_name, date_of_birth, qualified, checked_at
            FROM eligibility_checks
            ORDER BY checked_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def init_enrollment_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cm_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_first_name TEXT NOT NULL,
                patient_last_name TEXT NOT NULL,
                medicaid_id TEXT NOT NULL,
                dob DATE NOT NULL,
                phone TEXT,
                alt_phone TEXT,
                email TEXT,
                preferred_contact TEXT,

                address_street TEXT,
                address_apt TEXT,
                address_city TEXT,
                address_state TEXT,
                address_zip TEXT,

                primary_diagnosis TEXT,
                substance_use_history TEXT,
                enrollment_location TEXT,
                referral_source TEXT,

                consent_given BOOLEAN,
                consent_date DATE,
                consent_method TEXT,
                witness_name TEXT,

                emergency_name TEXT,
                emergency_relation TEXT,
                emergency_phone TEXT,

                enrolled_by TEXT,
                enrollment_date TIMESTAMP,
                enrollment_status TEXT,

                eligibility_check_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_enrollment(self, enrollment_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Convert eligibility check data to JSON
        eligibility_json = json.dumps(enrollment_data.get('eligibility_check_data'))

        cursor.execute('''
            INSERT INTO cm_enrollments (
                patient_first_name, patient_last_name, medicaid_id, dob,
                phone, alt_phone, email, preferred_contact,
                address_street, address_apt, address_city, address_state, address_zip,
                primary_diagnosis, substance_use_history, enrollment_location, referral_source,
                consent_given, consent_date, consent_method, witness_name,
                emergency_name, emergency_relation, emergency_phone,
                enrolled_by, enrollment_date, enrollment_status,
                eligibility_check_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            enrollment_data.get('patient_first_name'),
            enrollment_data.get('patient_last_name'),
            enrollment_data.get('medicaid_id'),
            enrollment_data.get('dob'),
            enrollment_data.get('phone'),
            enrollment_data.get('alt_phone'),
            enrollment_data.get('email'),
            enrollment_data.get('preferred_contact'),
            enrollment_data.get('address_street'),
            enrollment_data.get('address_apt'),
            enrollment_data.get('address_city'),
            enrollment_data.get('address_state'),
            enrollment_data.get('address_zip'),
            enrollment_data.get('primary_diagnosis'),
            enrollment_data.get('substance_use_history'),
            enrollment_data.get('enrollment_location'),
            enrollment_data.get('referral_source'),
            enrollment_data.get('consent_given'),
            enrollment_data.get('consent_date'),
            enrollment_data.get('consent_method'),
            enrollment_data.get('witness_name'),
            enrollment_data.get('emergency_name'),
            enrollment_data.get('emergency_relation'),
            enrollment_data.get('emergency_phone'),
            enrollment_data.get('enrolled_by'),
            enrollment_data.get('enrollment_date'),
            enrollment_data.get('enrollment_status'),
            eligibility_json
        ))

        enrollment_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return enrollment_id
