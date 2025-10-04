"""
Enhanced X12 270 Message Builder for Multiple Payers via UHIN
Supports Utah Medicaid, U of U Health Plans, and other insurers
"""

from datetime import datetime
from typing import Dict, Optional, List
import random


class X12_270BuilderMulti:
    """Builds X12 270 eligibility inquiry messages for multiple payers"""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize the builder with configuration

        Args:
            config: Dictionary containing:
                - trading_partner: UHIN Trading Partner Number
                - receiver_id: Payer receiver ID (varies by payer)
                - payer_name: Name of the payer
                - payer_code: Payer code/ID
                - provider_npi: Provider's NPI number
                - provider_name: Provider's name
                - provider_first_name: Provider's first name
        """
        self.config = config
        self.segment_count = 0
        self.segments = []

    def generate_control_number(self, length: int = 9) -> str:
        """Generate a unique control number"""
        return str(int(datetime.now().timestamp()))[-length:]

    def generate_tracking_reference(self) -> str:
        """Generate a tracking reference number"""
        timestamp = str(int(datetime.now().timestamp()))
        random_suffix = str(random.randint(100000, 999999))
        return f"{timestamp[-8]}-{random_suffix}"

    def format_date(self, date: datetime, format_type: str = 'YYMMDD') -> str:
        """Format date according to X12 standards"""
        if format_type == 'YYMMDD':
            return date.strftime('%y%m%d')
        elif format_type in ['YYYYMMDD', 'CCYYMMDD']:
            return date.strftime('%Y%m%d')
        return date.strftime('%Y%m%d')

    def format_time(self, time: datetime) -> str:
        """Format time as HHMM for X12 standards"""
        return time.strftime('%H%M')

    def add_segment(self, segment: str):
        """Add a segment to the message and increment counter"""
        self.segments.append(segment)
        self.segment_count += 1

    def build(self,
             patient_first_name: str,
             patient_last_name: str,
             patient_dob: str,
             patient_gender: str = 'M',
             member_id: Optional[str] = None,
             service_date: Optional[datetime] = None,
             test_mode: bool = False,
             eligibility_segments: Optional[List[str]] = None) -> str:
        """
        Build the complete X12 270 message with payer-specific configuration

        Args:
            patient_first_name: Patient's first name
            patient_last_name: Patient's last name
            patient_dob: Patient date of birth (YYYYMMDD format string)
            patient_gender: M or F (defaults to M)
            member_id: Optional member ID
            service_date: Service date (defaults to today)
            test_mode: If True, uses test flag in ISA segment
            eligibility_segments: List of eligibility/benefit codes to check

        Returns:
            Complete X12 270 message string
        """
        self.segments = []
        self.segment_count = 0

        # Generate control numbers
        control_number = self.generate_control_number()
        tracking_ref = self.generate_tracking_reference()

        # Date/time formatting
        now = datetime.now()
        date_6 = self.format_date(now, 'YYMMDD')
        date_8 = self.format_date(now, 'YYYYMMDD')
        time_4 = self.format_time(now)

        # Service date handling
        if service_date is None:
            service_date = now
        service_date_str = self.format_date(service_date, 'YYYYMMDD')

        # Convert patient DOB to proper format
        if len(patient_dob) == 8:
            dob_formatted = patient_dob
        elif len(patient_dob) == 10 and '-' in patient_dob:
            dob_formatted = patient_dob.replace('-', '')
        else:
            raise ValueError(f"Invalid date of birth format: {patient_dob}")

        # Ensure gender is valid
        if patient_gender not in ['M', 'F']:
            patient_gender = 'M'  # Default to M if unknown

        # Default eligibility segments
        if not eligibility_segments:
            eligibility_segments = ['30']  # Default: Health Benefit Plan Coverage

        # Get payer info from config
        payer_name = self.config.get('payer_name', 'UNKNOWN PAYER')
        payer_code = self.config.get('payer_code', self.config.get('receiver_id', ''))

        # ISA - Interchange Control Header
        test_flag = 'T' if test_mode else 'P'
        self.add_segment(
            f"ISA*00*          *00*          *ZZ*{self.config['trading_partner'].ljust(15)}"
            f"*ZZ*{self.config['receiver_id'].ljust(15)}"
            f"*{date_6}*{time_4}*^*00501*{control_number}*1*{test_flag}*:~"
        )

        # GS - Functional Group Header
        self.add_segment(
            f"GS*HS*{self.config['trading_partner']}*{self.config['receiver_id']}"
            f"*{date_8}*{time_4}*{control_number}*X*005010X279A1~"
        )

        # ST - Transaction Set Header
        self.add_segment("ST*270*0001*005010X279A1~")

        # BHT - Beginning of Hierarchical Transaction
        self.add_segment(f"BHT*0022*13**{date_8}*{time_4}~")

        # HL - Hierarchical Level (Information Source - Payer)
        self.add_segment("HL*1**20*1~")

        # NM1 - Information Source Name (Payer)
        # Use receiver ID with 46 qualifier (standard for UHIN)
        self.add_segment(f"NM1*PR*2*{payer_name}*****46*{self.config['receiver_id']}~")

        # HL - Hierarchical Level (Information Receiver - Provider)
        self.add_segment("HL*2*1*21*1~")

        # NM1 - Information Receiver Name (Provider)
        provider_last = self.config.get('provider_name', 'PROVIDER')
        provider_first = self.config.get('provider_first_name', '')
        if provider_first:
            self.add_segment(
                f"NM1*1P*1*{provider_last}*{provider_first}****XX*{self.config['provider_npi']}~"
            )
        else:
            # Organization format if no first name
            self.add_segment(
                f"NM1*1P*2*{provider_last}*****XX*{self.config['provider_npi']}~"
            )

        # HL - Hierarchical Level (Subscriber/Patient)
        self.add_segment("HL*3*2*22*0~")

        # TRN - Trace Number
        originator = self.config.get('provider_npi', '1234567890')[:10]
        self.add_segment(f"TRN*1*{tracking_ref}*{originator}~")

        # NM1 - Subscriber Name
        if member_id:
            self.add_segment(
                f"NM1*IL*1*{patient_last_name.upper()}*{patient_first_name.upper()}****MI*{member_id}~"
            )
        else:
            # Without member ID, still need the NM1 segment
            self.add_segment(
                f"NM1*IL*1*{patient_last_name.upper()}*{patient_first_name.upper()}~"
            )

        # DMG - Demographic Information
        self.add_segment(f"DMG*D8*{dob_formatted}*{patient_gender.upper()}~")

        # DTP - Date or Time Period (Service Date Range)
        self.add_segment(f"DTP*291*RD8*{service_date_str}-{service_date_str}~")

        # EQ - Eligibility or Benefit Inquiry
        # Support multiple eligibility segments if specified
        eq_segments_added = 0
        for eq_code in eligibility_segments:
            self.add_segment(f"EQ*{eq_code}~")
            eq_segments_added += 1

        # Calculate segment count
        # ISA and IEA don't count, GS and GE don't count
        # Count from ST to SE inclusive
        # ST, BHT, HL, NM1, HL, NM1, HL, TRN, NM1, DMG, DTP, EQ(s), SE
        segment_count = 12 + eq_segments_added  # Base segments + EQ segments + SE itself

        # SE - Transaction Set Trailer
        self.add_segment(f"SE*{segment_count}*0001~")

        # GE - Functional Group Trailer
        self.add_segment(f"GE*1*{control_number}~")

        # IEA - Interchange Control Trailer
        self.add_segment(f"IEA*1*{control_number}~")

        # Join all segments with newlines for readability
        return '\n'.join(self.segments)

    def validate(self, x12_message: str) -> Dict[str, any]:
        """Validate an X12 270 message for common issues"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'segment_count': 0
        }

        lines = x12_message.strip().split('\n')
        results['segment_count'] = len(lines)

        # Check for required segments
        required_segments = ['ISA', 'GS', 'ST', 'BHT', 'HL', 'NM1', 'EQ', 'SE', 'GE', 'IEA']
        found_segments = set()

        for line in lines:
            if '*' in line:
                segment_id = line.split('*')[0]
            else:
                segment_id = line[:3] if len(line) >= 3 else ''

            if segment_id in required_segments:
                found_segments.add(segment_id)

        missing = set(required_segments) - found_segments
        if missing:
            results['valid'] = False
            results['errors'].append(f"Missing required segments: {', '.join(missing)}")

        return results