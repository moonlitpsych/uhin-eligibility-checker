#!/usr/bin/env python3
"""
Detailed test for U of U Health Plans eligibility checking
Shows full error messages and X12 details
"""

from multi_payer_checker import MultiPayerEligibilityChecker
from soap_client import SOAPClient
import logging
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_soap_fault(error_text):
    """Extract SOAP fault details from error response"""
    try:
        # Parse the XML
        root = ET.fromstring(error_text)

        # Find the fault text
        namespaces = {
            'soapenv': 'http://www.w3.org/2003/05/soap-envelope/',
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/'
        }

        # Try SOAP 1.2 first
        fault_text = root.find('.//soapenv:Text', namespaces)
        if fault_text is not None:
            return fault_text.text

        # Try SOAP 1.1
        fault_string = root.find('.//faultstring')
        if fault_string is not None:
            return fault_string.text

        return None
    except:
        return None

def test_uofu_detailed():
    """Test U of U Health Plans with detailed error reporting"""

    checker = MultiPayerEligibilityChecker()

    print("\n" + "="*70)
    print("U of U Health Plans Detailed Test (TPN: HT000179-002)")
    print("="*70)

    # Test patient info
    patient = {
        'first_name': 'Jeremy',
        'last_name': 'Montoya',
        'date_of_birth': '1984-07-17',
        'gender': 'M'
    }

    # First verify Utah Medicaid works
    print("\n1. Baseline Test: Utah Medicaid")
    print("-" * 40)

    result = checker.check_eligibility(
        payer_key='UTAH_MEDICAID',
        **patient
    )

    if result.get('success'):
        print("✅ Utah Medicaid: Working")
        if result.get('patient_info'):
            print(f"   Patient: {result['patient_info'].get('first_name')} {result['patient_info'].get('last_name')}")
            print(f"   Member ID: {result['patient_info'].get('member_id', 'N/A')}")
    else:
        print(f"❌ Utah Medicaid: {result.get('error', 'Unknown error')[:100]}")

    # Now test U of U Health Plans
    print("\n2. U of U Health Plans Test")
    print("-" * 40)

    result = checker.check_eligibility(
        payer_key='U_OF_U_HEALTH',
        **patient
    )

    if result.get('success'):
        print("✅ U of U Health Plans: SUCCESS!")
        if result.get('patient_info'):
            print(f"   Patient: {result['patient_info']}")
        if result.get('interpretation'):
            print(f"   Coverage: {result['interpretation']}")
    else:
        error = result.get('error', 'Unknown error')

        # Extract detailed error
        fault_msg = extract_soap_fault(error)

        if fault_msg:
            print(f"❌ U of U Health Plans SOAP Fault:")
            print(f"   {fault_msg}")

            # Parse specific error codes
            if "No Route Found" in fault_msg:
                print("\n   Issue: UHIN cannot route to this payer")
                print("   Possible causes:")
                print("   - Trading Partner Number might be incorrect")
                print("   - Payer might not accept real-time eligibility")
                print("   - Trading partner agreement might be needed")
            elif "Invalid" in fault_msg:
                print("\n   Issue: Message format problem")
                print("   Check X12 message format in output directory")
            elif "Member not found" in fault_msg:
                print("\n   Issue: Patient not found in U of U Health Plans")
                print("   This is expected - Jeremy Montoya has Utah Medicaid")
        else:
            print(f"❌ U of U Health Plans: {error[:200]}")

    # Test with a member ID (hypothetical)
    print("\n3. U of U Health Plans Test with Member ID")
    print("-" * 40)
    print("   (Using hypothetical member ID)")

    result = checker.check_eligibility(
        payer_key='U_OF_U_HEALTH',
        first_name='Test',
        last_name='Patient',
        date_of_birth='1990-01-01',
        gender='M',
        member_id='UU123456789'  # Hypothetical member ID
    )

    if result.get('success'):
        print("✅ U of U Health Plans: SUCCESS with Member ID!")
        if result.get('patient_info'):
            print(f"   Patient: {result['patient_info']}")
    else:
        error = result.get('error', 'Unknown error')
        fault_msg = extract_soap_fault(error)

        if fault_msg:
            print(f"❌ With Member ID SOAP Fault:")
            print(f"   {fault_msg}")
        else:
            print(f"❌ With Member ID: {error[:200]}")

    print("\n" + "="*70)
    print("Test Complete")
    print("\nX12 messages saved to: output/x12_270_U_OF_U_HEALTH_*.txt")
    print("="*70)

if __name__ == "__main__":
    test_uofu_detailed()