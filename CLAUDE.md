# UHIN 270/271 Eligibility Checking - Complete Working System

## 🚀 Quick Start

```bash
# Terminal 1: Backend (port 5001)
cd /Users/macsweeney/uhin-eligibility-checker
python backend/app.py

# Terminal 2: Frontend (port 5174)
cd /Users/macsweeney/uhin-eligibility-checker/frontend
npm run dev
```

Access at: http://localhost:5174

## ✅ Current System Status (2025-09-30)

### Working Components
- **Core X12 270/271 UHIN Integration** - Fully functional with Utah Medicaid
- **Flask Backend API** - Running on port 5001 with eligibility & enrollment endpoints
- **React Frontend** - Mobile-first interface with 5-step enrollment wizard
- **SQLite Database** - Stores eligibility checks and enrollment records
- **TAM Detection** - Correctly identifies Targeted Adult Medicaid vs managed care

### Critical Technical Fixes Applied
1. **X12 Gender**: Default 'M' (Utah rejects 'U') - Error 1068 fixed
2. **Port Conflict**: Moved to 5001 (macOS AirPlay uses 5000)
3. **TAM Recognition**: "TRADITIONAL ADULT" correctly identified as TAM
4. **Transportation Filter**: Modivcare excluded as non-payer
5. **CORS**: Configured for frontend at localhost:5174

### Test Results
- **Jeremy Montoya (1984-07-17)**: ✅ FFS qualified
- **Patient KN**: ✅ Fixed gender='U' issue
- **Patient EM**: ✅ Confirmed TAM patient

## ⚠️ PROTECTED FILES - DO NOT MODIFY

These files contain the exact working X12 format after extensive debugging:
- `x12_builder.py` - X12 270 builder with exact Utah Medicaid format
- `soap_client.py` - SOAP client for UHIN connection
- `main.py` - Main eligibility checker orchestration
- `parser.py` - X12 271 response parser with TAM detection
- `.env.local` - UHIN credentials and configuration

See `X12_FIX_JOURNEY.md` and `PROTECTED_FILES.md` for critical context.

## 📋 System Architecture

### Backend Structure
```
backend/
├── app.py           # Flask API (port 5001)
├── database.py      # SQLite with eligibility_checks & cm_enrollments
└── requirements.txt # Dependencies
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── EligibilityCheck.jsx  # Name + DOB input form
│   │   ├── ResultScreen.jsx      # Qualified/not qualified display
│   │   ├── EnrollmentFlow.jsx    # 5-step enrollment wizard
│   │   └── RecentChecks.jsx      # History display
│   └── App.jsx                    # Main router
└── package.json
```

## 🔌 API Reference

### POST /api/eligibility/check
Check if patient qualifies for contingency management.

**Request:**
```json
{
  "first_name": "Jeremy",
  "last_name": "Montoya",
  "date_of_birth": "1984-07-17"
}
```

**Response (Qualified):**
```json
{
  "success": true,
  "qualified": true,
  "patient_info": {
    "first_name": "Jeremy",
    "last_name": "Montoya",
    "medicaid_id": "0900412827"
  },
  "checked_at": "2025-09-30T10:30:00Z"
}
```

### POST /api/enrollment/create
Create new CM program enrollment.

**Request:**
```json
{
  "patient_id": "0900412827",
  "first_name": "Jeremy",
  "last_name": "Montoya",
  "date_of_birth": "1984-07-17",
  "phone": "8015551234",
  "enrollment_data": {...}
}
```

## 🏗️ Technical Implementation Details

### UHIN Connection
- **Endpoint**: https://ws.uhin.org/webservices/core/soaptype4.asmx
- **Trading Partner**: HT009582-001
- **Receiver**: HT000004-001 (Utah Medicaid)
- **Transaction**: RealTime CORE 270/271
- **Security**: WS-Security UsernameToken

### X12 270 Format (Critical - Do Not Change)
```
ISA*00*          *00*          *ZZ*HT009582-001   *ZZ*HT000004-001...
GS*HS*HT009582-001*HT000004-001...
ST*270*0001*005010X279A1~
BHT*0022*13...
HL*1**20*1~
NM1*PR*2*UTAH MEDICAID FFS*****46*HT000004-001~
HL*2*1*21*1~
NM1*1P*1*[PROVIDER_LAST]*[PROVIDER_FIRST]****XX*[NPI]~
HL*3*2*22*0~
TRN*1*[TRACE_NUM]*[NPI]~
NM1*IL*1*[PATIENT_LAST]*[PATIENT_FIRST]****MI*[MEDICAID_ID]~
DMG*D8*[DOB]*[M/F]~
DTP*291*RD8*[DATE_RANGE]~
EQ*30~
SE*13*0001~
GE*1...
IEA*1...
```

**Key Requirements:**
- Provider NM1 uses `XX` qualifier (not `MD*34`)
- ONE TRN segment per subscriber loop
- TRN03 must be exactly 10 characters (use NPI)
- Segment count: 13 from ST to SE
- Gender: M or F only (no U)

### FFS Eligibility Detection Logic
```python
# Parser identifies Traditional FFS by checking:
- Plan contains "Traditional Medicaid" or "Targeted Adult Medicaid"
- No MCO assignment (Molina, SelectHealth, Anthem, Healthy U)
- Active coverage (EB codes 1-5)
- Not transportation vendor (Modivcare, Logisticare)
```

## 🔮 Next Development Steps

1. **Notifyre Integration** - SMS enrollment links
2. **PDF Generation** - Enrollment documents
3. **Authentication** - CPSS user login system
4. **Production Deploy** - Cloud hosting
5. **Analytics** - Enrollment metrics dashboard

## 🛠️ Troubleshooting

### Eligibility Checker Issues
1. Check `.env.local` credentials
2. Run `python test_live_connection.py` to verify UHIN connection
3. Review `X12_FIX_JOURNEY.md` for format requirements
4. Check `output/` directory for saved X12 messages

### Common Errors
- **AAA*Y**42*Y~** : Invalid/missing subscriber ID
- **AAA*Y**41*Y~** : Invalid/missing date of birth
- **AAA*Y**73*N~** : Invalid patient gender (use M/F not U)
- **Port 5000 in use**: macOS AirPlay conflict, use 5001

### Development Notes
- **Credentials**: Stored in `.env.local` (never commit)
- **Testing**: Use Jeremy Montoya (DOB: 1984-07-17, ID: 0900412827)
- **Response Time**: Expect 1-2 seconds from UHIN
- **Security**: Implement PII redaction in logs

## 📚 Additional Documentation

- `X12_FIX_JOURNEY.md` - Detailed debugging history
- `PROTECTED_FILES.md` - Files that must not be modified
- `backend/README.md` - Backend-specific details
- `frontend/README.md` - Frontend-specific details

## ⚡ Key Business Rules

### Qualifying for CM Program
- Must have Traditional FFS Medicaid (TAM or Traditional Adult)
- Cannot be in managed care (temporary 3-week FFS doesn't count)
- Stimulant use disorder only (meth/cocaine)
- Text-only outreach via Notifyre

### Enrollment Requirements
- Valid phone for SMS enrollment link
- Informed consent required
- CPSS referral tracking (e.g., Zack from USARA)
- Same-day enrollment in acute care settings