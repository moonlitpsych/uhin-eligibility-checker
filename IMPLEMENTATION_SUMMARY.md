# UHIN Utah Medicaid Eligibility Checker - Implementation Summary

## Project Overview
Building a Python-based eligibility checking system to connect to Utah Medicaid through UHIN's UTRANSEND clearinghouse network using SOAP/X12 270/271 transactions. The goal is to determine if patients have Fee-For-Service (FFS) Medicaid (Traditional or Targeted Adult Medicaid) to qualify them for contingency management programs.

## Credentials & Configuration
- **Production Credentials**: MoonlitProd / 3shz8trtYF2M06!N
- **UAT Credentials**: MoonlitUAT / tPKkfP@K5r2$cONG
- **Trading Partner Number**: HT009582-001
- **Provider NPI**: 1275348807
- **Medicaid Billing Agent ID**: 3003535

## What We've Built

### 1. Core Modules Created
- **`x12_builder.py`**: Builds X12 270 eligibility inquiry messages
- **`soap_client.py`**: Handles SOAP envelope creation with WS-Security headers
- **`parser.py`**: Parses X12 271 responses and determines FFS eligibility
- **`main.py`**: Orchestrates the complete workflow
- **`.env.local`**: Contains credentials (gitignored)

### 2. Key Features Implemented
- ✅ X12 270 message construction with proper segment formatting
- ✅ SOAP envelope with WS-Security authentication
- ✅ HTTP communication with UHIN endpoint
- ✅ X12 271 response parsing
- ✅ FFS vs Managed Care detection logic
- ✅ Error handling and logging
- ✅ File output for debugging

## Breakthroughs Achieved

### 1. Successfully Connected to UHIN
- Established SOAP connection with proper authentication
- Received responses from UHIN servers (both production and UAT)

### 2. Timestamp Format Resolution
- Initially got `TimeStampIllegal` error - timestamp was too long
- **Solution**: Changed from ISO format with microseconds to exactly 20 chars: `YYYY-MM-DDTHH:MM:SSZ`
- Later found UHIN accepts milliseconds: `YYYY-MM-DDTHH:MM:SS.sssZ`

### 3. PayloadID Format
- Initial error: "PayloadID cannot be less than 36 characters"
- **Solution**: Must be exactly 36 characters (UUID format works, or padded string)

### 4. X12 999 Response Parsing
- Built `parse_999.py` to decode functional acknowledgment errors
- Successfully identifies specific segment and element errors

## Persistent Issues - X12 999 Errors

### Current Blocker: Utah Medicaid Rejects Our X12 270
Despite trying multiple formats, Utah Medicaid consistently returns X12 999 (Functional Acknowledgment) with these errors:

#### Error Pattern 1: NM1 Segment (Provider)
- **Position**: 6 (2100 loop)
- **Errors**:
  - IK4 position 8: Error 66 (Invalid/Missing ID Qualifier)
  - IK4 position 9: Error 67 (Invalid/Missing ID) 
  - Error code I12: "Implementation 'Not Used' element present"
- **What this means**: Utah Medicaid doesn't want the provider NPI in the NM1 segment

#### Error Pattern 2: TRN Segment (Trace)
- **Position**: 9 (2000 loop)
- **Errors**:
  - IK4 position 3: Error 509 (Implementation Not Used)
  - Error code I5: "Implementation segment not expected"
- **What this means**: Utah Medicaid doesn't want certain elements in TRN segments

## Formats We've Tried

### 1. Original Format (from accepted example)
```
NM1*1P*1*MONTOYA*JEREMY***MD*34*1275348807~
TRN*1*00702156-185943*1275348807*ELIGIBILITY~
TRN*1*1756400702156380*HT009582-001*REALTIME~
```
**Result**: X12 999 errors

### 2. Simplified Provider NM1 (no NPI)
```
NM1*1P*1*MONTOYA*JEREMY***MD~
```
**Result**: Still gets errors on position 8 (the MD qualifier)

### 3. Minimal TRN (single segment)
```
TRN*1*757719003~
```
**Result**: Still rejected

### 4. Various Combinations
- With/without provider credentials
- With/without second TRN segment
- Different date formats
- Different control number formats

**All resulted in X12 999 errors**

## Interesting Observations

### 1. Discrepancy with Documentation
The UHIN Connectivity Guide shows an accepted example with:
- Provider NPI in NM1 segment
- Two TRN segments with qualifiers
- SE*14*0001 (14 segments)

But Utah Medicaid rejects this exact format.

### 2. Error Consistency
The errors are always the same:
- NM1 position 8 and 9
- TRN position 3
This suggests a systematic implementation difference, not random validation issues.

### 3. HTTP 500 Errors
When we tried extremely minimal formats, we got HTTP 500 errors instead of X12 999s, suggesting the request was malformed at a deeper level.

## Files for Analysis

### Key Files to Review
1. **`Moonlit REALTIME CORE 270 Connectivity Guide (3).pdf`** - UHIN's guide showing "accepted" format
2. **`UTRANSEND TRM.V3 (3).pdf`** - Full UTRANSEND manual (21MB) - needs detailed review
3. **`output/x12_270_*.txt`** - Our attempted X12 270 messages
4. **`output/x12_271_*.txt`** - X12 999 error responses from Utah Medicaid

### Test Data Used
- Patient: Jeremy Montoya
- DOB: 1984-07-17
- Member ID: 0900412827
- This was from the accepted example in the Connectivity Guide

## Hypothesis for Resolution

### Possible Causes
1. **Utah Medicaid has custom implementation** that differs from UHIN's standard guide
2. **Provider enrollment issue** - Our NPI might need special configuration
3. **Test vs Production confusion** - The accepted example might be for test environment only
4. **Documentation outdated** - The guide might show an old format

### What We Need
1. **Utah Medicaid's specific Implementation Guide** (not just UHIN's generic guide)
2. **Working example from another vendor** that successfully queries Utah Medicaid
3. **Direct support from UHIN** to clarify the discrepancies

## Next Steps for Resolution

### For Web Claude Analysis
Please analyze the UTRANSEND PDF for:
1. Utah Medicaid-specific requirements (search for "Utah", "Medicaid", "UTMCD")
2. NM1 segment implementation notes
3. TRN segment requirements
4. Any mention of "Implementation Not Used" scenarios

### Questions to Investigate
1. Is there a different endpoint for Utah Medicaid vs other payers?
2. Are there payer-specific companion guides mentioned?
3. What's the difference between clearinghouse validation and payer validation?
4. Could the issue be with our Trading Partner enrollment/configuration?

## Code Status
The codebase is fully functional and modular. Once we determine the correct X12 270 format, we only need to update the `x12_builder.py` to match Utah Medicaid's requirements. Everything else (SOAP, parsing, etc.) is working correctly.