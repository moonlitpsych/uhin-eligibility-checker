#!/usr/bin/env python3
"""
Test script for U of U Health Plans eligibility checking
Tries different payer ID variations to find the correct routing
"""

from multi_payer_checker import MultiPayerEligibilityChecker
from payer_config import PayerConfig
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_patient():
    """Test patient information"""
    return {
        'first_name': 'Jeremy',
        'last_name': 'Montoya',
        'date_of_birth': '1984-07-17',
        'gender': 'M'
    }

def test_uofu_variations():
    """Test different U of U Health Plans payer ID variations"""

    # Possible variations based on common patterns
    uofu_variations = [
        ('SX155', 'U of U Health Plans - Standard ID'),
        ('UUHP', 'U of U Health Plans - Abbreviation'),
        ('UOFUH', 'University of Utah Health - Alternative'),
        ('HMHI', 'HMHI - BHN Network'),
        ('BHN', 'Behavioral Health Network'),
        ('HT000155', 'UHIN Format - HT Prefix'),
    ]

    checker = MultiPayerEligibilityChecker()
    patient = test_patient()

    print("\n" + "="*70)
    print("Testing U of U Health Plans Payer ID Variations")
    print("="*70)

    # First, verify Utah Medicaid still works
    print("\n✓ Baseline Test: Utah Medicaid FFS")
    result = checker.check_eligibility(
        payer_key='UTAH_MEDICAID',
        **patient
    )

    if result.get('success'):
        print(f"  SUCCESS: Got response for {result.get('patient_info', {}).get('first_name')} {result.get('patient_info', {}).get('last_name')}")
    else:
        print(f"  FAILED: {result.get('error', 'Unknown error')}")

    # Now test U of U Health Plans variations
    print("\n✗ Testing U of U Health Plans Variations:")

    for payer_id, description in uofu_variations:
        print(f"\n  Testing: {payer_id} ({description})")

        # Temporarily update the payer config
        PayerConfig.PAYERS['U_OF_U_HEALTH_TEST'] = {
            'name': f'U of U Health Plans Test - {payer_id}',
            'payer_id': payer_id,
            'payer_name': 'U OF U HEALTH PLANS',
            'payer_code': payer_id,
            'receiver_id': payer_id,
            'description': description,
            'eligibility_segments': ['30', '48'],
            'supported_services': ['medical', 'behavioral_health'],
            'identifier_type': 'MI',
            'requires_member_id': False,  # Try without member ID first
            'test_receiver_id': None
        }

        result = checker.check_eligibility(
            payer_key='U_OF_U_HEALTH_TEST',
            **patient
        )

        if result.get('success'):
            print(f"    ✓ SUCCESS! Got valid response")
            if result.get('patient_info'):
                print(f"      Patient: {result['patient_info']}")
            if result.get('interpretation'):
                print(f"      Coverage: {result['interpretation']['coverage_type']}")
                print(f"      Eligible: {result['interpretation']['is_eligible']}")
            break  # Found working ID!
        else:
            error = result.get('error', 'Unknown error')
            if 'No Route Found' in error:
                print(f"    ✗ No route to payer ID {payer_id}")
            elif 'Invalid' in error:
                print(f"    ✗ Invalid payer ID format")
            else:
                print(f"    ✗ Error: {error[:100]}...")

    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)

def check_other_local_payers():
    """Test other common Utah payers"""

    payers_to_test = [
        'SELECTHEALTH',
        'MOLINA',
        'ANTHEM_BCBS'
    ]

    checker = MultiPayerEligibilityChecker()
    patient = test_patient()

    print("\n" + "="*70)
    print("Testing Other Local Payers")
    print("="*70)

    for payer_key in payers_to_test:
        payer = PayerConfig.get_payer(payer_key)
        print(f"\n• {payer['name']} (ID: {payer['payer_id']})")

        result = checker.check_eligibility(
            payer_key=payer_key,
            **patient
        )

        if result.get('success'):
            print(f"  ✓ SUCCESS: Got response")
            interp = result.get('interpretation', {})
            print(f"    Coverage: {interp.get('coverage_type', 'Unknown')}")
            print(f"    Eligible: {interp.get('is_eligible', False)}")
        else:
            error = result.get('error', 'Unknown error')
            if 'No Route Found' in error:
                print(f"  ✗ No route to payer")
            else:
                print(f"  ✗ Error: {error[:100] if len(error) > 100 else error}")

    print("\n" + "="*70)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        # Test all payers
        test_uofu_variations()
        check_other_local_payers()
    else:
        # Just test U of U Health Plans
        test_uofu_variations()
        print("\nRun with --all to test other local payers too")