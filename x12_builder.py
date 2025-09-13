"""
X12 270 Message Builder for UHIN UTRANSEND Clearinghouse
Builds properly formatted X12 270 eligibility inquiry messages for Utah Medicaid
"""

from datetime import datetime
from typing import Dict, Optional
import random


class X12_270Builder:
    """Builds X12 270 eligibility inquiry messages according to HIPAA 5010 standards"""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize the builder with configuration
        
        Args:
            config: Dictionary containing:
                - trading_partner: UHIN Trading Partner Number (e.g., 'HT009582-001')
                - receiver_id: Payer receiver ID (e.g., 'HT000004-001' for UHIN, 'HT000004-003' for test)
                - provider_npi: Provider's NPI number
                - provider_name: Provider's name
                - provider_first_name: Provider's first name (optional)
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
        """
        Format date according to X12 standards
        
        Args:
            date: DateTime object
            format_type: 'YYMMDD', 'YYYYMMDD', or 'CCYYMMDD'
        """
        if format_type == 'YYMMDD':
            return date.strftime('%y%m%d')
        elif format_type in ['YYYYMMDD', 'CCYYMMDD']:
            return date.strftime('%Y%m%d')
        else:
            raise ValueError(f"Unknown date format: {format_type}")
    
    def format_time(self, time: datetime) -> str:
        """Format time as HHMM for X12"""
        return time.strftime('%H%M')
    
    def add_segment(self, segment: str):
        """Add a segment to the message"""
        self.segments.append(segment)
        self.segment_count += 1
        
    def build(self, 
             patient_first_name: str,
             patient_last_name: str,
             patient_dob: str,
             patient_gender: str = 'U',
             member_id: Optional[str] = None,
             service_date: Optional[datetime] = None,
             test_mode: bool = False) -> str:
        """
        Build the complete X12 270 message
        
        Args:
            patient_first_name: Patient's first name
            patient_last_name: Patient's last name
            patient_dob: Patient date of birth (YYYYMMDD format string)
            patient_gender: M, F, or U (unknown)
            member_id: Optional member ID if known
            service_date: Service date (defaults to today)
            test_mode: If True, uses test flag in ISA segment
        
        Returns:
            Complete X12 270 message string
        """
        self.segments = []
        self.segment_count = 0
        
        # Generate control numbers
        control_number = self.generate_control_number()
        tracking_ref1 = self.generate_tracking_reference()
        tracking_ref2 = f"{int(datetime.now().timestamp())}{random.randint(100, 999)}"
        
        # Date/time formatting
        now = datetime.now()
        date_6 = self.format_date(now, 'YYMMDD')
        date_8 = self.format_date(now, 'YYYYMMDD')
        time_4 = self.format_time(now)
        
        # Service date handling
        if service_date is None:
            service_date = now
        service_date_str = self.format_date(service_date, 'YYYYMMDD')
        
        # Convert patient DOB from YYYYMMDD string to X12 format
        if len(patient_dob) == 8:
            dob_formatted = patient_dob
        elif len(patient_dob) == 10 and '-' in patient_dob:
            # Handle YYYY-MM-DD format
            dob_formatted = patient_dob.replace('-', '')
        else:
            raise ValueError(f"Invalid date of birth format: {patient_dob}")
        
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
        
        # BHT - Beginning of Hierarchical Transaction (empty reference field like accepted example)
        self.add_segment(f"BHT*0022*13**{date_8}*{time_4}~")
        
        # HL - Hierarchical Level (Information Source - Payer)
        self.add_segment("HL*1**20*1~")
        
        # NM1 - Information Source Name (Payer) - matching accepted format exactly
        self.add_segment(f"NM1*PR*2*UTAH MEDICAID FFS*****46*{self.config['receiver_id']}~")
        
        # HL - Hierarchical Level (Information Receiver - Provider)
        self.add_segment("HL*2*1*21*1~")
        
        # NM1 - Information Receiver Name (Provider) - using XX qualifier with NPI
        self.add_segment(
            f"NM1*1P*1*{self.config.get('provider_last', 'PROVIDER')}*{self.config.get('provider_first', 'TEST')}****XX*{self.config['provider_npi']}~"
        )
        
        # HL - Hierarchical Level (Subscriber/Patient)
        self.add_segment("HL*3*2*22*0~")
        
        # TRN - Trace Number with sender ID as originator (10 chars max for TRN03)
        # Using first 10 chars of provider NPI as originator reference
        originator = self.config.get('provider_npi', '1275348807')[:10]
        self.add_segment(
            f"TRN*1*{tracking_ref1}*{originator}~"
        )
        
        # NM1 - Subscriber Name
        if member_id:
            self.add_segment(
                f"NM1*IL*1*{patient_last_name.upper()}*{patient_first_name.upper()}****MI*{member_id}~"
            )
        else:
            # Without member ID, still include patient name
            self.add_segment(
                f"NM1*IL*1*{patient_last_name.upper()}*{patient_first_name.upper()}~"
            )
        
        # DMG - Demographic Information
        self.add_segment(f"DMG*D8*{dob_formatted}*{patient_gender.upper()}~")
        
        # DTP - Date or Time Period (Service Date Range)
        self.add_segment(f"DTP*291*RD8*{service_date_str}-{service_date_str}~")
        
        # EQ - Eligibility or Benefit Inquiry
        # 30 = Health Benefit Plan Coverage
        self.add_segment("EQ*30~")
        
        # SE - Transaction Set Trailer
        # Count segments from ST through SE inclusive
        # ST, BHT, HL, NM1, HL, NM1, HL, TRN, NM1, DMG, DTP, EQ, SE = 13
        self.add_segment(f"SE*13*0001~")
        
        # GE - Functional Group Trailer
        self.add_segment(f"GE*1*{control_number}~")
        
        # IEA - Interchange Control Trailer
        self.add_segment(f"IEA*1*{control_number}~")
        
        # Join all segments with newlines for readability
        return '\n'.join(self.segments)
    
    def validate(self, x12_message: str) -> Dict[str, any]:
        """
        Validate an X12 270 message for common issues
        
        Returns:
            Dictionary with validation results
        """
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
            # Extract segment ID (first 2-3 characters before *)
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
        
        # Check ISA segment format
        if lines and lines[0].startswith('ISA'):
            isa_parts = lines[0].split('*')
            if len(isa_parts) != 17:
                results['errors'].append(f"ISA segment has {len(isa_parts)} elements, expected 17")
                results['valid'] = False
        
        # Check for matching control numbers
        control_numbers = set()
        for line in lines:
            if line.startswith('ISA') or line.startswith('GS') or line.startswith('GE') or line.startswith('IEA'):
                parts = line.split('*')
                if line.startswith('ISA') and len(parts) > 13:
                    control_numbers.add(parts[13])
                elif line.startswith('IEA') and len(parts) > 2:
                    control_numbers.add(parts[2].rstrip('~'))
        
        if len(control_numbers) > 1:
            results['warnings'].append(f"Multiple control numbers found: {control_numbers}")
        
        return results