"""
X12 271 Response Parser for Utah Medicaid FFS Eligibility
Parses X12 271 eligibility responses and determines FFS vs Managed Care status
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class X12_271Parser:
    """Parses X12 271 eligibility response messages"""
    
    # Eligibility/Benefit codes (EB01)
    ELIGIBILITY_CODES = {
        '1': 'Active Coverage',
        '2': 'Active - Full Risk Capitation',
        '3': 'Active - Services Capitated',
        '4': 'Active - Services Capitated to Primary Care Physician',
        '5': 'Active - Pending Investigation',
        '6': 'Inactive',
        '7': 'Inactive - Pending Eligibility Update',
        '8': 'Inactive - Pending Investigation',
        'A': 'Co-Insurance',
        'B': 'Deductible',
        'C': 'Coverage Basis',
        'D': 'Benefit Description',
        'E': 'Exclusions',
        'F': 'Limitations',
        'G': 'Out of Pocket (Stop Loss)',
        'H': 'Unlimited',
        'I': 'Non-Covered',
        'J': 'Cost Containment',
        'K': 'Reserve',
        'L': 'Primary Care Provider',
        'M': 'Pre-existing Condition',
        'N': 'Services Restricted to Following Provider',
        'O': 'Services Not Restricted to Following Provider',
        'P': 'Benefit Disclaimer',
        'Q': 'Second Surgical Opinion Required',
        'R': 'Other or Additional Payor',
        'S': 'Prior Year(s) History',
        'T': 'Card(s) Reported Lost/Stolen',
        'U': 'Contact Following Entity for Eligibility or Benefit Information',
        'V': 'Cannot Process',
        'W': 'Other Source of Data',
        'X': 'Health Care Facility',
        'Y': 'Spend Down'
    }
    
    # AAA Error codes
    AAA_ERROR_CODES = {
        '15': 'Required application data missing',
        '41': 'Authorization/Access Restrictions',
        '42': 'Unable to Respond at Current Time',
        '43': 'Invalid/Missing Provider Identification',
        '44': 'Invalid/Missing Provider Name',
        '45': 'Invalid/Missing Provider Specialty',
        '46': 'Invalid/Missing Provider Phone Number',
        '47': 'Invalid/Missing Provider State',
        '48': 'Invalid/Missing Referring Provider Identification Number',
        '49': 'Provider is Not Primary Care Physician',
        '50': 'Provider Ineligible for Inquiries',
        '51': 'Provider Not on File',
        '52': 'Service Dates Not Within Provider Plan Enrollment',
        '53': 'Inquired Coverage Inconsistent with Provider Type',
        '54': 'Inappropriate Provider Role',
        '55': 'Invalid/Missing Provider Address',
        '56': 'Invalid/Missing NPI',
        '57': 'Invalid/Missing Taxonomy Code',
        '58': 'Invalid/Missing Provider ID Qualifier',
        '60': 'Invalid/Missing Subscriber ID',
        '61': 'Invalid/Missing Subscriber Name',
        '62': 'Invalid/Missing Subscriber Gender',
        '63': 'Invalid/Missing Subscriber Birth Date',
        '64': 'Invalid/Missing Subscriber/Insured Indicator',
        '65': 'Invalid/Missing Subscriber/Insured Name',
        '66': 'Subscriber/Insured Not Found',
        '67': 'Subscriber/Insured Not Eligible for Benefits',
        '68': 'Duplicate Subscriber ID',
        '69': 'Subscriber/Dependent Not Found',
        '70': 'Invalid/Missing Subscriber/Dependent Name',
        '71': 'Invalid/Missing Patient ID',
        '72': 'Invalid/Missing Patient Name',
        '73': 'Invalid/Missing Patient Gender',
        '74': 'Invalid/Missing Patient Birth Date',
        '75': 'Patient Not Found',
        '76': 'Duplicate Patient ID/Name'
    }
    
    def __init__(self):
        self.segments = []
        self.parsed_data = {}
        
    def parse(self, x12_271: str) -> Dict[str, any]:
        """
        Parse X12 271 response message
        
        Args:
            x12_271: Raw X12 271 response string
            
        Returns:
            Dictionary containing parsed eligibility information
        """
        # Clean and split the message into segments
        x12_271 = x12_271.strip()
        
        # Handle both ~ and newline as segment terminators
        if '~' in x12_271:
            self.segments = [seg.strip() for seg in x12_271.split('~') if seg.strip()]
        else:
            self.segments = [seg.strip() for seg in x12_271.split('\n') if seg.strip()]
        
        # Initialize result structure
        result = {
            'success': False,
            'eligible': False,
            'eligibility_details': [],
            'errors': [],
            'warnings': [],
            'patient_info': {},
            'payer_info': {},
            'provider_info': {},
            'plan_info': {},
            'ffs_status': 'UNKNOWN',
            'managed_care_detected': False,
            'raw_segments': {
                'EB': [],
                'AAA': [],
                'NM1': [],
                'DTP': [],
                'REF': []
            }
        }
        
        # Process each segment
        for segment in self.segments:
            if not segment:
                continue
                
            # Get segment ID (first 2-3 chars before * or ~)
            if '*' in segment:
                segment_id = segment.split('*')[0]
            else:
                segment_id = segment[:3] if len(segment) >= 3 else ''
            
            if segment_id == 'ISA':
                self._parse_isa(segment, result)
            elif segment_id == 'ST':
                self._parse_st(segment, result)
            elif segment_id == 'BHT':
                self._parse_bht(segment, result)
            elif segment_id == 'NM1':
                self._parse_nm1(segment, result)
            elif segment_id == 'EB':
                self._parse_eb(segment, result)
            elif segment_id == 'AAA':
                self._parse_aaa(segment, result)
            elif segment_id == 'DTP':
                self._parse_dtp(segment, result)
            elif segment_id == 'REF':
                self._parse_ref(segment, result)
            elif segment_id == 'MSG':
                self._parse_msg(segment, result)
        
        # Determine FFS status based on parsed data
        self._determine_ffs_status(result)
        
        # Set overall success flag
        if result['eligibility_details'] and not result['errors']:
            result['success'] = True
            result['eligible'] = any(
                detail.get('status') == 'Active Coverage' 
                for detail in result['eligibility_details']
            )
        
        return result
    
    def _parse_isa(self, segment: str, result: Dict):
        """Parse ISA segment for interchange information"""
        parts = segment.split('*')
        if len(parts) >= 17:
            result['interchange_info'] = {
                'sender_id': parts[6].strip(),
                'receiver_id': parts[8].strip(),
                'date': parts[9],
                'time': parts[10],
                'control_number': parts[13]
            }
    
    def _parse_st(self, segment: str, result: Dict):
        """Parse ST segment for transaction set information"""
        parts = segment.split('*')
        if len(parts) >= 3:
            result['transaction_info'] = {
                'type': parts[1],
                'control_number': parts[2]
            }
    
    def _parse_bht(self, segment: str, result: Dict):
        """Parse BHT segment for beginning of hierarchical transaction"""
        parts = segment.split('*')
        if len(parts) >= 5:
            result['transaction_info'] = result.get('transaction_info', {})
            result['transaction_info'].update({
                'purpose': parts[1],
                'reference': parts[2] if len(parts) > 2 else '',
                'date': parts[3] if len(parts) > 3 else '',
                'time': parts[4] if len(parts) > 4 else ''
            })
    
    def _parse_nm1(self, segment: str, result: Dict):
        """Parse NM1 segment for name information"""
        parts = segment.split('*')
        result['raw_segments']['NM1'].append(segment)
        
        if len(parts) < 3:
            return
        
        entity_type = parts[1]
        
        # PR = Payer
        if entity_type == 'PR':
            result['payer_info'] = {
                'name': parts[3] if len(parts) > 3 else '',
                'id_qualifier': parts[8] if len(parts) > 8 else '',
                'id': parts[9].rstrip('~') if len(parts) > 9 else ''
            }
            
            # Check for Utah Medicaid
            payer_name = parts[3].upper() if len(parts) > 3 else ''
            if 'MEDICAID' in payer_name or 'UTAH' in payer_name:
                result['payer_info']['is_utah_medicaid'] = True
                
                # Check for specific programs
                if 'TARGETED ADULT' in parts[3].upper():
                    result['plan_info']['program'] = 'Targeted Adult Medicaid'
                elif 'TRADITIONAL' in parts[3].upper():
                    result['plan_info']['program'] = 'Traditional Medicaid'
        
        # IL = Insured/Subscriber
        elif entity_type == 'IL':
            result['patient_info'] = {
                'last_name': parts[3] if len(parts) > 3 else '',
                'first_name': parts[4] if len(parts) > 4 else '',
                'middle_name': parts[5] if len(parts) > 5 else '',
                'id_qualifier': parts[8] if len(parts) > 8 else '',
                'member_id': parts[9].rstrip('~') if len(parts) > 9 else ''
            }
        
        # 1P = Provider
        elif entity_type == '1P':
            result['provider_info'] = {
                'last_name': parts[3] if len(parts) > 3 else '',
                'first_name': parts[4] if len(parts) > 4 else '',
                'id_qualifier': parts[8] if len(parts) > 8 else '',
                'npi': parts[9].rstrip('~') if len(parts) > 9 else ''
            }
    
    def _parse_eb(self, segment: str, result: Dict):
        """Parse EB segment for eligibility/benefit information"""
        parts = segment.split('*')
        result['raw_segments']['EB'].append(segment)
        
        if len(parts) < 2:
            return
        
        eligibility_code = parts[1]
        coverage_level = parts[2] if len(parts) > 2 else ''
        service_types = parts[3] if len(parts) > 3 else ''
        insurance_type = parts[4] if len(parts) > 4 else ''
        plan_description = parts[5] if len(parts) > 5 else ''
        
        detail = {
            'code': eligibility_code,
            'status': self.ELIGIBILITY_CODES.get(eligibility_code, f'Unknown ({eligibility_code})'),
            'coverage_level': coverage_level,
            'service_types': service_types,
            'insurance_type': insurance_type,
            'plan_description': plan_description.rstrip('~')
        }
        
        result['eligibility_details'].append(detail)
        
        # Check for managed care indicators
        if insurance_type:
            # HM = Health Maintenance Organization (HMO)
            if 'HM' in insurance_type.upper():
                result['managed_care_detected'] = True
                result['plan_info']['type'] = 'HMO'
            # MC = Medicaid
            elif 'MC' in insurance_type.upper():
                result['plan_info']['type'] = 'Medicaid'
                
                # Check plan description for FFS indicators
                if plan_description:
                    plan_upper = plan_description.upper()
                    if 'TARGETED ADULT' in plan_upper:
                        result['plan_info']['program'] = 'Targeted Adult Medicaid'
                        result['ffs_status'] = 'TRADITIONAL_FFS'
                    elif 'TRADITIONAL' in plan_upper:
                        result['plan_info']['program'] = 'Traditional Medicaid'
                        result['ffs_status'] = 'TRADITIONAL_FFS'
                    elif any(mc in plan_upper for mc in ['MOLINA', 'SELECTHEALTH', 'ANTHEM', 'HEALTHY U']):
                        result['managed_care_detected'] = True
                        result['ffs_status'] = 'MANAGED_CARE'
    
    def _parse_aaa(self, segment: str, result: Dict):
        """Parse AAA segment for request validation errors"""
        parts = segment.split('*')
        result['raw_segments']['AAA'].append(segment)
        
        if len(parts) < 5:
            return
        
        error_code = parts[3] if len(parts) > 3 else ''
        error_desc = parts[4].rstrip('~') if len(parts) > 4 else ''
        
        error_info = {
            'code': error_code,
            'description': self.AAA_ERROR_CODES.get(error_code, error_desc)
        }
        
        result['errors'].append(error_info)
    
    def _parse_dtp(self, segment: str, result: Dict):
        """Parse DTP segment for date/time period information"""
        parts = segment.split('*')
        result['raw_segments']['DTP'].append(segment)
        
        if len(parts) < 4:
            return
        
        date_qualifier = parts[1]
        date_format = parts[2]
        date_value = parts[3].rstrip('~')
        
        # Common date qualifiers
        date_types = {
            '291': 'Plan Begin',
            '292': 'Plan End',
            '346': 'Plan Period',
            '347': 'Benefit Begin',
            '348': 'Benefit End',
            '349': 'Benefit Period',
            '356': 'Eligibility Begin',
            '357': 'Eligibility End'
        }
        
        if date_qualifier in date_types:
            result['plan_info'][date_types[date_qualifier]] = date_value
    
    def _parse_ref(self, segment: str, result: Dict):
        """Parse REF segment for reference information"""
        parts = segment.split('*')
        result['raw_segments']['REF'].append(segment)
        
        if len(parts) < 3:
            return
        
        ref_qualifier = parts[1]
        ref_value = parts[2].rstrip('~')
        
        # Common reference qualifiers
        ref_types = {
            '1L': 'Group Number',
            '18': 'Plan Number',
            '49': 'Family Unit Number',
            '6P': 'Group ID',
            'HJ': 'Identity Card Number',
            'IG': 'Insurance Policy Number',
            'N6': 'Plan Network ID',
            'SY': 'Social Security Number',
            'ZZ': 'Mutually Defined'
        }
        
        if ref_qualifier in ref_types:
            result['plan_info'][ref_types[ref_qualifier]] = ref_value
    
    def _parse_msg(self, segment: str, result: Dict):
        """Parse MSG segment for free-form messages"""
        parts = segment.split('*')
        if len(parts) > 1:
            message = parts[1].rstrip('~')
            result['warnings'].append(message)
    
    def _determine_ffs_status(self, result: Dict):
        """Determine if the patient qualifies for FFS based on all parsed data"""
        
        # Check if Utah Medicaid is the payer
        is_utah_medicaid = result.get('payer_info', {}).get('is_utah_medicaid', False)
        
        # Check for managed care indicators
        has_managed_care = result.get('managed_care_detected', False)
        
        # Check program type
        program = result.get('plan_info', {}).get('program', '')
        
        # Check for active eligibility
        has_active_coverage = any(
            detail.get('code') in ['1', '2', '3', '4', '5'] or 
            'Active' in detail.get('status', '')
            for detail in result.get('eligibility_details', [])
        )
        
        # Determine final FFS status
        if not has_active_coverage:
            result['ffs_status'] = 'NOT_ELIGIBLE'
            result['ffs_qualification'] = 'NOT_QUALIFIED'
        elif has_managed_care:
            result['ffs_status'] = 'MANAGED_CARE'
            result['ffs_qualification'] = 'ENROLLED_NOT_QUALIFIED'
        elif is_utah_medicaid and program in ['Targeted Adult Medicaid', 'Traditional Medicaid']:
            result['ffs_status'] = 'TRADITIONAL_FFS'
            result['ffs_qualification'] = 'QUALIFIED'
        elif is_utah_medicaid:
            # Utah Medicaid but program not specified - needs review
            result['ffs_status'] = 'FFS_UNKNOWN'
            result['ffs_qualification'] = 'NEEDS_REVIEW'
        else:
            result['ffs_status'] = 'NOT_UTAH_MEDICAID'
            result['ffs_qualification'] = 'NOT_QUALIFIED'
        
        # Add summary
        result['summary'] = self._generate_summary(result)
    
    def _generate_summary(self, result: Dict) -> str:
        """Generate a human-readable summary of eligibility status"""
        
        ffs_status = result.get('ffs_status', 'UNKNOWN')
        qualification = result.get('ffs_qualification', 'UNKNOWN')
        patient = result.get('patient_info', {})
        plan = result.get('plan_info', {})
        
        name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        
        if qualification == 'QUALIFIED':
            program = plan.get('program', 'Utah Medicaid FFS')
            return f"{name} is enrolled in {program} (Traditional FFS) - QUALIFIES for CM Program"
        elif qualification == 'ENROLLED_NOT_QUALIFIED':
            return f"{name} is enrolled in Managed Care Medicaid - DOES NOT QUALIFY for CM Program"
        elif qualification == 'NOT_QUALIFIED':
            if ffs_status == 'NOT_ELIGIBLE':
                return f"{name} is not currently eligible for Medicaid"
            else:
                return f"{name} does not have Utah Medicaid FFS coverage"
        elif qualification == 'NEEDS_REVIEW':
            return f"{name} has Utah Medicaid but program type needs manual review"
        else:
            return f"Unable to determine eligibility status for {name}"
    
    def format_response(self, parsed_result: Dict) -> str:
        """Format parsed response for display"""
        
        lines = []
        lines.append("\n" + "="*60)
        lines.append("X12 271 ELIGIBILITY RESPONSE ANALYSIS")
        lines.append("="*60)
        
        # Patient Information
        if parsed_result.get('patient_info'):
            patient = parsed_result['patient_info']
            lines.append("\nPATIENT INFORMATION:")
            lines.append(f"  Name: {patient.get('first_name', '')} {patient.get('last_name', '')}")
            if patient.get('member_id'):
                lines.append(f"  Member ID: {patient['member_id']}")
        
        # Payer Information
        if parsed_result.get('payer_info'):
            payer = parsed_result['payer_info']
            lines.append("\nPAYER INFORMATION:")
            lines.append(f"  Name: {payer.get('name', 'Unknown')}")
            if payer.get('id'):
                lines.append(f"  ID: {payer['id']}")
        
        # Eligibility Status
        lines.append("\nELIGIBILITY STATUS:")
        lines.append(f"  Overall Status: {'✅ ELIGIBLE' if parsed_result.get('eligible') else '❌ NOT ELIGIBLE'}")
        lines.append(f"  FFS Status: {parsed_result.get('ffs_status', 'UNKNOWN')}")
        lines.append(f"  CM Qualification: {parsed_result.get('ffs_qualification', 'UNKNOWN')}")
        
        # Eligibility Details
        if parsed_result.get('eligibility_details'):
            lines.append("\nELIGIBILITY DETAILS:")
            for detail in parsed_result['eligibility_details']:
                lines.append(f"  - {detail.get('status', 'Unknown')}")
                if detail.get('plan_description'):
                    lines.append(f"    Plan: {detail['plan_description']}")
                if detail.get('service_types'):
                    lines.append(f"    Services: {detail['service_types']}")
        
        # Errors
        if parsed_result.get('errors'):
            lines.append("\n⚠️ ERRORS:")
            for error in parsed_result['errors']:
                lines.append(f"  - {error.get('code', '')}: {error.get('description', 'Unknown error')}")
        
        # Summary
        lines.append("\nSUMMARY:")
        lines.append(f"  {parsed_result.get('summary', 'No summary available')}")
        
        lines.append("\n" + "="*60)
        
        return '\n'.join(lines)