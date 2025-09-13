# UHIN Eligibility Checker for Utah Medicaid

## ✅ Status: WORKING as of 2025-09-12

This system successfully checks Utah Medicaid eligibility via UHIN's CORE clearinghouse and correctly identifies Traditional FFS vs Managed Care enrollment.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env.local` with your credentials (see `.env.local` for current working config)

### 3. Test Connection
```bash
python test_live_connection.py
# Choose option 1 for Production
```

### 4. Check Patient Eligibility
```python
from main import UHINEligibilityChecker
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

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

checker = UHINEligibilityChecker(config)

# Check eligibility
result = checker.check_eligibility(
    first_name='Jeremy',
    last_name='Montoya',
    date_of_birth='1984-07-17',
    gender='M',
    member_id='0900412827'
)

if result['success']:
    print(f"Qualified for CM: {result['qualified_for_cm']}")
    print(f"Plan Type: {result['ffs_status']}")
```

## Key Features

- ✅ Real-time eligibility verification
- ✅ Correctly formatted X12 270 messages for Utah Medicaid
- ✅ SOAP integration with UHIN CORE clearinghouse
- ✅ Parses X12 271 responses
- ✅ Identifies Traditional FFS vs Managed Care
- ✅ Determines CM program eligibility

## Response Interpretation

- **Traditional FFS** → Qualifies for Contingency Management
- **Managed Care** (Molina, SelectHealth, Anthem, etc.) → Does NOT qualify
- **Not Enrolled** → Not eligible for Medicaid

## Important Files

### Working Code (DO NOT MODIFY)
- `x12_builder.py` - X12 270 message builder
- `soap_client.py` - UHIN SOAP client
- `main.py` - Main eligibility checker
- `parser.py` - X12 271 response parser

### Documentation
- `CLAUDE.md` - Critical instructions for AI assistants
- `X12_FIX_JOURNEY.md` - How we solved the 999 rejections
- `PROTECTED_FILES.md` - List of files that must not be changed

### Testing
- `test_live_connection.py` - Live connection tester
- `example_usage.py` - Usage examples

## Troubleshooting

### Getting 999 Rejections?
1. DO NOT modify the X12 builders
2. Check `X12_FIX_JOURNEY.md` for the solution history
3. Verify credentials in `.env.local`
4. Ensure provider NPI is valid

### Getting 500 Errors?
1. Check if UAT environment is down (use Production)
2. Verify endpoint URL is correct
3. Check network connectivity

### Getting False Negatives?
1. Patient might be in Managed Care (check `ffs_status`)
2. Medicaid ID might be incorrect
3. Patient might not be enrolled

## Output Files

The system saves debugging information to `output/`:
- `x12_270_*.txt` - Sent eligibility inquiry
- `x12_271_*.txt` - Received eligibility response
- `parsed_result_*.json` - Parsed eligibility data

## Integration with CM Billing System

This eligibility checker is designed to integrate with the larger Contingency Management billing system. It provides:
1. Real-time eligibility verification during patient intake
2. FFS vs Managed Care determination
3. Qualification status for CM program enrollment

## Support

For issues with the X12 format or UHIN integration, refer to:
1. `CLAUDE.md` for AI assistant instructions
2. `X12_FIX_JOURNEY.md` for debugging approach
3. UHIN support for clearinghouse issues

---

**Remember:** This code is working. Don't fix what isn't broken!