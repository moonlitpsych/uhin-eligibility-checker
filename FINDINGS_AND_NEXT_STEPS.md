# Utah Medicaid X12 270/271 Integration - Findings and Next Steps

## Current Status: Blocked by X12 999 Errors

Despite implementing web Claude's recommendations for minimal X12 270 format, Utah Medicaid continues to reject our eligibility inquiries with X12 999 functional acknowledgment errors.

## What We've Learned

### 1. The Core Issue
Utah Medicaid has implemented the X12 270 standard with many elements marked as "Not Used" that are typically included in standard implementations. This is more restrictive than even web Claude's analysis suggested.

### 2. Persistent Error Pattern
No matter what format we try, we consistently get:
- **NM1 Provider Segment**: Errors on positions 8-9 (even when omitted)
- **TRN Segment**: Errors on position 3 (even with minimal format)

### 3. Formats Tested

#### Standard Format (from UHIN guide)
```
NM1*1P*1*MONTOYA*JEREMY***MD*34*1275348807~
TRN*1*00702156-185943*1275348807*ELIGIBILITY~
TRN*1*1756400702156380*HT009582-001*REALTIME~
```
**Result**: ❌ X12 999 errors

#### Minimal Format (web Claude recommendation)
```
NM1*1P*1*MONTOYA*JEREMY~
TRN*1*75771996719968~
```
**Result**: ❌ Still X12 999 errors

#### Ultra Minimal Format
```
NM1*1P*2*PROVIDER~
[No TRN segment]
```
**Result**: ❌ Still errors

## Root Cause Hypothesis

### Most Likely Scenario
Utah Medicaid has a **payer-specific companion guide** with unique requirements that:
1. Differ from UHIN's generic examples
2. Are not documented in the publicly available UTRANSEND manual
3. May require special enrollment or configuration for our Trading Partner Number

### Alternative Possibilities
1. **Provider Enrollment Issue**: Our provider (NPI: 1275348807) may need special configuration with Utah Medicaid
2. **Wrong Endpoint**: Utah Medicaid might use a different endpoint or receiver ID than documented
3. **Version Mismatch**: They may be using a different version of the X12 standard

## Recommended Next Steps

### 1. Contact UHIN Support Immediately
Provide them with:
- Our Trading Partner Number: HT009582-001
- The specific X12 999 errors we're receiving
- Request for **Utah Medicaid's specific companion guide**
- Ask for a **working X12 270 example** that successfully queries Utah Medicaid

### 2. Questions to Ask UHIN

1. **Does Utah Medicaid have a separate companion guide?**
   - If yes, request a copy
   - If no, why are we getting errors on standard format?

2. **Is our Trading Partner properly enrolled for Utah Medicaid?**
   - Do we need additional configuration?
   - Are there payer-specific settings needed?

3. **Can you provide a recent successful X12 270 for Utah Medicaid?**
   - Sanitized for patient privacy
   - Shows the exact format they accept

4. **Are we using the correct receiver ID?**
   - HT000004-001 for production
   - Is this correct for Utah Medicaid FFS?

5. **Is there a test environment we should use first?**
   - Different credentials needed?
   - Different validation rules?

### 3. Temporary Workaround Options

While waiting for UHIN support:

1. **Try Other Payers**: Test with commercial payers to verify our system works
2. **Manual Verification**: Use Utah Medicaid's web portal for urgent eligibility checks
3. **Partner Integration**: Consider if Office Ally or another clearinghouse has working Utah Medicaid integration

## Technical Implementation Status

### ✅ Completed Components
- SOAP client with WS-Security authentication
- X12 270 builder (multiple format variations)
- X12 271 response parser
- X12 999 error parser
- Comprehensive testing framework

### ⏸️ Blocked Component
- Utah Medicaid-specific X12 270 format

### 📝 Code Quality
The codebase is modular and well-structured. Once we get the correct format from UHIN, we only need to update the `x12_builder_utah_medicaid.py` file.

## Files for UHIN Support

When contacting UHIN, reference these files in the GitHub repository:
1. `IMPLEMENTATION_SUMMARY.md` - Complete history of attempts
2. `test_utah_medicaid_minimal.py` - Shows exact formats we've tried
3. `parse_999.py` - Demonstrates how we're parsing their error responses

## Bottom Line

**We cannot proceed without Utah Medicaid's specific implementation requirements.**

The system is fully functional and ready - we just need the correct X12 270 format that Utah Medicaid will accept. This information can only come from UHIN support or Utah Medicaid directly.

## Contact Information

UHIN Support:
- Phone: 801-716-5901
- Email: support@uhin.org
- Hours: Monday-Friday 7:00 AM - 6:00 PM MT

When calling, reference:
- Trading Partner: HT009582-001 (Moonlit)
- Issue: X12 999 errors on Utah Medicaid eligibility (270/271)
- Request: Utah Medicaid companion guide and working example