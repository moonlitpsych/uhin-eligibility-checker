#!/usr/bin/env python3
"""
Test Script for UHIN Utah Medicaid Eligibility Checker
Demonstrates building X12 270, sending SOAP requests, and parsing X12 271 responses
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from getpass import getpass

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from main import UHINEligibilityChecker
from x12_builder import X12_270Builder
from parser import X12_271Parser


def test_x12_builder():
    """Test the X12 270 message builder"""
    print("\n" + "="*60)
    print("TESTING X12 270 MESSAGE BUILDER")
    print("="*60)
    
    config = {
        'trading_partner': 'HT009582-001',
        'receiver_id': 'HT000004-003',  # Test environment
        'provider_npi': '1275348807',
        'provider_name': 'MONTOYA',
        'provider_first_name': 'JEREMY'
    }
    
    builder = X12_270Builder(config)
    
    # Build a test message
    x12_270 = builder.build(
        patient_first_name='Jeremy',
        patient_last_name='Montoya',
        patient_dob='1984-07-17',
        patient_gender='M',
        member_id='0900412827',
        test_mode=True
    )
    
    print("\n📄 Generated X12 270 Message:")
    print("-" * 40)
    print(x12_270)
    print("-" * 40)
    
    # Validate the message
    validation = builder.validate(x12_270)
    print(f"\n✅ Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
    print(f"   Segment count: {validation['segment_count']}")
    if validation['errors']:
        print("   Errors:", validation['errors'])
    if validation['warnings']:
        print("   Warnings:", validation['warnings'])
    
    return x12_270


def test_x12_parser():
    """Test the X12 271 response parser with a sample response"""
    print("\n" + "="*60)
    print("TESTING X12 271 RESPONSE PARSER")
    print("="*60)
    
    # Sample X12 271 response (based on real Utah Medicaid response)
    sample_271 = """ISA*00*          *00*          *ZZ*HT000004-003   *ZZ*HT009582-001   *240912*1430*^*00501*123456789*0*P*:~
GS*HB*HT000004-003*HT009582-001*20240912*1430*123456789*X*005010X279A1~
ST*271*0001*005010X279A1~
BHT*0022*11**20240912*1430~
HL*1**20*1~
NM1*PR*2*UTAH MEDICAID*****PI*UTMCD~
HL*2*1*21*1~
NM1*1P*1*MONTOYA*JEREMY***MD*34*1275348807~
HL*3*2*22*0~
NM1*IL*1*MONTOYA*JEREMY****MI*0900412827~
EB*1*IND*30^1^45^47^48^50^54^60^86^88^98^AL^UC*MC*TARGETED ADULT MEDICAID~
SE*11*0001~
GE*1*123456789~
IEA*1*123456789~"""
    
    parser = X12_271Parser()
    result = parser.parse(sample_271)
    
    print("\n📋 Parsed Result:")
    print("-" * 40)
    print(f"Success: {result['success']}")
    print(f"Eligible: {result['eligible']}")
    print(f"FFS Status: {result['ffs_status']}")
    print(f"CM Qualification: {result['ffs_qualification']}")
    print(f"\nSummary: {result['summary']}")
    
    # Display formatted response
    print(parser.format_response(result))
    
    return result


def test_full_workflow():
    """Test the complete eligibility checking workflow"""
    print("\n" + "="*60)
    print("TESTING COMPLETE ELIGIBILITY WORKFLOW")
    print("="*60)
    
    # Check for credentials
    username = os.getenv('UHIN_USERNAME')
    password = os.getenv('UHIN_PASSWORD')
    provider_npi = os.getenv('PROVIDER_NPI')
    
    if not username or not password:
        print("\n⚠️  UHIN credentials not found in environment variables")
        print("   You can set them using:")
        print("   export UHIN_USERNAME='your_username'")
        print("   export UHIN_PASSWORD='your_password'")
        print("   export PROVIDER_NPI='your_npi'")
        
        use_manual = input("\nWould you like to enter credentials manually? (y/n): ")
        if use_manual.lower() == 'y':
            username = input("UHIN Username: ")
            password = getpass("UHIN Password: ")
            provider_npi = input("Provider NPI: ")
        else:
            print("\nSkipping live test. Running mock test instead...")
            return test_mock_workflow()
    
    # Create configuration
    config = {
        'username': username,
        'password': password,
        'provider_npi': provider_npi or '1275348807',
        'provider_name': 'TEST_PROVIDER'
    }
    
    # Create checker instance
    checker = UHINEligibilityChecker(config)
    
    # Test patient (Jeremy Montoya from the sample data)
    test_patient = {
        'first_name': 'Jeremy',
        'last_name': 'Montoya',
        'date_of_birth': '1984-07-17',
        'gender': 'M',
        'member_id': '0900412827'
    }
    
    print(f"\n🔍 Checking eligibility for: {test_patient['first_name']} {test_patient['last_name']}")
    print(f"   DOB: {test_patient['date_of_birth']}")
    print(f"   Member ID: {test_patient.get('member_id', 'Not provided')}")
    
    # Run eligibility check
    result = checker.check_eligibility(
        first_name=test_patient['first_name'],
        last_name=test_patient['last_name'],
        date_of_birth=test_patient['date_of_birth'],
        gender=test_patient['gender'],
        member_id=test_patient.get('member_id'),
        test_mode=True,  # Use test environment
        save_files=True
    )
    
    # Display result
    print(checker.format_result_summary(result))
    
    return result


def test_mock_workflow():
    """Test workflow with mock data (no actual SOAP calls)"""
    print("\n" + "="*60)
    print("MOCK ELIGIBILITY WORKFLOW (No Live Connection)")
    print("="*60)
    
    # Step 1: Build X12 270
    print("\n1️⃣ Building X12 270 Request...")
    x12_270 = test_x12_builder()
    
    # Step 2: Mock SOAP response
    print("\n2️⃣ Simulating SOAP Response...")
    print("   (In production, this would be sent to UHIN)")
    
    # Step 3: Parse X12 271
    print("\n3️⃣ Parsing X12 271 Response...")
    parsed_result = test_x12_parser()
    
    print("\n" + "="*60)
    print("MOCK TEST COMPLETE")
    print("="*60)
    
    return parsed_result


def test_batch_patients():
    """Test batch patient eligibility checking"""
    print("\n" + "="*60)
    print("TESTING BATCH PATIENT CHECKING")
    print("="*60)
    
    # Sample patients
    patients = [
        {
            'first_name': 'Jeremy',
            'last_name': 'Montoya',
            'date_of_birth': '1984-07-17',
            'gender': 'M',
            'member_id': '0900412827'
        },
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': 'M'
        },
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': '1985-05-15',
            'gender': 'F'
        }
    ]
    
    print(f"\n📋 Processing {len(patients)} patients...")
    
    # This would normally use real credentials
    checker = UHINEligibilityChecker()
    
    # Process each patient (mock mode)
    for i, patient in enumerate(patients, 1):
        print(f"\n{i}. {patient['first_name']} {patient['last_name']} (DOB: {patient['date_of_birth']})")
        print("   Status: Would check eligibility...")
        print("   Result: [Mock - requires credentials]")
    
    print("\n✅ Batch processing demonstration complete")


def main():
    """Main test runner"""
    print("\n" + "🏥 "*20)
    print("UHIN UTAH MEDICAID ELIGIBILITY CHECKER - TEST SUITE")
    print("🏥 "*20)
    
    while True:
        print("\nSelect a test to run:")
        print("1. Test X12 270 Message Builder")
        print("2. Test X12 271 Response Parser")
        print("3. Test Complete Workflow (requires credentials)")
        print("4. Test Mock Workflow (no credentials needed)")
        print("5. Test Batch Patient Processing (demonstration)")
        print("6. Run All Tests")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-6): ")
        
        if choice == '1':
            test_x12_builder()
        elif choice == '2':
            test_x12_parser()
        elif choice == '3':
            test_full_workflow()
        elif choice == '4':
            test_mock_workflow()
        elif choice == '5':
            test_batch_patients()
        elif choice == '6':
            print("\n🔄 Running all tests...")
            test_x12_builder()
            test_x12_parser()
            test_mock_workflow()
            test_batch_patients()
            print("\n✅ All tests complete!")
        elif choice == '0':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())