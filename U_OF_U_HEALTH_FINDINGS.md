# U of U Health Plans Eligibility Integration Findings

## Summary
Despite having the correct Trading Partner Number (HT000179-002) for U of U Health Plans, UHIN returns a "No Route Found" error for eligibility requests. This suggests U of U Health Plans may not support real-time eligibility through UHIN.

## What We Tried

### 1. Payer IDs Tested
- **SX155** (documented payer ID) ❌
- **HT000179-002** (Trading Partner Number) ❌
- Various alternatives (UUHP, UOFUH, HMHI, BHN) ❌

### 2. Configuration Used
```python
'U_OF_U_HEALTH': {
    'name': 'U of U Health Plans',
    'payer_id': 'SX155',
    'receiver_id': 'HT000179-002',  # Correct TPN from web Claude
    'payer_name': 'U OF U HEALTH PLANS'
}
```

### 3. X12 270 Message Format
Generated proper X12 270 messages with:
- Correct ISA/IEA envelope
- Proper receiver ID (HT000179-002)
- Valid patient demographics
- Multiple eligibility segments (30, 48, AL)

## Error Details

### UHIN Response
```
MessageCode: NRF
Message: No Route Found. Data transfer unsuccessful.
Trading partner may not support this type of transfer.
Contact trading partner.
```

## Possible Reasons

1. **No Real-Time Support**: U of U Health Plans may only support batch eligibility files, not real-time transactions
2. **Special Agreement Required**: May need a separate trading partner agreement with U of U Health Plans
3. **Different Channel**: They might use a direct connection rather than UHIN clearinghouse
4. **Portal Only**: Might only offer web portal access for eligibility

## Next Steps

### Option 1: Contact U of U Health Plans Directly
- Ask about EDI eligibility support
- Inquire about real-time vs batch processing
- Get technical contact for EDI setup

### Option 2: Contact UHIN
- Verify Trading Partner Number is correct
- Ask about U of U Health Plans eligibility routing
- Check if special setup is needed

### Option 3: Alternative Methods
- Check if U of U Health Plans has a web portal API
- Investigate batch file submission options
- Consider direct integration if available

## Working Payers

### ✅ Utah Medicaid FFS
- **TPN**: HT000004-001
- **Status**: Fully functional
- **Type**: Real-time eligibility

### ⏸️ Other Payers (Need TPNs)
- SelectHealth (SX062)
- Molina Healthcare (MOLNA)
- Anthem BCBS (SX107)

All show "No Route Found" - likely need correct Trading Partner Numbers from UHIN.

## Technical Implementation

The multi-payer system is ready and working:
- ✅ Flexible payer configuration (`payer_config.py`)
- ✅ Multi-payer X12 builder (`x12_builder_multi.py`)
- ✅ Multi-payer checker (`multi_payer_checker.py`)
- ✅ Test scripts for validation

Once we get confirmation on U of U Health Plans' eligibility support method, the system can be quickly configured to work with them.

## Contact Information Needed

To resolve this, we need:
1. U of U Health Plans EDI/IT department contact
2. UHIN payer relations contact
3. Current payer availability chart from UHIN

---

*Last Updated: 2025-10-03*
*Status: Awaiting payer confirmation on eligibility support method*