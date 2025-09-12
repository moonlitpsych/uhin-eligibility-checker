#!/usr/bin/env python3
"""Test Utah Medicaid specific format based on 999 error feedback"""

import os
from datetime import datetime
from dotenv import load_dotenv
from soap_client import SOAPClient
from parser import X12_271Parser

load_dotenv('.env.local')

def build_utah_medicaid_270():
    """Build X12 270 based on 999 error feedback"""
    
    control_number = str(int(datetime.now().timestamp()))[-9:]
    now = datetime.now()
    date_6 = now.strftime('%y%m%d')
    date_8 = now.strftime('%Y%m%d')
    time_4 = now.strftime('%H%M')
    
    segments = []
    
    # ISA
    segments.append(
        f"ISA*00*          *00*          *ZZ*HT009582-001   "
        f"*ZZ*HT000004-001   *{date_6}*{time_4}*^*00501*{control_number}*0*P*:~"
    )
    
    # GS
    segments.append(
        f"GS*HS*HT009582-001*HT000004-001*{date_8}*{time_4}*{control_number}*X*005010X279A1~"
    )
    
    # ST
    segments.append("ST*270*0001*005010X279A1~")
    
    # BHT
    segments.append(f"BHT*0022*13**{date_8}*{time_4}~")
    
    # HL - Payer
    segments.append("HL*1**20*1~")
    
    # NM1 - Payer
    segments.append("NM1*PR*2*UTAH MEDICAID FFS*****46*HT000004-001~")
    
    # HL - Provider
    segments.append("HL*2*1*21*1~")
    
    # NM1 - Provider (WITHOUT position 8 and 9 to avoid I12 error)
    segments.append("NM1*1P*1*MONTOYA*JEREMY***MD~")
    
    # HL - Subscriber
    segments.append("HL*3*2*22*0~")
    
    # TRN - First trace (with NPI and ELIGIBILITY)
    segments.append(f"TRN*1*{control_number[:8]}-{control_number[-6:]}*1275348807*ELIGIBILITY~")
    
    # TRN - Second trace (WITHOUT position 3 to avoid I5 error)
    segments.append(f"TRN*1*{control_number}{control_number[:3]}~")
    
    # NM1 - Subscriber
    segments.append("NM1*IL*1*MONTOYA*JEREMY****MI*0900412827~")
    
    # DMG
    segments.append("DMG*D8*19840717*M~")
    
    # DTP
    segments.append(f"DTP*291*RD8*{date_8}-{date_8}~")
    
    # EQ
    segments.append("EQ*30~")
    
    # SE
    segments.append("SE*14*0001~")
    
    # GE
    segments.append(f"GE*1*{control_number}~")
    
    # IEA
    segments.append(f"IEA*1*{control_number}~")
    
    return '\n'.join(segments)


# Build and send
x12_270 = build_utah_medicaid_270()

print("UTAH MEDICAID SPECIFIC X12 270:")
print("="*60)
print(x12_270)
print("="*60)

config = {
    'username': os.getenv('UHIN_USERNAME'),
    'password': os.getenv('UHIN_PASSWORD'),
    'endpoint': os.getenv('UHIN_ENDPOINT'),
    'trading_partner': 'HT009582-001',
    'receiver_id': 'HT000004-001'
}

client = SOAPClient(config)
result = client.check_eligibility(x12_270)

if result['success']:
    print("\n✅ SUCCESS! Got valid X12 271 response")
    
    parser = X12_271Parser()
    parsed = parser.parse(result['x12_271'])
    
    print(f"\nPatient: {parsed.get('patient_info', {}).get('first_name')} {parsed.get('patient_info', {}).get('last_name')}")
    print(f"Eligible: {parsed.get('eligible')}")
    print(f"FFS Status: {parsed.get('ffs_status')}")
    print(f"Summary: {parsed.get('summary')}")
    
    # Save successful response
    with open('output/successful_271_response.txt', 'w') as f:
        f.write(result['x12_271'])
    print("\n✅ Successful response saved to output/successful_271_response.txt")
else:
    print(f"\n❌ Failed: {result.get('error')}")
    if result.get('x12_271'):
        # Check if it's a 999
        if 'ST*999' in result['x12_271']:
            print("Got X12 999 error response - checking errors...")
            with open('output/latest_999_error.txt', 'w') as f:
                f.write(result['x12_271'])
            
            import subprocess
            subprocess.run(['python3', 'parse_999.py'])