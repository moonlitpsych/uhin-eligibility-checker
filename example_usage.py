#!/usr/bin/env python3
"""
Example Usage of UHIN Utah Medicaid Eligibility Checker

This script demonstrates how to use the eligibility checker in your own code.
"""

import os
from datetime import datetime
from main import UHINEligibilityChecker


def basic_example():
    """Basic example of checking a single patient's eligibility"""
    
    # Option 1: Use environment variables for credentials
    # Set these in your .env file or shell:
    # export UHIN_USERNAME='your_username'
    # export UHIN_PASSWORD='your_password'
    # export PROVIDER_NPI='your_npi'
    
    # Option 2: Pass credentials directly (be careful not to commit these!)
    config = {
        'username': os.getenv('UHIN_USERNAME', 'your_username'),
        'password': os.getenv('UHIN_PASSWORD', 'your_password'),
        'provider_npi': os.getenv('PROVIDER_NPI', '1234567890'),
        'provider_name': 'YOUR_PRACTICE',
        'trading_partner': 'HT009582-001',  # Your UHIN TPN
        'receiver_id': 'HT000004-001'  # Utah Medicaid Production
    }
    
    # Create checker instance
    checker = UHINEligibilityChecker(config)
    
    # Check eligibility for a patient
    result = checker.check_eligibility(
        first_name='John',
        last_name='Doe',
        date_of_birth='1990-01-15',  # Format: YYYY-MM-DD
        gender='M',  # M, F, or U
        member_id=None,  # Optional, provide if known
        test_mode=False,  # Use True for test environment
        save_files=True  # Save X12 messages to files
    )
    
    # Check the results
    if result['success']:
        if result['qualified_for_cm']:
            print(f"✅ Patient QUALIFIES for Contingency Management")
            print(f"   FFS Status: {result['ffs_status']}")
        else:
            print(f"⚠️ Patient DOES NOT QUALIFY for CM")
            print(f"   Reason: {result['ffs_status']}")
            
        # Access detailed information
        details = result.get('eligibility_details', {})
        if details.get('patient_info'):
            patient = details['patient_info']
            print(f"   Patient: {patient.get('first_name')} {patient.get('last_name')}")
            
        if details.get('summary'):
            print(f"   Summary: {details['summary']}")
    else:
        print(f"❌ Eligibility check failed")
        if result.get('errors'):
            print(f"   Errors: {', '.join(result['errors'])}")
    
    return result


def batch_example():
    """Example of checking multiple patients"""
    
    # Create checker instance (credentials from environment)
    checker = UHINEligibilityChecker()
    
    # List of patients to check
    patients = [
        {
            'first_name': 'Jeremy',
            'last_name': 'Montoya',
            'date_of_birth': '1984-07-17',
            'gender': 'M',
            'member_id': '0900412827'
        },
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': '1985-05-15',
            'gender': 'F'
        },
        {
            'first_name': 'Robert',
            'last_name': 'Johnson',
            'date_of_birth': '1978-12-03',
            'gender': 'M'
        }
    ]
    
    # Check each patient
    results = []
    for patient in patients:
        print(f"\nChecking {patient['first_name']} {patient['last_name']}...")
        
        result = checker.check_eligibility(
            first_name=patient['first_name'],
            last_name=patient['last_name'],
            date_of_birth=patient['date_of_birth'],
            gender=patient.get('gender', 'U'),
            member_id=patient.get('member_id'),
            test_mode=True,  # Using test mode for this example
            save_files=False  # Don't save files for batch processing
        )
        
        results.append({
            'patient': patient,
            'qualified': result.get('qualified_for_cm', False),
            'status': result.get('ffs_status', 'UNKNOWN'),
            'success': result.get('success', False)
        })
    
    # Summary report
    print("\n" + "="*60)
    print("BATCH ELIGIBILITY CHECK RESULTS")
    print("="*60)
    
    qualified_count = sum(1 for r in results if r['qualified'])
    print(f"\nTotal Patients Checked: {len(results)}")
    print(f"Qualified for CM: {qualified_count}")
    print(f"Not Qualified: {len(results) - qualified_count}")
    
    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        patient = result['patient']
        status_icon = "✅" if result['qualified'] else "❌"
        print(f"{i}. {patient['first_name']} {patient['last_name']} - {status_icon} {result['status']}")
    
    return results


def parse_existing_x12_271():
    """Example of parsing an existing X12 271 response"""
    
    from parser import X12_271Parser
    
    # Load an existing X12 271 response (e.g., from a file)
    with open('output/x12_271_sample.txt', 'r') as f:
        x12_271_content = f.read()
    
    # Parse the response
    parser = X12_271Parser()
    result = parser.parse(x12_271_content)
    
    # Display results
    print("Parsed X12 271 Response:")
    print(f"  Eligible: {result['eligible']}")
    print(f"  FFS Status: {result['ffs_status']}")
    print(f"  CM Qualification: {result['ffs_qualification']}")
    print(f"  Summary: {result['summary']}")
    
    # Get formatted output
    formatted = parser.format_response(result)
    print(formatted)
    
    return result


def build_x12_270_only():
    """Example of just building an X12 270 message without sending it"""
    
    from x12_builder import X12_270Builder
    
    config = {
        'trading_partner': 'HT009582-001',
        'receiver_id': 'HT000004-001',
        'provider_npi': '1234567890',
        'provider_name': 'DOE',
        'provider_first_name': 'JOHN'
    }
    
    builder = X12_270Builder(config)
    
    # Build the message
    x12_270 = builder.build(
        patient_first_name='Jane',
        patient_last_name='Smith',
        patient_dob='1985-05-15',
        patient_gender='F',
        member_id='123456789',
        test_mode=False
    )
    
    # Validate it
    validation = builder.validate(x12_270)
    
    print("Generated X12 270 Message:")
    print("-" * 40)
    print(x12_270)
    print("-" * 40)
    print(f"Valid: {validation['valid']}")
    
    if not validation['valid']:
        print(f"Errors: {validation['errors']}")
    
    # Save to file
    with open('output/x12_270_example.txt', 'w') as f:
        f.write(x12_270)
    print("Saved to output/x12_270_example.txt")
    
    return x12_270


if __name__ == '__main__':
    print("UHIN Utah Medicaid Eligibility Checker - Usage Examples")
    print("="*60)
    
    # Check for credentials
    if not os.getenv('UHIN_USERNAME'):
        print("\n⚠️ Note: UHIN credentials not found in environment")
        print("Set them using:")
        print("  export UHIN_USERNAME='your_username'")
        print("  export UHIN_PASSWORD='your_password'")
        print("  export PROVIDER_NPI='your_npi'")
        print("\nOr create a .env file with these values")
        print("\nFor this demo, we'll just build X12 messages without sending them.")
        
        print("\n1. Building X12 270 Message...")
        build_x12_270_only()
        
    else:
        print("\nSelect an example to run:")
        print("1. Basic single patient check")
        print("2. Batch patient checking")
        print("3. Parse existing X12 271")
        print("4. Build X12 270 only")
        
        choice = input("\nEnter choice (1-4): ")
        
        if choice == '1':
            basic_example()
        elif choice == '2':
            batch_example()
        elif choice == '3':
            parse_existing_x12_271()
        elif choice == '4':
            build_x12_270_only()
        else:
            print("Invalid choice")