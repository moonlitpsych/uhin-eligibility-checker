"""
Minimal X12 270 Message Builder for Utah Medicaid via UHIN
Creates the most minimal valid X12 270 with only required elements
"""

from datetime import datetime
from typing import Dict, Optional
import random


class MinimalX12_270Builder:
    """Builds minimal X12 270 eligibility inquiry messages"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.segments = []
        
    def generate_control_number(self, length: int = 9) -> str:
        """Generate a unique control number"""
        return str(int(datetime.now().timestamp()))[-length:]
    
    def build(self, 
             patient_first_name: str,
             patient_last_name: str,
             patient_dob: str,
             patient_gender: str = 'U',
             member_id: Optional[str] = None) -> str:
        """Build minimal X12 270 message"""
        
        self.segments = []
        
        # Control numbers and dates
        control_number = self.generate_control_number()
        now = datetime.now()
        date_6 = now.strftime('%y%m%d')
        date_8 = now.strftime('%Y%m%d')
        time_4 = now.strftime('%H%M')
        
        # Format DOB
        if '-' in patient_dob:
            dob_formatted = patient_dob.replace('-', '')
        else:
            dob_formatted = patient_dob
        
        # ISA - Interchange Control Header
        self.segments.append(
            f"ISA*00*          *00*          *ZZ*{self.config['trading_partner'].ljust(15)}"
            f"*ZZ*{self.config['receiver_id'].ljust(15)}"
            f"*{date_6}*{time_4}*^*00501*{control_number}*0*P*:~"
        )
        
        # GS - Functional Group Header
        self.segments.append(
            f"GS*HS*{self.config['trading_partner']}*{self.config['receiver_id']}"
            f"*{date_8}*{time_4}*{control_number}*X*005010X279A1~"
        )
        
        # ST - Transaction Set Header
        self.segments.append("ST*270*0001*005010X279A1~")
        
        # BHT - Beginning of Hierarchical Transaction
        self.segments.append(f"BHT*0022*13*{control_number}*{date_8}*{time_4}~")
        
        # HL - Hierarchical Level (Information Source - Payer)
        self.segments.append("HL*1**20*1~")
        
        # NM1 - Payer Name (Minimal - just entity type and name)
        self.segments.append("NM1*PR*2*UTAH MEDICAID~")
        
        # HL - Hierarchical Level (Information Receiver - Provider)
        self.segments.append("HL*2*1*21*1~")
        
        # NM1 - Provider Name (Minimal - just entity type and name)
        self.segments.append("NM1*1P*2*PROVIDER~")
        
        # HL - Hierarchical Level (Subscriber)
        self.segments.append("HL*3*2*22*0~")
        
        # TRN - Trace Number (Minimal - just trace number)
        self.segments.append(f"TRN*1*{control_number}~")
        
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
        
        # EQ - Eligibility Inquiry
        self.segments.append("EQ*30~")
        
        # SE - Transaction Set Trailer
        # Count segments from ST through SE inclusive
        segment_count = len(self.segments) - 2 + 1  # -2 for ISA/GS, +1 for SE itself
        self.segments.append(f"SE*{segment_count}*0001~")
        
        # GE - Functional Group Trailer
        self.segments.append(f"GE*1*{control_number}~")
        
        # IEA - Interchange Control Trailer
        self.segments.append(f"IEA*1*{control_number}~")
        
        return '\n'.join(self.segments)