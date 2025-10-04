from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sys
import os
from datetime import datetime
import secrets

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import UHINEligibilityChecker
from backend.database import Database
from backend.cpss_routes import cpss_api
from backend.auth_routes import auth_api
from backend.auth import AuthManager

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # For session management

# Initialize Auth Manager
auth_manager = AuthManager(secret_key=app.secret_key)
app.config['AUTH_MANAGER'] = auth_manager

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5174", "http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Authorization"],
        "supports_credentials": True
    }
})

# Register blueprints
app.register_blueprint(auth_api)
app.register_blueprint(cpss_api)

# Initialize
checker = UHINEligibilityChecker()
db = Database('backend/eligibility.db')

@app.route('/api/eligibility/check', methods=['POST'])
def check_eligibility():
    data = request.json

    # Extract patient info
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    dob = data.get('date_of_birth')

    # Validate inputs
    if not all([first_name, last_name, dob]):
        return jsonify({
            'success': False,
            'error': 'Missing required fields'
        }), 400

    # Check eligibility
    # Extract gender if provided, default to 'M' since Utah doesn't accept 'U'
    gender = data.get('gender', 'M')  # Default to M if not provided
    if gender == 'U':  # Utah Medicaid doesn't accept U
        gender = 'M'  # Default to M

    result = checker.check_eligibility(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=dob,
        gender=gender,
        test_mode=False,
        save_files=False
    )

    # Parse result
    qualified = result.get('qualified_for_cm', False)
    details = result.get('eligibility_details', {})
    patient_info = details.get('patient_info', {})

    # Save to database
    db.save_check(
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        qualified=qualified,
        patient_info=patient_info
    )

    # Return response - Include ALL data from the result for debugging
    response = {
        'success': result.get('success', False),
        'qualified': qualified,
        'checked_at': datetime.now().isoformat(),
        # Add detailed information for testing/debugging
        'eligibility_details': {
            'ffs_status': result.get('ffs_status', 'Unknown'),
            'ffs_qualification': result.get('ffs_qualification', 'Unknown'),
            'eligibility_info': details.get('eligibility_details', []) or details.get('eligibility_info', []),
            'plan_details': details.get('plan_info', {}) or details.get('plan_details', {}),
            'patient_info': patient_info,
            'payer_info': details.get('payer_info', {}),
            'rejection_reasons': details.get('rejection_reasons', []),
            'raw_response_summary': details.get('raw_segments', {}) or details.get('raw_response_summary', {}),
            'is_enrolled': details.get('eligible', False) or details.get('is_enrolled', False),
            'enrollment_type': details.get('enrollment_type', 'Unknown'),
            'errors': details.get('errors', []) or result.get('errors', []),
            'warnings': details.get('warnings', []),
            'summary': details.get('summary', '') or result.get('summary', ''),
            'managed_care_detected': details.get('managed_care_detected', False)
        }
    }

    if qualified and patient_info:
        response['patient_info'] = {
            'first_name': patient_info.get('first_name'),
            'last_name': patient_info.get('last_name'),
            'medicaid_id': patient_info.get('member_id'),
            'phone': patient_info.get('phone'),  # Check if available in 271
            'address': patient_info.get('address', {}),  # Check if available
            'dob': patient_info.get('dob')
        }

    return jsonify(response)

@app.route('/api/enrollment/create', methods=['POST'])
def create_enrollment():
    """Create a new CM program enrollment"""
    try:
        data = request.json

        # Extract enrollment data
        enrollment_data = {
            'patient_first_name': data.get('firstName'),
            'patient_last_name': data.get('lastName'),
            'medicaid_id': data.get('medicaidId'),
            'dob': data.get('dob'),
            'phone': data.get('phone'),
            'alt_phone': data.get('altPhone'),
            'email': data.get('email'),
            'preferred_contact': data.get('preferredContact'),

            # Address
            'address_street': data.get('street'),
            'address_apt': data.get('apt'),
            'address_city': data.get('city'),
            'address_state': data.get('state'),
            'address_zip': data.get('zip'),

            # Program info
            'primary_diagnosis': data.get('primaryDiagnosis'),
            'substance_use_history': data.get('substanceUseHistory'),
            'enrollment_location': data.get('enrollmentLocation'),
            'referral_source': data.get('referralSource'),

            # Consent
            'consent_given': data.get('consentGiven'),
            'consent_date': data.get('consentDate'),
            'consent_method': data.get('consentMethod'),
            'witness_name': data.get('witnessName'),

            # Emergency contact
            'emergency_name': data.get('emergencyName'),
            'emergency_relation': data.get('emergencyRelation'),
            'emergency_phone': data.get('emergencyPhone'),

            # Meta
            'enrolled_by': data.get('enrolledBy'),
            'enrollment_date': data.get('enrollmentDate'),
            'enrollment_status': 'active',

            # Original eligibility data
            'eligibility_check_data': data.get('eligibilityData')
        }

        # Save enrollment to database
        enrollment_id = db.save_enrollment(enrollment_data)

        return jsonify({
            'success': True,
            'enrollment_id': enrollment_id,
            'patient': {
                'firstName': enrollment_data['patient_first_name'],
                'lastName': enrollment_data['patient_last_name'],
                'medicaidId': enrollment_data['medicaid_id']
            },
            'message': 'Patient successfully enrolled in CM program'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/eligibility/recent', methods=['GET'])
def recent_checks():
    checks = db.get_recent_checks(limit=10)
    return jsonify({'checks': checks})

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')
