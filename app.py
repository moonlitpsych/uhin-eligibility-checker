from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
from main import UHINEligibilityChecker
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv('.env.local')

app = Flask(__name__)

# Initialize configuration
config = {
    'username': os.getenv('UHIN_USERNAME'),
    'password': os.getenv('UHIN_PASSWORD'),
    'endpoint': os.getenv('UHIN_ENDPOINT'),
    'trading_partner': os.getenv('UHIN_TRADING_PARTNER'),
    'receiver_id': os.getenv('UHIN_RECEIVER_ID'),
    'provider_npi': os.getenv('PROVIDER_NPI'),
    'provider_first': os.getenv('PROVIDER_FIRST_NAME'),
    'provider_last': os.getenv('PROVIDER_LAST_NAME')
}

def parse_detailed_271(raw_response):
    """Parse detailed information from X12 271 response"""
    details = {
        'member_id': None,
        'plan_name': None,
        'plan_type': None,
        'mco_name': None,
        'phone': None,
        'address': {},
        'coverage_status': None,
        'effective_date': None,
        'termination_date': None,
        'benefits': [],
        'is_targeted_adult': False,
        'transportation_vendor': None
    }
    
    if not raw_response:
        return details
    
    lines = raw_response.split('~')
    
    for i, line in enumerate(lines):
        # Member ID from REF segment
        if line.startswith('REF*HJ*') or line.startswith('REF*3H*'):
            parts = line.split('*')
            if len(parts) > 2:
                details['member_id'] = parts[2]
        
        # Subscriber/Member information
        if line.startswith('NM1*IL*'):
            parts = line.split('*')
            if len(parts) > 8:
                # Sometimes member ID is in NM1 segment
                if not details['member_id'] and parts[8] == 'MI':
                    details['member_id'] = parts[9] if len(parts) > 9 else None
        
        # Main Plan/Payer information (first NM1*PR is Utah Medicaid)
        if line.startswith('NM1*PR*') and not details['plan_name']:
            parts = line.split('*')
            if len(parts) > 3:
                payer_name = parts[3]
                # This is the main payer - Utah Medicaid
                if 'UTAH MEDICAID' in payer_name.upper():
                    details['plan_name'] = 'Utah Medicaid'
                    details['plan_type'] = 'TRADITIONAL_FFS'  # Default to FFS
                # Check for actual MCOs
                elif any(mco in payer_name.upper() for mco in ['MOLINA', 'SELECTHEALTH', 'HEALTHY U', 'ANTHEM']):
                    details['mco_name'] = payer_name
                    details['plan_type'] = 'MANAGED_CARE'
                    details['plan_name'] = payer_name
        
        # Address information
        if line.startswith('N3*'):
            parts = line.split('*')
            if len(parts) > 1:
                details['address']['street'] = parts[1]
                if len(parts) > 2 and parts[2]:
                    details['address']['street2'] = parts[2]
        
        if line.startswith('N4*'):
            parts = line.split('*')
            if len(parts) > 3:
                details['address']['city'] = parts[1]
                details['address']['state'] = parts[2]
                details['address']['zip'] = parts[3]
        
        # Phone number
        if line.startswith('PER*'):
            parts = line.split('*')
            for j in range(len(parts)):
                if parts[j] == 'TE' and j + 1 < len(parts):
                    details['phone'] = parts[j + 1]
        
        # Eligibility/Benefit information
        if line.startswith('EB*'):
            parts = line.split('*')
            if len(parts) > 1:
                # Coverage status
                if parts[1] == '1':
                    details['coverage_status'] = 'Active Coverage'
                elif parts[1] == '6':
                    details['coverage_status'] = 'Inactive Coverage'
                elif parts[1] == 'I':
                    details['coverage_status'] = 'Non-Covered'
                elif parts[1] == '3':
                    # This is for special services like transportation
                    continue
                
                # Look for plan details
                if len(parts) > 4:
                    plan_info = parts[4] if parts[4] else ''
                    
                    # Check for specific Medicaid programs - MOST IMPORTANT
                    if 'TARGETED ADULT MEDICAID' in plan_info.upper():
                        details['is_targeted_adult'] = True
                        details['plan_name'] = 'Targeted Adult Medicaid'
                        details['plan_type'] = 'TRADITIONAL_FFS'  # Targeted Adult is FFS
                    elif 'EXPANSION' in plan_info.upper() or 'PCN' in plan_info.upper():
                        details['plan_name'] = 'Medicaid Expansion'
                    elif 'TRADITIONAL' in plan_info.upper():
                        details['plan_name'] = 'Traditional Medicaid'
                    
                    # Transportation vendor is NOT an MCO
                    if 'NON EMERGENCY TRANSPORTATION' in plan_info.upper():
                        # Skip - this is just transportation, not the main plan
                        continue
                
                # Store benefit details (but skip transportation as main benefit)
                if len(parts) > 2 and 'TRANSPORTATION' not in (parts[4] if len(parts) > 4 else '').upper():
                    benefit = {
                        'status': parts[1],
                        'type': parts[2] if len(parts) > 2 else '',
                        'description': parts[4] if len(parts) > 4 else ''
                    }
                    details['benefits'].append(benefit)
        
        # Date information
        if line.startswith('DTP*'):
            parts = line.split('*')
            if len(parts) > 3:
                date_qualifier = parts[1]
                date_value = parts[3]
                
                if date_qualifier == '291':  # Plan begin
                    details['effective_date'] = format_x12_date(date_value)
                elif date_qualifier == '036':  # Plan end
                    details['termination_date'] = format_x12_date(date_value)
    
    return details

def format_x12_date(date_str):
    """Format X12 date (YYYYMMDD) to readable format"""
    if len(date_str) == 8:
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%B %d, %Y')
        except:
            pass
    return date_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_eligibility', methods=['POST'])
def check_eligibility():
    try:
        data = request.json
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        dob = data.get('dateOfBirth', '').strip()
        
        if not all([first_name, last_name, dob]):
            return jsonify({
                'success': False,
                'error': 'Please provide all required fields'
            }), 400
        
        # Initialize checker
        checker = UHINEligibilityChecker(config)
        
        # Try to guess gender from first name for better matching
        # This is a simple heuristic - could be improved
        gender = 'U'
        male_names = ['jeremy', 'john', 'james', 'robert', 'michael', 'david', 'william', 'tanner']
        female_names = ['mary', 'jennifer', 'linda', 'patricia', 'elizabeth', 'susan', 'jessica']
        
        if first_name.lower() in male_names:
            gender = 'M'
        elif first_name.lower() in female_names:
            gender = 'F'
        
        # Check eligibility
        result = checker.check_eligibility(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=dob,
            gender=gender,
            member_id=None  # Will search by name/DOB
        )
        
        # Check if we got a 999 rejection
        if result.get('eligibility_details', {}).get('transaction_info', {}).get('type') == '999':
            # This is a 999 rejection - patient may not be in system
            return jsonify({
                'success': False,
                'error': 'Unable to verify eligibility. The patient may not be enrolled in Utah Medicaid or there may be an issue with the search criteria.',
                'rejection_type': '999',
                'details': 'The eligibility system could not process this request. Please verify the patient information and try again.'
            }), 400
        
        # Get raw 271 response for parsing
        raw_271 = result.get('eligibility_details', {}).get('raw_271_response', '') or result.get('raw_271_response', '')
        
        # Parse detailed information
        details = parse_detailed_271(raw_271)
        
        # Determine CM qualification based on Targeted Adult Medicaid
        qualified_for_cm = details['is_targeted_adult'] or (
            details['plan_type'] == 'TRADITIONAL_FFS' and 
            details['plan_name'] and 
            'TARGETED' in details['plan_name'].upper()
        )
        
        # Combine results
        response = {
            'success': True,
            'qualified_for_cm': qualified_for_cm,
            'ffs_status': 'TRADITIONAL_FFS' if details['is_targeted_adult'] else result.get('ffs_status', 'UNKNOWN'),
            'member_id': details['member_id'] or result.get('member_id'),
            'plan_name': details['plan_name'] or result.get('plan_details', {}).get('name'),
            'plan_type': details['plan_type'] or result.get('ffs_status'),
            'mco_name': details['mco_name'],
            'phone': details['phone'],
            'address': details['address'],
            'coverage_status': details['coverage_status'],
            'effective_date': details['effective_date'],
            'termination_date': details['termination_date'],
            'benefits': details['benefits'][:5] if details['benefits'] else [],  # Limit to first 5
            'raw_response': result.get('raw_271_response', '') if data.get('showRaw') else None
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)