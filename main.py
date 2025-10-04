"""
Main Orchestration Module for UHIN Utah Medicaid Eligibility Checking
Coordinates the X12 270 building, SOAP communication, and X12 271 parsing
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

from x12_builder import X12_270Builder
from soap_client import SOAPClient
from parser import X12_271Parser

# Load environment variables from .env.local
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UHINEligibilityChecker:
    """Main orchestrator for Utah Medicaid eligibility checking via UHIN"""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize the eligibility checker
        
        Args:
            config: Optional configuration dictionary. If not provided,
                   will attempt to load from environment variables
        """
        if config:
            self.config = config
        else:
            self.config = self._load_config_from_env()
        
        # Validate configuration
        self._validate_config()
        
        # Initialize components
        self.x12_builder = X12_270Builder(self.config)
        self.soap_client = SOAPClient(self.config)
        self.x12_parser = X12_271Parser()
        
        # Create output directory for logs/responses
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def _load_config_from_env(self) -> Dict[str, str]:
        """Load configuration from environment variables"""
        return {
            'endpoint': os.getenv('UHIN_ENDPOINT', 'https://ws.uhin.org/webservices/core/soaptype4.asmx'),
            'username': os.getenv('UHIN_USERNAME', ''),
            'password': os.getenv('UHIN_PASSWORD', ''),
            'trading_partner': os.getenv('UHIN_TRADING_PARTNER', 'HT009582-001'),
            'receiver_id': os.getenv('UHIN_RECEIVER_ID', 'HT000004-001'),  # Production Utah Medicaid
            'provider_npi': os.getenv('PROVIDER_NPI', ''),
            'provider_name': os.getenv('PROVIDER_NAME', 'PROVIDER'),
            'provider_first_name': os.getenv('PROVIDER_FIRST_NAME', '')
        }
    
    def _validate_config(self):
        """Validate required configuration fields"""
        required_fields = ['username', 'password', 'provider_npi']
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            logger.warning(f"Missing required configuration fields: {missing_fields}")
            logger.info("You can set these via environment variables or pass a config dictionary")
    
    def check_eligibility(self,
                         first_name: str,
                         last_name: str,
                         date_of_birth: str,
                         gender: Optional[str] = 'U',
                         member_id: Optional[str] = None,
                         test_mode: bool = False,
                         save_files: bool = True) -> Dict[str, any]:
        """
        Check patient eligibility for Utah Medicaid FFS
        
        Args:
            first_name: Patient's first name
            last_name: Patient's last name
            date_of_birth: Patient's date of birth (YYYY-MM-DD or YYYYMMDD)
            gender: Patient's gender (M/F/U)
            member_id: Optional Medicaid member ID
            test_mode: If True, uses test environment
            save_files: If True, saves X12 messages to files
            
        Returns:
            Dictionary containing:
                - success: Overall success status
                - qualified_for_cm: Whether patient qualifies for CM program
                - ffs_status: FFS status (TRADITIONAL_FFS, MANAGED_CARE, etc.)
                - eligibility_details: Detailed eligibility information
                - errors: Any errors encountered
                - files: Paths to saved files (if save_files=True)
        """
        result = {
            'success': False,
            'qualified_for_cm': False,
            'ffs_status': 'UNKNOWN',
            'eligibility_details': {},
            'errors': [],
            'files': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Update receiver ID for test mode
            if test_mode:
                self.config['receiver_id'] = 'HT000004-003'  # Utah Medicaid Test
                logger.info("Using TEST environment (HT000004-003)")
            else:
                self.config['receiver_id'] = 'HT000004-001'  # Utah Medicaid Production
                logger.info("Using PRODUCTION environment (HT000004-001)")
            
            # Step 1: Build X12 270 request
            logger.info(f"Building X12 270 for {first_name} {last_name}")
            x12_270 = self.x12_builder.build(
                patient_first_name=first_name,
                patient_last_name=last_name,
                patient_dob=date_of_birth,
                patient_gender=gender,
                member_id=member_id,
                test_mode=test_mode
            )
            
            # Validate the X12 270
            validation_result = self.x12_builder.validate(x12_270)
            if not validation_result['valid']:
                result['errors'].extend(validation_result['errors'])
                logger.error(f"X12 270 validation failed: {validation_result['errors']}")
                return result
            
            # Save X12 270 if requested
            if save_files:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                x270_filename = self.output_dir / f"x12_270_{last_name}_{first_name}_{timestamp}.txt"
                with open(x270_filename, 'w') as f:
                    f.write(x12_270)
                result['files']['x12_270'] = str(x270_filename)
                logger.info(f"Saved X12 270 to {x270_filename}")
            
            # Step 2: Send SOAP request
            logger.info("Sending SOAP request to UHIN...")
            soap_result = self.soap_client.check_eligibility(x12_270)
            
            if not soap_result['success']:
                result['errors'].append(soap_result.get('error', 'SOAP request failed'))
                if soap_result.get('soap_fault'):
                    result['soap_fault'] = soap_result['soap_fault']
                logger.error(f"SOAP request failed: {soap_result.get('error')}")
                return result
            
            # Save X12 271 response if received
            x12_271 = soap_result.get('x12_271')
            if x12_271 and save_files:
                x271_filename = self.output_dir / f"x12_271_{last_name}_{first_name}_{timestamp}.txt"
                with open(x271_filename, 'w') as f:
                    f.write(x12_271)
                result['files']['x12_271'] = str(x271_filename)
                logger.info(f"Saved X12 271 to {x271_filename}")
            
            # Step 3: Parse X12 271 response
            logger.info("Parsing X12 271 response...")
            parsed_result = self.x12_parser.parse(x12_271)
            
            # Update result with parsed data
            result['success'] = parsed_result.get('success', False)
            result['ffs_status'] = parsed_result.get('ffs_status', 'UNKNOWN')
            result['qualified_for_cm'] = parsed_result.get('ffs_qualification') == 'QUALIFIED'
            result['eligibility_details'] = parsed_result
            result['raw_271_response'] = x12_271  # Add raw response for detailed parsing
            
            # Add any parsing errors
            if parsed_result.get('errors'):
                result['errors'].extend([
                    f"{err.get('code', '')}: {err.get('description', '')}"
                    for err in parsed_result['errors']
                ])
            
            # Log summary
            logger.info(f"Eligibility check complete: {parsed_result.get('summary', 'No summary')}")
            
            # Save parsed result if requested
            if save_files:
                parsed_filename = self.output_dir / f"parsed_result_{last_name}_{first_name}_{timestamp}.json"
                with open(parsed_filename, 'w') as f:
                    json.dump(result, f, indent=2)
                result['files']['parsed_result'] = str(parsed_filename)
                logger.info(f"Saved parsed result to {parsed_filename}")
            
        except Exception as e:
            logger.error(f"Unexpected error during eligibility check: {str(e)}", exc_info=True)
            result['errors'].append(f"System error: {str(e)}")
        
        return result
    
    def check_eligibility_batch(self, patients: list, test_mode: bool = False) -> list:
        """
        Check eligibility for multiple patients
        
        Args:
            patients: List of patient dictionaries with first_name, last_name, date_of_birth
            test_mode: If True, uses test environment
            
        Returns:
            List of results for each patient
        """
        results = []
        
        for i, patient in enumerate(patients, 1):
            logger.info(f"Processing patient {i}/{len(patients)}: {patient.get('first_name')} {patient.get('last_name')}")
            
            result = self.check_eligibility(
                first_name=patient.get('first_name'),
                last_name=patient.get('last_name'),
                date_of_birth=patient.get('date_of_birth'),
                gender=patient.get('gender', 'U'),
                member_id=patient.get('member_id'),
                test_mode=test_mode
            )
            
            results.append({
                'patient': patient,
                'result': result
            })
        
        return results
    
    def format_result_summary(self, result: Dict) -> str:
        """Format a result dictionary as a readable summary"""
        
        lines = []
        lines.append("\n" + "="*60)
        lines.append("ELIGIBILITY CHECK RESULT SUMMARY")
        lines.append("="*60)
        
        lines.append(f"\nTimestamp: {result.get('timestamp', 'N/A')}")
        lines.append(f"Success: {'✅ YES' if result.get('success') else '❌ NO'}")
        
        if result.get('success'):
            lines.append(f"\nQualifies for CM Program: {'✅ YES' if result.get('qualified_for_cm') else '❌ NO'}")
            lines.append(f"FFS Status: {result.get('ffs_status', 'UNKNOWN')}")
            
            details = result.get('eligibility_details', {})
            if details.get('summary'):
                lines.append(f"\nSummary: {details['summary']}")
            
            if details.get('patient_info'):
                patient = details['patient_info']
                lines.append(f"\nPatient: {patient.get('first_name', '')} {patient.get('last_name', '')}")
                if patient.get('member_id'):
                    lines.append(f"Member ID: {patient['member_id']}")
            
            if details.get('payer_info'):
                payer = details['payer_info']
                lines.append(f"\nPayer: {payer.get('name', 'Unknown')}")
        
        if result.get('errors'):
            lines.append("\n⚠️ ERRORS:")
            for error in result['errors']:
                lines.append(f"  - {error}")
        
        if result.get('files'):
            lines.append("\n📁 SAVED FILES:")
            for file_type, path in result['files'].items():
                lines.append(f"  - {file_type}: {path}")
        
        lines.append("\n" + "="*60)
        
        return '\n'.join(lines)


def main():
    """Main entry point for command-line usage"""
    import argparse
    from getpass import getpass
    
    parser = argparse.ArgumentParser(description='Check Utah Medicaid eligibility via UHIN')
    parser.add_argument('--first-name', required=True, help='Patient first name')
    parser.add_argument('--last-name', required=True, help='Patient last name')
    parser.add_argument('--dob', required=True, help='Date of birth (YYYY-MM-DD)')
    parser.add_argument('--gender', default='U', choices=['M', 'F', 'U'], help='Gender')
    parser.add_argument('--member-id', help='Medicaid member ID (if known)')
    parser.add_argument('--test', action='store_true', help='Use test environment')
    parser.add_argument('--no-save', action='store_true', help='Do not save files')
    parser.add_argument('--username', help='UHIN username (or set UHIN_USERNAME env var)')
    parser.add_argument('--password', help='UHIN password (or set UHIN_PASSWORD env var)')
    parser.add_argument('--npi', help='Provider NPI (or set PROVIDER_NPI env var)')
    parser.add_argument('--provider-name', help='Provider name')
    
    args = parser.parse_args()
    
    # Build configuration
    config = {}
    
    # Get credentials
    if args.username:
        config['username'] = args.username
    elif not os.getenv('UHIN_USERNAME'):
        config['username'] = input('UHIN Username: ')
    
    if args.password:
        config['password'] = args.password
    elif not os.getenv('UHIN_PASSWORD'):
        config['password'] = getpass('UHIN Password: ')
    
    if args.npi:
        config['provider_npi'] = args.npi
    elif not os.getenv('PROVIDER_NPI'):
        config['provider_npi'] = input('Provider NPI: ')
    
    if args.provider_name:
        config['provider_name'] = args.provider_name
    
    # Create checker instance
    checker = UHINEligibilityChecker(config)
    
    # Check eligibility
    print(f"\nChecking eligibility for {args.first_name} {args.last_name}...")
    result = checker.check_eligibility(
        first_name=args.first_name,
        last_name=args.last_name,
        date_of_birth=args.dob,
        gender=args.gender,
        member_id=args.member_id,
        test_mode=args.test,
        save_files=not args.no_save
    )
    
    # Display result
    print(checker.format_result_summary(result))
    
    # Return appropriate exit code
    if result['success']:
        if result['qualified_for_cm']:
            print("\n✅ Patient QUALIFIES for Contingency Management program")
            return 0
        else:
            print("\n⚠️ Patient DOES NOT QUALIFY for Contingency Management program")
            return 1
    else:
        print("\n❌ Eligibility check failed")
        return 2


if __name__ == '__main__':
    exit(main())