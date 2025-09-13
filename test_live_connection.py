#!/usr/bin/env python3
"""
Test Live Connection to UHIN
Tests the credentials and connection to UHIN's UTRANSEND clearinghouse
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load credentials from .env.local
load_dotenv('.env.local')

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import UHINEligibilityChecker


def test_production_connection():
    """Test connection to UHIN production environment"""
    
    print("\n" + "="*60)
    print("TESTING UHIN PRODUCTION CONNECTION")
    print("="*60)
    
    # Check credentials are loaded
    username = os.getenv('UHIN_USERNAME')
    password = os.getenv('UHIN_PASSWORD')
    endpoint = os.getenv('UHIN_ENDPOINT')
    tpn = os.getenv('UHIN_TRADING_PARTNER')
    
    print("\n📋 Configuration Check:")
    print(f"  Username: {'✅ Set' if username else '❌ Missing'} ({username if username else 'Not found'})")
    print(f"  Password: {'✅ Set' if password else '❌ Missing'} ({'*' * len(password) if password else 'Not found'})")
    print(f"  Endpoint: {endpoint}")
    print(f"  TPN: {tpn}")
    print(f"  Environment: {os.getenv('ENVIRONMENT', 'production')}")
    
    if not username or not password:
        print("\n❌ Missing credentials. Check .env.local file")
        return False
    
    # Create checker with production credentials
    config = {
        'username': username,
        'password': password,
        'endpoint': endpoint,
        'trading_partner': tpn,
        'receiver_id': 'HT000004-001',  # Production Utah Medicaid
        'provider_npi': os.getenv('PROVIDER_NPI', '1275348807'),
        'provider_name': os.getenv('PROVIDER_NAME', 'TEST_PROVIDER'),
        'provider_first': os.getenv('PROVIDER_FIRST_NAME', 'Rufus'),
        'provider_last': os.getenv('PROVIDER_LAST_NAME', 'Sweeney')
    }
    
    checker = UHINEligibilityChecker(config)
    
    # Test with Jeremy Montoya (known test patient)
    print("\n🔍 Testing with Jeremy Montoya (sample patient)...")
    print("   First Name: Jeremy")
    print("   Last Name: Montoya")
    print("   DOB: 1984-07-17")
    print("   Gender: M")
    print("   Member ID: 0900412827")
    
    result = checker.check_eligibility(
        first_name='Jeremy',
        last_name='Montoya',
        date_of_birth='1984-07-17',
        gender='M',
        member_id='0900412827',
        test_mode=False,  # Use production
        save_files=True
    )
    
    # Display results
    print("\n📊 Results:")
    print(f"  Success: {'✅ YES' if result['success'] else '❌ NO'}")
    
    if result['success']:
        print(f"  Qualified for CM: {'✅ YES' if result['qualified_for_cm'] else '❌ NO'}")
        print(f"  FFS Status: {result['ffs_status']}")
        
        details = result.get('eligibility_details', {})
        if details.get('summary'):
            print(f"  Summary: {details['summary']}")
    else:
        print(f"  Errors: {result.get('errors', 'Unknown error')}")
        if result.get('soap_fault'):
            print(f"  SOAP Fault: {result['soap_fault']}")
    
    if result.get('files'):
        print("\n📁 Files saved:")
        for file_type, path in result['files'].items():
            print(f"  - {file_type}: {path}")
    
    return result['success']


def test_uat_connection():
    """Test connection to UHIN UAT/Test environment"""
    
    print("\n" + "="*60)
    print("TESTING UHIN UAT CONNECTION")
    print("="*60)
    
    # Use UAT credentials
    config = {
        'username': 'MoonlitUAT',
        'password': 'tPKkfP@K5r2$cONG',
        'endpoint': 'https://uat-ws.uhin.org/webservices/core/soaptype4.asmx',
        'trading_partner': os.getenv('UHIN_TRADING_PARTNER', 'HT009582-001'),
        'receiver_id': 'HT000004-003',  # Test Utah Medicaid
        'provider_npi': os.getenv('PROVIDER_NPI', '1275348807'),
        'provider_name': 'TEST_PROVIDER',
        'provider_first': os.getenv('PROVIDER_FIRST_NAME', 'Rufus'),
        'provider_last': os.getenv('PROVIDER_LAST_NAME', 'Sweeney')
    }
    
    print("\n📋 UAT Configuration:")
    print(f"  Username: {config['username']}")
    print(f"  Endpoint: {config['endpoint']}")
    print(f"  Receiver ID: {config['receiver_id']} (Test environment)")
    
    checker = UHINEligibilityChecker(config)
    
    # Test with sample patient
    print("\n🔍 Testing UAT with test patient...")
    
    result = checker.check_eligibility(
        first_name='Test',
        last_name='Patient',
        date_of_birth='1990-01-01',
        gender='U',
        test_mode=True,  # Use test mode flag
        save_files=True
    )
    
    print("\n📊 UAT Results:")
    print(f"  Success: {'✅ YES' if result['success'] else '❌ NO'}")
    
    if not result['success']:
        print(f"  Response: {result.get('errors', 'Check output files for details')}")
    
    return result['success']


def main():
    """Main test runner"""
    
    print("\n🏥 UHIN LIVE CONNECTION TEST")
    print("="*60)
    
    print("\nThis will test your UHIN credentials against the live system.")
    print("Choose which environment to test:\n")
    print("1. Production Environment (MoonlitProd)")
    print("2. UAT/Test Environment (MoonlitUAT)")
    print("3. Test Both")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-3): ")
    
    if choice == '1':
        success = test_production_connection()
        if success:
            print("\n✅ Production connection test PASSED!")
        else:
            print("\n❌ Production connection test FAILED")
            print("   Check your credentials and network connection")
            
    elif choice == '2':
        success = test_uat_connection()
        if success:
            print("\n✅ UAT connection test PASSED!")
        else:
            print("\n❌ UAT connection test FAILED")
            print("   Note: UAT may have limited test data available")
            
    elif choice == '3':
        print("\n1️⃣ Testing Production...")
        prod_success = test_production_connection()
        
        print("\n2️⃣ Testing UAT...")
        uat_success = test_uat_connection()
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Production: {'✅ PASSED' if prod_success else '❌ FAILED'}")
        print(f"UAT: {'✅ PASSED' if uat_success else '❌ FAILED'}")
        
    else:
        print("Exiting...")
        return 0
    
    print("\n" + "="*60)
    print("For debugging, check the output/ directory for saved X12 messages")
    print("="*60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()