"""
Payer Configuration Module for UHIN Eligibility Checking
Manages different payer configurations for X12 270/271 transactions
"""

from typing import Dict, Optional

class PayerConfig:
    """Configuration management for different insurance payers"""

    # Payer configurations
    PAYERS = {
        'UTAH_MEDICAID': {
            'name': 'Utah Medicaid FFS',
            'payer_id': 'HT000004-001',
            'payer_name': 'UTAH MEDICAID FFS',
            'payer_code': 'UTMCD',
            'receiver_id': 'HT000004-001',
            'description': 'Utah Medicaid Fee-for-Service (Traditional)',
            'eligibility_segments': ['30'],  # Medical coverage
            'supported_services': ['medical', 'behavioral_health'],
            'identifier_type': 'MI',  # Medicaid ID
            'requires_member_id': False,  # Can search by name/DOB
            'test_receiver_id': 'HT000004-003'
        },
        'U_OF_U_HEALTH': {
            'name': 'U of U Health Plans',
            'payer_id': 'SX155',
            'payer_name': 'U OF U HEALTH PLANS',
            'payer_code': 'SX155',
            'receiver_id': 'HT000179-002',  # U of U Health Plans Trading Partner Number
            'description': 'University of Utah Health Plans / HMHI-BHN',
            'eligibility_segments': ['30', '48', 'AL'],  # Medical, Hospital, Vision/Hearing
            'supported_services': ['medical', 'behavioral_health', 'hospital'],
            'identifier_type': 'MI',  # Member ID
            'requires_member_id': True,  # May require member ID
            'test_receiver_id': None  # No test environment known
        },
        'SELECTHEALTH': {
            'name': 'SelectHealth',
            'payer_id': 'SX062',
            'payer_name': 'SELECTHEALTH',
            'payer_code': 'SX062',
            'receiver_id': 'SX062',
            'description': 'SelectHealth (Intermountain Healthcare)',
            'eligibility_segments': ['30', '48'],
            'supported_services': ['medical', 'behavioral_health'],
            'identifier_type': 'MI',
            'requires_member_id': True,
            'test_receiver_id': None
        },
        'MOLINA': {
            'name': 'Molina Healthcare of Utah',
            'payer_id': 'MOLNA',
            'payer_name': 'MOLINA HEALTHCARE OF UTAH',
            'payer_code': 'MOLNA',
            'receiver_id': 'MOLNA',
            'description': 'Molina Healthcare Utah Medicaid',
            'eligibility_segments': ['30'],
            'supported_services': ['medical', 'behavioral_health'],
            'identifier_type': 'MI',
            'requires_member_id': False,
            'test_receiver_id': None
        },
        'ANTHEM_BCBS': {
            'name': 'Anthem Blue Cross Blue Shield',
            'payer_id': 'SX107',
            'payer_name': 'ANTHEM BCBS',
            'payer_code': 'SX107',
            'receiver_id': 'SX107',
            'description': 'Anthem BCBS Utah',
            'eligibility_segments': ['30', '48'],
            'supported_services': ['medical', 'behavioral_health'],
            'identifier_type': 'MI',
            'requires_member_id': True,
            'test_receiver_id': None
        }
    }

    @classmethod
    def get_payer(cls, payer_key: str) -> Optional[Dict]:
        """
        Get payer configuration by key

        Args:
            payer_key: Key identifying the payer (e.g., 'UTAH_MEDICAID', 'U_OF_U_HEALTH')

        Returns:
            Payer configuration dictionary or None if not found
        """
        return cls.PAYERS.get(payer_key.upper())

    @classmethod
    def get_payer_by_id(cls, payer_id: str) -> Optional[Dict]:
        """
        Get payer configuration by payer ID

        Args:
            payer_id: Payer ID (e.g., 'SX155', 'HT000004-001')

        Returns:
            Payer configuration dictionary or None if not found
        """
        for key, config in cls.PAYERS.items():
            if config['payer_id'] == payer_id or config.get('receiver_id') == payer_id:
                return config
        return None

    @classmethod
    def list_payers(cls) -> Dict[str, str]:
        """
        Get a list of all available payers

        Returns:
            Dictionary of payer keys to names
        """
        return {key: config['name'] for key, config in cls.PAYERS.items()}

    @classmethod
    def validate_payer_config(cls, payer_key: str) -> tuple[bool, str]:
        """
        Validate if a payer is configured and ready to use

        Args:
            payer_key: Key identifying the payer

        Returns:
            Tuple of (is_valid, message)
        """
        payer = cls.get_payer(payer_key)
        if not payer:
            return False, f"Payer '{payer_key}' not found in configuration"

        required_fields = ['payer_id', 'payer_name', 'receiver_id']
        missing = [f for f in required_fields if not payer.get(f)]

        if missing:
            return False, f"Payer '{payer_key}' missing required fields: {missing}"

        return True, f"Payer '{payer['name']}' is properly configured"

    @classmethod
    def format_x12_payer_name(cls, payer_key: str, test_mode: bool = False) -> tuple[str, str, str]:
        """
        Get X12-formatted payer information

        Args:
            payer_key: Key identifying the payer
            test_mode: Whether to use test receiver ID if available

        Returns:
            Tuple of (receiver_id, payer_name, payer_code)
        """
        payer = cls.get_payer(payer_key)
        if not payer:
            raise ValueError(f"Unknown payer: {payer_key}")

        receiver_id = payer.get('test_receiver_id') if test_mode else payer['receiver_id']
        if not receiver_id:
            receiver_id = payer['receiver_id']  # Fall back to production if no test ID

        return receiver_id, payer['payer_name'], payer.get('payer_code', payer['payer_id'])