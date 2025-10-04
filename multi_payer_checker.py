"""
Multi-Payer Eligibility Checker for UHIN
Supports multiple insurance payers including Utah Medicaid and U of U Health Plans
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from dotenv import load_dotenv

from x12_builder_multi import X12_270BuilderMulti
from soap_client import SOAPClient
from parser import X12_271Parser
from payer_config import PayerConfig

# Load environment variables from .env.local
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiPayerEligibilityChecker:
    """Eligibility checker supporting multiple insurance payers via UHIN"""

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize the multi-payer eligibility checker

        Args:
            config: Optional configuration dictionary
        """
        if config:
            self.config = config
        else:
            self.config = self._load_config_from_env()

        # Validate configuration
        self._validate_config()

        # Initialize X12 parser (shared across all payers)
        self.x12_parser = X12_271Parser()

        # Create output directory for logs/responses
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

        logger.info("Multi-payer eligibility checker initialized")
        logger.info(f"Available payers: {list(PayerConfig.list_payers().values())}")

    def _load_config_from_env(self) -> Dict[str, str]:
        """Load configuration from environment variables"""
        return {
            'endpoint': os.getenv('UHIN_ENDPOINT', 'https://ws.uhin.org/webservices/core/soaptype4.asmx'),
            'username': os.getenv('UHIN_USERNAME', ''),
            'password': os.getenv('UHIN_PASSWORD', ''),
            'trading_partner': os.getenv('UHIN_TRADING_PARTNER', 'HT009582-001'),
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

    def check_eligibility(self,
                         payer_key: str,
                         first_name: str,
                         last_name: str,
                         date_of_birth: str,
                         gender: Optional[str] = 'M',
                         member_id: Optional[str] = None,
                         test_mode: bool = False,
                         save_files: bool = True) -> Dict[str, any]:
        """
        Check patient eligibility with specified payer

        Args:
            payer_key: Payer identifier (e.g., 'UTAH_MEDICAID', 'U_OF_U_HEALTH')
            first_name: Patient's first name
            last_name: Patient's last name
            date_of_birth: Patient's date of birth (YYYY-MM-DD)
            gender: Patient's gender (M/F, defaults to M)
            member_id: Optional member ID
            test_mode: If True, uses test environment
            save_files: If True, saves X12 messages to files

        Returns:
            Dictionary containing eligibility response
        """
        try:
            # Get payer configuration
            payer = PayerConfig.get_payer(payer_key)
            if not payer:
                return {
                    'success': False,
                    'error': f'Unknown payer: {payer_key}',
                    'available_payers': PayerConfig.list_payers()
                }

            logger.info(f"Checking eligibility with {payer['name']} (ID: {payer['payer_id']})")

            # Check if member ID is required
            if payer['requires_member_id'] and not member_id:
                logger.warning(f"{payer['name']} typically requires a member ID - results may be limited")

            # Get payer-specific configuration
            receiver_id, payer_name, payer_code = PayerConfig.format_x12_payer_name(
                payer_key, test_mode
            )

            # Update config with payer-specific values
            payer_config = self.config.copy()
            payer_config['receiver_id'] = receiver_id
            payer_config['payer_name'] = payer_name
            payer_config['payer_code'] = payer_code

            # Create SOAP client with payer-specific config
            soap_client = SOAPClient(payer_config)

            # Build X12 270 message with payer-specific config
            x12_builder = X12_270BuilderMulti(payer_config)

            # Format dates
            dob = self._format_date(date_of_birth)
            if not dob:
                return {
                    'success': False,
                    'error': f'Invalid date format: {date_of_birth}. Use YYYY-MM-DD'
                }

            # Build the X12 270 message
            x12_message = x12_builder.build(
                patient_first_name=first_name,
                patient_last_name=last_name,
                patient_dob=dob.strftime('%Y%m%d'),
                patient_gender=gender if gender in ['M', 'F'] else 'M',
                member_id=member_id,
                eligibility_segments=payer.get('eligibility_segments', ['30'])
            )

            # Save request if requested
            if save_files:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                request_file = self.output_dir / f"x12_270_{payer_key}_{last_name}_{timestamp}.txt"
                request_file.write_text(x12_message)
                logger.info(f"Saved X12 270 request to: {request_file}")

            # Send to UHIN via SOAP
            logger.info(f"Sending eligibility request to UHIN for {payer['name']}")
            success, message, x12_response = soap_client.send_request(x12_message)

            logger.debug(f"SOAP Response - Success: {success}, Message: {message}, Has X12: {bool(x12_response)}")

            # Check if request was successful
            if not success:
                return {
                    'success': False,
                    'error': message,
                    'payer': payer['name']
                }

            # Save response if requested
            if save_files and x12_response:
                response_file = self.output_dir / f"x12_271_{payer_key}_{last_name}_{timestamp}.txt"
                response_file.write_text(x12_response)
                logger.info(f"Saved X12 271 response to: {response_file}")

            # Parse the X12 271 response
            if x12_response:
                result = self.x12_parser.parse(x12_response)
                result['payer'] = payer['name']
                result['payer_id'] = payer['payer_id']

                # Add payer-specific interpretation
                result['interpretation'] = self._interpret_eligibility(result, payer_key)

                return result
            else:
                return {
                    'success': False,
                    'error': 'No response received from UHIN',
                    'payer': payer['name']
                }

        except Exception as e:
            logger.error(f"Error checking eligibility: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'payer': payer_key
            }

    def _format_date(self, date_str: str) -> Optional[datetime]:
        """Convert date string to datetime object"""
        date_formats = ['%Y-%m-%d', '%Y%m%d', '%m/%d/%Y']
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def _interpret_eligibility(self, result: Dict, payer_key: str) -> Dict:
        """
        Interpret eligibility response based on payer

        Args:
            result: Parsed X12 271 response
            payer_key: Payer identifier

        Returns:
            Interpretation dictionary
        """
        interpretation = {
            'is_eligible': False,
            'coverage_type': 'Unknown',
            'notes': []
        }

        if result.get('eligible'):
            interpretation['is_eligible'] = True

            # Get patient info
            patient_info = result.get('patient_info', {})

            if payer_key == 'UTAH_MEDICAID':
                # Check for FFS vs managed care
                plan_info = patient_info.get('plan_sponsor', '')
                if 'TARGETED ADULT' in plan_info.upper() or 'TRADITIONAL' in plan_info.upper():
                    interpretation['coverage_type'] = 'Traditional FFS Medicaid'
                    interpretation['notes'].append('Qualifies for contingency management program')
                elif any(mco in plan_info.upper() for mco in ['MOLINA', 'SELECTHEALTH', 'ANTHEM']):
                    interpretation['coverage_type'] = 'Managed Care Medicaid'
                    interpretation['notes'].append('Does NOT qualify for CM program - managed care')
                else:
                    interpretation['coverage_type'] = 'Medicaid (type unclear)'

            elif payer_key == 'U_OF_U_HEALTH':
                interpretation['coverage_type'] = 'U of U Health Plans'
                if patient_info.get('member_id'):
                    interpretation['notes'].append(f"Member ID: {patient_info['member_id']}")

                # Check for specific benefit types
                benefits = result.get('benefits', [])
                if benefits:
                    covered_services = [b.get('service_type') for b in benefits if b.get('covered')]
                    if covered_services:
                        interpretation['notes'].append(f"Covered services: {', '.join(covered_services)}")

            else:
                interpretation['coverage_type'] = f'{PayerConfig.get_payer(payer_key)["name"]} Coverage'

        return interpretation

    def check_multiple_payers(self,
                            first_name: str,
                            last_name: str,
                            date_of_birth: str,
                            payers: Optional[List[str]] = None,
                            gender: Optional[str] = 'M',
                            member_id: Optional[str] = None) -> Dict[str, Dict]:
        """
        Check eligibility with multiple payers

        Args:
            first_name: Patient's first name
            last_name: Patient's last name
            date_of_birth: Patient's date of birth
            payers: List of payer keys to check (default: all)
            gender: Patient's gender
            member_id: Optional member ID

        Returns:
            Dictionary of payer results
        """
        if not payers:
            payers = list(PayerConfig.list_payers().keys())

        results = {}
        for payer_key in payers:
            logger.info(f"Checking eligibility with {payer_key}")
            result = self.check_eligibility(
                payer_key=payer_key,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=gender,
                member_id=member_id,
                save_files=True
            )
            results[payer_key] = result

            # Add summary
            if result.get('success'):
                interp = result.get('interpretation', {})
                logger.info(f"{payer_key}: {interp.get('coverage_type', 'Unknown')} - "
                          f"Eligible: {interp.get('is_eligible', False)}")

        return results


def main():
    """Test multi-payer eligibility checking"""
    checker = MultiPayerEligibilityChecker()

    # Test with Jeremy Montoya
    print("\n" + "="*60)
    print("Testing Multi-Payer Eligibility Checking")
    print("="*60)

    # First try Utah Medicaid (known to work)
    print("\n1. Testing with Utah Medicaid (baseline)...")
    result = checker.check_eligibility(
        payer_key='UTAH_MEDICAID',
        first_name='Jeremy',
        last_name='Montoya',
        date_of_birth='1984-07-17',
        gender='M'
    )

    if result.get('success'):
        print(f"✅ Utah Medicaid: {result.get('patient_info', {}).get('first_name')} {result.get('patient_info', {}).get('last_name')}")
        interp = result.get('interpretation', {})
        print(f"   Coverage: {interp.get('coverage_type')}")
        print(f"   Eligible: {interp.get('is_eligible')}")
    else:
        print(f"❌ Utah Medicaid: {result.get('error')}")

    # Now try U of U Health Plans
    print("\n2. Testing with U of U Health Plans...")
    result = checker.check_eligibility(
        payer_key='U_OF_U_HEALTH',
        first_name='Jeremy',
        last_name='Montoya',
        date_of_birth='1984-07-17',
        gender='M'
    )

    if result.get('success'):
        print(f"✅ U of U Health: Response received")
        print(f"   Patient: {result.get('patient_info', {})}")
        interp = result.get('interpretation', {})
        print(f"   Coverage: {interp.get('coverage_type')}")
        print(f"   Eligible: {interp.get('is_eligible')}")
        if interp.get('notes'):
            print(f"   Notes: {interp['notes']}")
    else:
        print(f"❌ U of U Health: {result.get('error')}")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()