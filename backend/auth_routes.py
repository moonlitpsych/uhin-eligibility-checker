"""
Authentication API Routes
Handles user registration, login, logout, and token refresh
"""

from flask import Blueprint, request, jsonify, current_app
from backend.auth import AuthManager, jwt_required

# Create Blueprint
auth_api = Blueprint('auth_api', __name__)

@auth_api.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json

    # Validate required fields
    required_fields = ['username', 'email', 'password', 'full_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Get auth manager
    auth_manager = current_app.config.get('AUTH_MANAGER')
    if not auth_manager:
        auth_manager = AuthManager()
        current_app.config['AUTH_MANAGER'] = auth_manager

    # Register user
    result = auth_manager.register_user(data)

    if result['success']:
        return jsonify({
            'success': True,
            'user': {
                'id': result['user_id'],
                'username': result['username'],
                'role': result['role']
            },
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token']
        }), 201
    else:
        return jsonify({'error': result['error']}), 400

@auth_api.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json

    username_or_email = data.get('username')
    password = data.get('password')

    if not username_or_email or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # Get auth manager
    auth_manager = current_app.config.get('AUTH_MANAGER')
    if not auth_manager:
        auth_manager = AuthManager()
        current_app.config['AUTH_MANAGER'] = auth_manager

    # Attempt login
    result = auth_manager.login_user(username_or_email, password)

    if result['success']:
        return jsonify({
            'success': True,
            'user': result['user'],
            'access_token': result['access_token'],
            'refresh_token': result['refresh_token']
        })
    else:
        return jsonify({'error': result['error']}), 401

@auth_api.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    data = request.json
    refresh_token = data.get('refresh_token')

    if not refresh_token:
        return jsonify({'error': 'Refresh token is required'}), 400

    # Get auth manager
    auth_manager = current_app.config.get('AUTH_MANAGER')
    if not auth_manager:
        auth_manager = AuthManager()
        current_app.config['AUTH_MANAGER'] = auth_manager

    # Refresh token
    result = auth_manager.refresh_access_token(refresh_token)

    if result['success']:
        return jsonify({
            'success': True,
            'access_token': result['access_token']
        })
    else:
        return jsonify({'error': result['error']}), 401

@auth_api.route('/api/auth/logout', methods=['POST'])
@jwt_required
def logout():
    """Logout user"""
    data = request.json
    refresh_token = data.get('refresh_token')

    # Get auth manager
    auth_manager = current_app.config.get('AUTH_MANAGER')
    if not auth_manager:
        auth_manager = AuthManager()
        current_app.config['AUTH_MANAGER'] = auth_manager

    # Logout user
    user_id = request.current_user.get('user_id')
    result = auth_manager.logout_user(user_id, refresh_token)

    return jsonify(result)

@auth_api.route('/api/auth/me', methods=['GET'])
@jwt_required
def get_current_user():
    """Get current user info"""
    auth_manager = current_app.config.get('AUTH_MANAGER')
    if not auth_manager:
        auth_manager = AuthManager()
        current_app.config['AUTH_MANAGER'] = auth_manager

    user_id = request.current_user.get('user_id')
    user = auth_manager.get_user_by_id(user_id)

    if user:
        # Remove sensitive fields
        user.pop('password_hash', None)
        user.pop('reset_token', None)
        user.pop('reset_token_expires', None)
        return jsonify(user)
    else:
        return jsonify({'error': 'User not found'}), 404

@auth_api.route('/api/auth/verify', methods=['GET'])
@jwt_required
def verify_token():
    """Verify if token is valid"""
    return jsonify({
        'valid': True,
        'user': {
            'id': request.current_user.get('user_id'),
            'username': request.current_user.get('username'),
            'role': request.current_user.get('role')
        }
    })