#!/usr/bin/env python3
"""Test with minimal X12 270"""

import os
from dotenv import load_dotenv
from x12_builder_minimal import MinimalX12_270Builder
from soap_client import SOAPClient
from parser import X12_271Parser

load_dotenv('.env.local')

# Build minimal X12 270
config = {
    'trading_partner': os.getenv('UHIN_TRADING_PARTNER', 'HT009582-001'),
    'receiver_id': 'HT000004-001',
    'username': os.getenv('UHIN_USERNAME'),
    'password': os.getenv('UHIN_PASSWORD'),
    'endpoint': os.getenv('UHIN_ENDPOINT')
}

builder = MinimalX12_270Builder(config)
x12_270 = builder.build(
    patient_first_name='Jeremy',
    patient_last_name='Montoya',
    patient_dob='1984-07-17',
    patient_gender='M',
    member_id='0900412827'
)

print("MINIMAL X12 270:")
print("="*60)
print(x12_270)
print("="*60)

# Send it
client = SOAPClient(config)
result = client.check_eligibility(x12_270)

if result['success']:
    print("\n✅ SUCCESS! Got X12 271 response")
    
    # Parse it
    parser = X12_271Parser()
    parsed = parser.parse(result['x12_271'])
    
    print(f"Eligible: {parsed.get('eligible')}")
    print(f"FFS Status: {parsed.get('ffs_status')}")
    print(f"Summary: {parsed.get('summary')}")
else:
    print(f"\n❌ FAILED: {result.get('error')}")
    if result.get('soap_fault'):
        print(f"SOAP Fault: {result['soap_fault']}")
    
    # Save for debugging
    if result.get('x12_271'):
        with open('output/minimal_test_response.txt', 'w') as f:
            f.write(result['x12_271'])
        print("Response saved to output/minimal_test_response.txt")