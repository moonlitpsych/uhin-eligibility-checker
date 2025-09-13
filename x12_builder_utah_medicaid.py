"""
Utah Medicaid Specific X12 270 Message Builder
Based on web Claude's analysis of UTRANSEND requirements
Utah Medicaid requires minimal format with many elements marked as "Not Used"
"""

from datetime import datetime
from typing import Dict, Optional
import random


class UtahMedicaidX12_270Builder:
    """Builds minimal X12 270 messages specifically for Utah Medicaid FFS"""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize with configuration
        
        Args:
            config: Dictionary containing:
                - trading_partner: UHIN Trading Partner Number
                - receiver_id: Utah Medicaid receiver ID
        """
        self.config = config
        self.segments = []
        
    def generate_control_number(self, length: int = 9) -> str:
        """Generate a unique control number"""
        return str(int(datetime.now().timestamp()))[-length:]
    
    def format_date(self, date: datetime, format_type: str = 'YYMMDD') -> str:
        """Format date according to X12 standards"""
        if format_type == 'YYMMDD':
            return date.strftime('%y%m%d')
        elif format_type in ['YYYYMMDD', 'CCYYMMDD']:
            return date.strftime('%Y%m%d')
        else:
            raise ValueError(f"Unknown date format: {format_type}")
    
    def format_time(self, time: datetime) -> str:
        """Format time as HHMM for X12"""
        return time.strftime('%H%M')
    
    def build(self, 
             patient_first_name: str,
             patient_last_name: str,
             patient_dob: str,
             patient_gender: str = 'U',
             member_id: Optional[str] = None,
             provider_first_name: str = 'JEREMY',
             provider_last_name: str = 'MONTOYA',
             test_mode: bool = False) -> str:
        """
        Build minimal X12 270 message for Utah Medicaid
        
        Based on web Claude's analysis:
        - NM1 provider segment WITHOUT positions 7-9 (no MD qualifier, no NPI)
        - Single TRN segment with ONLY trace number (no additional qualifiers)
        - 12 total segments between ST and SE
        """
        self.segments = []
        
        # Generate control numbers
        control_number = self.generate_control_number()
        now = datetime.now()
        date_6 = self.format_date(now, 'YYMMDD')
        date_8 = self.format_date(now, 'YYYYMMDD')
        time_4 = self.format_time(now)
        
        # Format patient DOB
        if '-' in patient_dob:
            dob_formatted = patient_dob.replace('-', '')
        else:
            dob_formatted = patient_dob
        
        # ISA - Interchange Control Header
        test_flag = 'T' if test_mode else 'P'
        self.segments.append(
            f"ISA*00*          *00*          *ZZ*{self.config['trading_partner'].ljust(15)}"
            f"*ZZ*{self.config['receiver_id'].ljust(15)}"
            f"*{date_6}*{time_4}*^*00501*{control_number}*0*{test_flag}*:~"
        )
        
        # GS - Functional Group Header
        self.segments.append(
            f"GS*HS*{self.config['trading_partner']}*{self.config['receiver_id']}"
            f"*{date_8}*{time_4}*{control_number}*X*005010X279A1~"
        )
        
        # ST - Transaction Set Header
        self.segments.append("ST*270*0001*005010X279A1~")
        
        # BHT - Beginning of Hierarchical Transaction
        self.segments.append(f"BHT*0022*13**{date_8}*{time_4}~")
        
        # HL - Hierarchical Level (Payer)
        self.segments.append("HL*1**20*1~")
        
        # NM1 - Payer Name (Utah Medicaid FFS)
        self.segments.append(f"NM1*PR*2*UTAH MEDICAID FFS*****46*{self.config['receiver_id']}~")
        
        # HL - Hierarchical Level (Provider)
        self.segments.append("HL*2*1*21*1~")
        
        # NM1 - Provider Name (using XX qualifier with NPI)
        provider_npi = self.config.get('provider_npi', '1275348807')  # Default to known NPI
        self.segments.append(f"NM1*1P*1*{provider_last_name}*{provider_first_name}****XX*{provider_npi}~")
        
        # HL - Hierarchical Level (Subscriber)
        self.segments.append("HL*3*2*22*0~")
        
        # TRN - Trace Number with provider NPI as originator (10 chars max for TRN03)
        trace_number = f"{control_number[:8]}{control_number[-6:]}"
        originator = self.config.get('provider_npi', '1275348807')[:10]
        self.segments.append(f"TRN*1*{trace_number}*{originator}~")
        
        # NM1 - Subscriber Name
        if member_id:
            self.segments.append(
                f"NM1*IL*1*{patient_last_name.upper()}*{patient_first_name.upper()}****MI*{member_id}~"
            )
        else:
            self.segments.append(
                f"NM1*IL*1*{patient_last_name.upper()}*{patient_first_name.upper()}~"
            )
        
        # DMG - Demographics
        self.segments.append(f"DMG*D8*{dob_formatted}*{patient_gender.upper()}~")
        
        # DTP - Date/Time Period (Service Date)
        self.segments.append(f"DTP*291*RD8*{date_8}-{date_8}~")
        
        # EQ - Eligibility/Benefit Inquiry
        self.segments.append("EQ*30~")
        
        # SE - Transaction Set Trailer (13 segments from ST to SE)
        self.segments.append("SE*13*0001~")
        
        # GE - Functional Group Trailer
        self.segments.append(f"GE*1*{control_number}~")
        
        # IEA - Interchange Control Trailer
        self.segments.append(f"IEA*1*{control_number}~")
        
        return '\n'.join(self.segments)
    
    def build_ultra_minimal(self, 
                           patient_first_name: str,
                           patient_last_name: str,
                           patient_dob: str,
                           patient_gender: str = 'U',
                           member_id: Optional[str] = None) -> str:
        """
        Build ULTRA minimal X12 270 if the standard minimal still fails
        - Provider as organization (not individual)
        - No TRN segment at all
        """
        self.segments = []
        
        control_number = self.generate_control_number()
        now = datetime.now()
        date_6 = self.format_date(now, 'YYMMDD')
        date_8 = self.format_date(now, 'YYYYMMDD')
        time_4 = self.format_time(now)
        
        if '-' in patient_dob:
            dob_formatted = patient_dob.replace('-', '')
        else:
            dob_formatted = patient_dob
        
        # ISA
        self.segments.append(
            f"ISA*00*          *00*          *ZZ*{self.config['trading_partner'].ljust(15)}"
            f"*ZZ*{self.config['receiver_id'].ljust(15)}"
            f"*{date_6}*{time_4}*^*00501*{control_number}*0*P*:~"
        )
        
        # GS
        self.segments.append(
            f"GS*HS*{self.config['trading_partner']}*{self.config['receiver_id']}"
            f"*{date_8}*{time_4}*{control_number}*X*005010X279A1~"
        )
        
        # ST
        self.segments.append("ST*270*0001*005010X279A1~")
        
        # BHT
        self.segments.append(f"BHT*0022*13**{date_8}*{time_4}~")
        
        # HL - Payer
        self.segments.append("HL*1**20*1~")
        
        # NM1 - Payer
        self.segments.append(f"NM1*PR*2*UTAH MEDICAID FFS*****46*{self.config['receiver_id']}~")
        
        # HL - Provider
        self.segments.append("HL*2*1*21*1~")
        
        # NM1 - Provider as ORGANIZATION (entity type 2)
        self.segments.append("NM1*1P*2*PROVIDER~")
        
        # HL - Subscriber
        self.segments.append("HL*3*2*22*0~")
        
        # NM1 - Subscriber (NO TRN segment at all)
        if member_id:
            self.segments.append(
                f"NM1*IL*1*{patient_last_name.upper()}*{patient_first_name.upper()}****MI*{member_id}~"
            )
        else:
            self.segments.append(
                f"NM1*IL*1*{patient_last_name.upper()}*{patient_first_name.upper()}~"
            )
        
        # DMG
        self.segments.append(f"DMG*D8*{dob_formatted}*{patient_gender.upper()}~")
        
        # EQ
        self.segments.append("EQ*30~")
        
        # SE - Only 11 segments now (no TRN, no DTP)
        self.segments.append("SE*11*0001~")
        
        # GE
        self.segments.append(f"GE*1*{control_number}~")
        
        # IEA
        self.segments.append(f"IEA*1*{control_number}~")
        
        return '\n'.join(self.segments)