# PROTECTED FILES - DO NOT MODIFY

## Core Working Files (DO NOT TOUCH)

These files contain the exact X12 format that Utah Medicaid accepts. Any modification could break the integration:

1. **`x12_builder.py`**
   - Contains the working X12 270 builder
   - Critical elements: NM1 with XX qualifier, single TRN with 10-char originator
   
2. **`x12_builder_utah_medicaid.py`**
   - Utah-specific variant with same critical fixes
   
3. **`soap_client.py`**
   - SOAP client configured for UHIN's CORE clearinghouse
   - Uses correct namespaces and WS-Security headers
   
4. **`main.py`**
   - Main eligibility checker orchestration
   - Correctly identifies Traditional FFS vs Managed Care

## Configuration Files

5. **`.env.local`**
   - Contains production credentials (DO NOT COMMIT)
   - Has working provider information

## Safe to Modify

- `test_live_connection.py` - For testing new scenarios
- `example_usage.py` - For demonstration purposes
- `parser.py` - For enhancing 271 parsing if needed
- Output files in `output/` directory

## Testing Before Any Changes

If you absolutely must modify protected files:

1. Run this first to confirm it's working:
```bash
python test_live_connection.py
# Choose option 1 (Production)
# Should get 271 response, not 999
```

2. Make your change

3. Run the test again immediately

4. If you get a 999 rejection, REVERT YOUR CHANGE

## Why These Files Are Protected

On 2025-09-12, after extensive debugging, we discovered Utah Medicaid has very specific X12 requirements:
- Provider NM1 must use XX qualifier (not MD)
- Only one TRN segment allowed
- TRN03 must be exactly 10 characters
- Segment counts must be exact

The current format in these files passes all Utah Medicaid validations and receives proper 271 responses.

## Emergency Recovery

If someone breaks these files, the last known working commit is:
```
git log --oneline | grep "fix"
```

Look for commits mentioning "X12 format fixes" or "999 rejection resolved"