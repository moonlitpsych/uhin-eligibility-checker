# UHIN Eligibility Checker - CRITICAL INSTRUCTIONS FOR CLAUDE

## =¨ CRITICAL WARNING: THIS CODE IS WORKING! =¨

**DO NOT MODIFY THE FOLLOWING FILES UNLESS EXPLICITLY ASKED:**
- `x12_builder.py` - WORKING X12 270 builder (DO NOT TOUCH)
- `x12_builder_utah_medicaid.py` - WORKING Utah-specific builder (DO NOT TOUCH)
- `soap_client.py` - WORKING SOAP client for UHIN (DO NOT TOUCH)
- `main.py` - WORKING eligibility checker (DO NOT TOUCH)

These files successfully communicate with Utah Medicaid FFS via UHIN and receive valid 271 eligibility responses. They were fixed on 2025-09-12 after extensive debugging of 999 rejection errors.

## What This System Does

This is a **WORKING** Utah Medicaid eligibility checker that:
1. Takes patient information (name, DOB, Medicaid ID)
2. Builds properly formatted X12 270 eligibility inquiry messages
3. Sends them via SOAP to UHIN's CORE clearinghouse
4. Receives and parses X12 271 eligibility responses
5. Determines if patients qualify for Contingency Management programs (Traditional FFS only)

## The Critical X12 Format (DO NOT CHANGE)

The X12 270 format that works with Utah Medicaid has these EXACT requirements:

```
NM1*1P*1*{PROVIDER_LAST}*{PROVIDER_FIRST}****XX*{PROVIDER_NPI}~
TRN*1*{unique_trace}*{PROVIDER_NPI}~
```

**Critical elements that MUST NOT change:**
- Provider NM1 uses `XX` qualifier (NOT `MD*34`)
- Only ONE TRN segment (not two)
- TRN03 MUST be exactly 10 characters (provider NPI works)
- SE segment count MUST be 13

## Environment Configuration

The system uses credentials from `.env.local`:
```
UHIN_USERNAME=MoonlitProd
UHIN_PASSWORD=3shz8trtYF2M06!N
UHIN_ENDPOINT=https://ws.uhin.org/webservices/core/soaptype4.asmx
UHIN_TRADING_PARTNER=HT009582-001
UHIN_RECEIVER_ID=HT000004-001
PROVIDER_NPI=1275348807
PROVIDER_FIRST_NAME=Rufus
PROVIDER_LAST_NAME=Sweeney
```

## How to Test (Without Breaking)

To verify the system is still working:
```bash
python test_live_connection.py
# Choose option 1 for Production test
```

Expected result: You should receive a 271 response (not a 999 rejection).

## Common Tasks

### Check eligibility for a patient:
```python
from main import UHINEligibilityChecker

config = {
    'username': 'MoonlitProd',
    'password': '...',
    'endpoint': 'https://ws.uhin.org/webservices/core/soaptype4.asmx',
    'trading_partner': 'HT009582-001',
    'receiver_id': 'HT000004-001',
    'provider_npi': '1275348807',
    'provider_first': 'Rufus',
    'provider_last': 'Sweeney'
}

checker = UHINEligibilityChecker(config)
result = checker.check_eligibility(
    first_name='Jeremy',
    last_name='Montoya',
    date_of_birth='1984-07-17',
    gender='M',
    member_id='0900412827'
)
```

### Understanding the Response:
- `qualified_for_cm: True` = Traditional FFS Medicaid (eligible for CM)
- `qualified_for_cm: False` = Managed Care or other (not eligible)
- `ffs_status` = "TRADITIONAL_FFS" or "MANAGED_CARE"

## What NOT to Do

1. **DO NOT** change the X12 segment format
2. **DO NOT** add or remove TRN segments
3. **DO NOT** change provider NM1 qualifiers
4. **DO NOT** modify TRN03 length or content
5. **DO NOT** update SE segment counts without recounting
6. **DO NOT** assume Office Ally format works here (it doesn't)

## If You Must Make Changes

If changes are absolutely necessary:
1. Read `X12_FIX_JOURNEY.md` first to understand the history
2. Make a backup of working files
3. Test with `test_live_connection.py` after EVERY change
4. Watch for 999 rejections - they mean format errors
5. Check IK3/IK4 segments in 999 responses for specific error locations

## Success Indicators

 You're getting 271 responses (not 999)
 The response contains eligibility benefit information
 The system correctly identifies FFS vs Managed Care
 No SOAP faults or HTTP 500 errors

## Project Context

This eligibility checker is part of a larger Contingency Management billing system for Utah Medicaid. It needs to:
- Verify patients have Traditional FFS Medicaid (not Managed Care)
- Support real-time eligibility checks during patient intake
- Feed eligibility data to the billing system for H0038 claims

## Files You CAN Modify

- Test files (`test_*.py`) - for testing new scenarios
- Documentation files (`*.md`) - except this one
- Output files in `output/` directory - these are temporary

## Contact for Issues

If the X12 format stops working:
1. Check if Utah Medicaid changed their requirements
2. Review the 999 rejection details (IK3/IK4 segments)
3. Refer to `X12_FIX_JOURNEY.md` for debugging approach
4. Test changes incrementally with production endpoint

---

**REMEMBER: This code is WORKING as of 2025-09-12. Don't fix what isn't broken!**