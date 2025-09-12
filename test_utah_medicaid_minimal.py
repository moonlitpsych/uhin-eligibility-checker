#!/usr/bin/env python3
"""
Test Utah Medicaid with minimal X12 270 format based on web Claude's analysis
"""

import os
import sys
from dotenv import load_dotenv
from x12_builder_utah_medicaid import UtahMedicaidX12_270Builder
from soap_client import SOAPClient
from parser import X12_271Parser

load_dotenv('.env.local')

def test_minimal_format():
    """Test the minimal format recommended by web Claude"""
    
    print("\n" + "="*60)
    print("TESTING UTAH MEDICAID MINIMAL FORMAT")
    print("Based on web Claude's analysis of UTRANSEND requirements")
    print("="*60)
    
    config = {
        'trading_partner': os.getenv('UHIN_TRADING_PARTNER', 'HT009582-001'),
        'receiver_id': 'HT000004-001',  # Production Utah Medicaid
        'username': os.getenv('UHIN_USERNAME'),
        'password': os.getenv('UHIN_PASSWORD'),
        'endpoint': os.getenv('UHIN_ENDPOINT')
    }
    
    builder = UtahMedicaidX12_270Builder(config)
    
    # Build minimal X12 270
    x12_270 = builder.build(
        patient_first_name='Jeremy',
        patient_last_name='Montoya',
        patient_dob='1984-07-17',
        patient_gender='M',
        member_id='0900412827',
        provider_first_name='JEREMY',
        provider_last_name='MONTOYA'
    )
    
    print("\n📄 MINIMAL X12 270 (Provider without NPI, single TRN without qualifiers):")
    print("-" * 60)
    for i, line in enumerate(x12_270.split('\n'), 1):
        if line.startswith('NM1*1P'):
            print(f"{i:2}. {line} ← MINIMAL PROVIDER (no pos 7-9)")
        elif line.startswith('TRN'):
            print(f"{i:2}. {line} ← MINIMAL TRN (only type & number)")
        elif line.startswith('SE'):
            print(f"{i:2}. {line} ← 12 segments total")
        else:
            print(f"{i:2}. {line}")
    print("-" * 60)
    
    # Send request
    print("\n📡 Sending to Utah Medicaid...")
    client = SOAPClient(config)
    result = client.check_eligibility(x12_270)
    
    if result['success'] and result.get('x12_271'):
        # Check if it's a 999 error or valid 271
        if 'ST*999' in result['x12_271']:
            print("\n❌ Still got X12 999 error")
            print("Parsing errors...")
            
            # Save and parse
            with open('output/minimal_999_response.txt', 'w') as f:
                f.write(result['x12_271'])
            
            # Parse 999
            import subprocess
            subprocess.run(['python3', 'parse_999.py'])
            
            return False
        else:
            print("\n✅ SUCCESS! Got valid X12 271 response!")
            
            # Parse response
            parser = X12_271Parser()
            parsed = parser.parse(result['x12_271'])
            
            print("\n📊 ELIGIBILITY RESULTS:")
            print(f"  Patient: {parsed.get('patient_info', {}).get('first_name')} {parsed.get('patient_info', {}).get('last_name')}")
            print(f"  Eligible: {parsed.get('eligible')}")
            print(f"  FFS Status: {parsed.get('ffs_status')}")
            print(f"  CM Qualification: {parsed.get('ffs_qualification')}")
            print(f"  Summary: {parsed.get('summary')}")
            
            # Save successful response
            with open('output/SUCCESSFUL_271_RESPONSE.txt', 'w') as f:
                f.write(result['x12_271'])
            print("\n✅ SUCCESSFUL RESPONSE SAVED TO output/SUCCESSFUL_271_RESPONSE.txt")
            
            # Also save the working X12 270 format
            with open('output/WORKING_X12_270_FORMAT.txt', 'w') as f:
                f.write(x12_270)
            print("✅ WORKING X12 270 FORMAT SAVED TO output/WORKING_X12_270_FORMAT.txt")
            
            return True
    else:
        print(f"\n❌ Request failed: {result.get('error')}")
        return False


def test_ultra_minimal():
    """Test ultra minimal format if standard minimal fails"""
    
    print("\n" + "="*60)
    print("TESTING ULTRA MINIMAL FORMAT (No TRN, Provider as Org)")
    print("="*60)
    
    config = {
        'trading_partner': os.getenv('UHIN_TRADING_PARTNER', 'HT009582-001'),
        'receiver_id': 'HT000004-001',
        'username': os.getenv('UHIN_USERNAME'),
        'password': os.getenv('UHIN_PASSWORD'),
        'endpoint': os.getenv('UHIN_ENDPOINT')
    }
    
    builder = UtahMedicaidX12_270Builder(config)
    
    # Build ultra minimal
    x12_270 = builder.build_ultra_minimal(
        patient_first_name='Jeremy',
        patient_last_name='Montoya',
        patient_dob='1984-07-17',
        patient_gender='M',
        member_id='0900412827'
    )
    
    print("\n📄 ULTRA MINIMAL X12 270:")
    print("-" * 60)
    for i, line in enumerate(x12_270.split('\n'), 1):
        if line.startswith('NM1*1P'):
            print(f"{i:2}. {line} ← PROVIDER AS ORG")
        elif 'TRN' in line:
            print(f"{i:2}. {line}")
        elif line.startswith('SE'):
            print(f"{i:2}. {line} ← 11 segments (no TRN)")
        else:
            print(f"{i:2}. {line}")
    print("-" * 60)
    
    # Send request
    print("\n📡 Sending ultra minimal to Utah Medicaid...")
    client = SOAPClient(config)
    result = client.check_eligibility(x12_270)
    
    if result['success'] and result.get('x12_271'):
        if 'ST*999' not in result['x12_271']:
            print("\n✅ ULTRA MINIMAL FORMAT WORKED!")
            
            # Parse and display
            parser = X12_271Parser()
            parsed = parser.parse(result['x12_271'])
            print(f"  Summary: {parsed.get('summary')}")
            
            # Save
            with open('output/ULTRA_MINIMAL_SUCCESS.txt', 'w') as f:
                f.write(result['x12_271'])
            with open('output/ULTRA_MINIMAL_X12_270.txt', 'w') as f:
                f.write(x12_270)
                
            return True
    
    print("\n❌ Ultra minimal also failed")
    return False


def main():
    """Run progressive testing"""
    
    print("\n🏥 UTAH MEDICAID MINIMAL FORMAT TESTING")
    print("Based on web Claude's analysis of UTRANSEND requirements")
    print("="*60)
    
    # Check credentials
    if not os.getenv('UHIN_USERNAME'):
        print("\n❌ Missing credentials in .env.local")
        return 1
    
    print("\n1️⃣ Testing minimal format (no NPI, minimal TRN)...")
    if test_minimal_format():
        print("\n🎉 SUCCESS! Minimal format works!")
        print("Use the UtahMedicaidX12_270Builder class for Utah Medicaid")
        return 0
    
    print("\n2️⃣ Minimal format failed. Trying ultra minimal...")
    if test_ultra_minimal():
        print("\n🎉 SUCCESS! Ultra minimal format works!")
        print("Use build_ultra_minimal() method for Utah Medicaid")
        return 0
    
    print("\n❌ Both formats failed. Need to contact UHIN support for clarification.")
    print("\nNext steps:")
    print("1. Share the X12 999 errors with UHIN support")
    print("2. Request Utah Medicaid's specific companion guide")
    print("3. Ask for a working X12 270 example for Utah Medicaid FFS")
    
    return 1


if __name__ == '__main__':
    sys.exit(main())