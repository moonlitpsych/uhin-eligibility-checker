"""
Authentication module for CPSS Dashboard
Handles user registration, login, and JWT token management
"""

import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import jsonify, request, current_app
import secrets
import re

class AuthManager:
    def __init__(self, db_path='cpss_dashboard.db', secret_key=None):
        self.db_path = db_path
        self.secret_key = secret_key or secrets.token_hex(32)
        self.init_auth_tables()

    def init_auth_tables(self):
        """Ensure user tables exist with proper auth fields"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enhanced users table with auth fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'cpss',
                organization TEXT,
                npi TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                email_verified BOOLEAN DEFAULT 0,
                reset_token TEXT,
                reset_token_expires TIMESTAMP
            )
        ''')

        # Session/refresh tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                token_type TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                revoked BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()

    def hash_password(self, password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password, password_hash):
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        return True, "Password is valid"

    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def register_user(self, user_data):
        """Register a new user"""
        # Extract user data
        username = user_data.get('username', '').strip().lower()
        email = user_data.get('email', '').strip().lower()
        password = user_data.get('password')
        full_name = user_data.get('full_name', '').strip()
        role = user_data.get('role', 'cpss')
        organization = user_data.get('organization', '')
        npi = user_data.get('npi', '')
        phone = user_data.get('phone', '')

        # Validate required fields
        if not all([username, email, password, full_name]):
            return {'success': False, 'error': 'Missing required fields'}

        # Validate email format
        if not self.validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}

        # Validate password strength
        is_valid, msg = self.validate_password(password)
        if not is_valid:
            return {'success': False, 'error': msg}

        # Check if username or email already exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'error': 'Username or email already exists'}

        # Hash password and insert user
        password_hash = self.hash_password(password)

        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, organization, npi, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, role, organization, npi, phone))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Generate token for immediate login
            access_token = self.generate_token(user_id, username, role)
            refresh_token = self.generate_refresh_token(user_id)

            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'role': role,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}

    def login_user(self, username_or_email, password):
        """Authenticate user and return tokens"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find user by username or email
        cursor.execute('''
            SELECT id, username, email, password_hash, full_name, role, is_active
            FROM users
            WHERE (username = ? OR email = ?) AND is_active = 1
        ''', (username_or_email.lower(), username_or_email.lower()))

        user = cursor.fetchone()

        if not user:
            conn.close()
            return {'success': False, 'error': 'Invalid credentials'}

        # Verify password
        if not self.verify_password(password, user['password_hash']):
            conn.close()
            return {'success': False, 'error': 'Invalid credentials'}

        # Update last login
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                      (datetime.now(), user['id']))
        conn.commit()
        conn.close()

        # Generate tokens
        access_token = self.generate_token(user['id'], user['username'], user['role'])
        refresh_token = self.generate_refresh_token(user['id'])

        return {
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def generate_token(self, user_id, username, role, expires_in=3600):
        """Generate JWT access token (1 hour default)"""
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            'iat': datetime.now(timezone.utc),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def generate_refresh_token(self, user_id, expires_in=604800):
        """Generate refresh token (7 days default)"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            'iat': datetime.now(timezone.utc),
            'type': 'refresh',
            'jti': secrets.token_hex(16)  # Unique token ID
        }

        token = jwt.encode(payload, self.secret_key, algorithm='HS256')

        # Store refresh token in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO auth_tokens (user_id, token_hash, token_type, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode(),
              'refresh', datetime.now() + timedelta(seconds=expires_in)))

        conn.commit()
        conn.close()

        return token

    def verify_token(self, token):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {'valid': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}

    def refresh_access_token(self, refresh_token):
        """Use refresh token to get new access token"""
        # Verify refresh token
        result = self.verify_token(refresh_token)
        if not result['valid']:
            return {'success': False, 'error': result['error']}

        payload = result['payload']
        if payload.get('type') != 'refresh':
            return {'success': False, 'error': 'Invalid refresh token'}

        # Get user info
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT username, role FROM users WHERE id = ? AND is_active = 1',
                      (payload['user_id'],))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return {'success': False, 'error': 'User not found'}

        # Generate new access token
        access_token = self.generate_token(payload['user_id'], user['username'], user['role'])

        return {
            'success': True,
            'access_token': access_token
        }

    def logout_user(self, user_id, refresh_token=None):
        """Logout user and optionally revoke refresh token"""
        if refresh_token:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Revoke the refresh token
            token_hash = bcrypt.hashpw(refresh_token.encode(), bcrypt.gensalt()).decode()
            cursor.execute('''
                UPDATE auth_tokens
                SET revoked = 1
                WHERE user_id = ? AND token_type = 'refresh'
            ''', (user_id,))

            conn.commit()
            conn.close()

        return {'success': True, 'message': 'Logged out successfully'}

    def get_user_by_id(self, user_id):
        """Get user info by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, username, email, full_name, role, organization, npi, phone,
                   created_at, last_login, is_active, email_verified
            FROM users
            WHERE id = ?
        ''', (user_id,))

        user = cursor.fetchone()
        conn.close()

        if user:
            return dict(user)
        return None


# Flask decorator for protecting routes
def jwt_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Get token from header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header'}), 401

        if not token:
            return jsonify({'error': 'Authorization token required'}), 401

        # Verify token
        auth_manager = current_app.config.get('AUTH_MANAGER')
        if not auth_manager:
            return jsonify({'error': 'Authentication not configured'}), 500

        result = auth_manager.verify_token(token)
        if not result['valid']:
            return jsonify({'error': result['error']}), 401

        # Add user info to request
        request.current_user = result['payload']
        return f(*args, **kwargs)

    return decorated_function

def role_required(allowed_roles):
    """Decorator to check user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401

            user_role = request.current_user.get('role')
            if user_role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator