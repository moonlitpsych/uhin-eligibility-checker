# Prompt for Web Claude to Solve UHIN X12 999 Errors

## Context
I've been working with Claude Code to build a Python-based eligibility checker for Utah Medicaid through UHIN's UTRANSEND clearinghouse. The system successfully connects and authenticates, but Utah Medicaid consistently returns X12 999 (Functional Acknowledgment) errors rejecting our X12 270 eligibility inquiries.

## Your Mission
You have access to:
1. **This GitHub repository**: https://github.com/moonlitpsych/uhin-eligibility-checker
2. **The UTRANSEND TRM.V3 (3).pdf** - A comprehensive 21MB manual that Claude Code couldn't fully read
3. **The implementation summary** in `IMPLEMENTATION_SUMMARY.md` documenting everything we've tried

## Critical Issue to Solve
Utah Medicaid returns X12 999 errors with these specific problems:
- **NM1 segment (position 6)**: Errors 66/67 on positions 8-9 (provider ID qualifier and NPI)
- **TRN segment (position 9)**: Error 509 on position 3 (additional qualifiers)
- Error codes I12 ("Implementation 'Not Used' element present") and I5 ("Implementation segment not expected")

## The Mystery
The UHIN Connectivity Guide shows an accepted X12 270 example that includes:
- Provider NPI in NM1*1P segment (position 8-9)
- Two TRN segments with multiple qualifiers
- Exactly the elements that Utah Medicaid is rejecting

This suggests either:
1. The documentation is outdated/incorrect
2. Utah Medicaid has special requirements different from other payers
3. There's a configuration issue with our Trading Partner setup
4. We're missing some context about when certain elements should/shouldn't be included

## What I Need You to Do

### 1. Deep Dive into the UTRANSEND PDF
Please thoroughly search the UTRANSEND manual for:
- **Utah Medicaid specific requirements** (search: "Utah", "Medicaid", "UTMCD", "HT000004-001")
- **NM1 segment implementation notes** especially for loop 2100
- **TRN segment requirements** for loop 2000
- **"Implementation Not Used" scenarios** - when elements should be omitted
- **Payer-specific companion guides** or variations
- **Situational rules** that might explain when to include/exclude elements
- Any mention of **error codes 66, 67, 509, I12, or I5**

### 2. Analyze the Discrepancy
Compare:
- The accepted example in `Moonlit REALTIME CORE 270 Connectivity Guide (3).pdf`
- The errors we're getting (documented in `IMPLEMENTATION_SUMMARY.md`)
- What the UTRANSEND manual actually specifies

Look for:
- Conditional requirements (e.g., "include NPI only if...")
- Version differences (5010 variations)
- Test vs Production differences
- Provider type distinctions

### 3. Generate Solution Hypotheses
Based on your analysis, provide:
1. **Most likely root cause** of the X12 999 errors
2. **Specific X12 270 format** Utah Medicaid expects
3. **Step-by-step testing plan** to validate the solution
4. **Alternative approaches** if the first solution doesn't work

### 4. Code Modifications
Suggest specific changes to:
- `x12_builder.py` - The exact segment format needed
- Any other files that might need adjustment

### 5. Create Implementation Strategy
Provide a clear action plan for the next Claude Code session:
1. What to try first
2. How to test it
3. What to do if it fails
4. How to know when we've succeeded

## Additional Context
- **Credentials are valid**: We successfully authenticate with UHIN
- **Connection works**: We receive responses (just X12 999 errors)
- **Provider NPI**: 1275348807 (Moonlit PLLC)
- **Trading Partner**: HT009582-001
- **Test patient**: Jeremy Montoya (DOB: 1984-07-17, Member ID: 0900412827)

## Success Criteria
We need to receive a valid X12 271 eligibility response (not a 999 error) that includes:
- Patient eligibility status
- Plan information indicating Traditional FFS or Managed Care
- No rejection errors

Please use your ability to read the full UTRANSEND PDF to find the specific implementation requirements that we're missing. The answer is likely buried in the technical specifications that differentiate Utah Medicaid's requirements from the generic UHIN example.