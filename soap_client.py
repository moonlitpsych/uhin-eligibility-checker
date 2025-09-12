"""
SOAP Client for UHIN UTRANSEND Clearinghouse
Handles SOAP envelope creation with WS-Security and HTTP communication
"""

import requests
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple
import xml.etree.ElementTree as ET
import logging
from xml.sax.saxutils import escape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SOAPClient:
    """Handles SOAP communication with UHIN UTRANSEND clearinghouse"""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize the SOAP client
        
        Args:
            config: Dictionary containing:
                - endpoint: UHIN SOAP endpoint URL
                - username: UHIN username
                - password: UHIN password
                - trading_partner: Trading partner ID
                - receiver_id: Receiver ID
        """
        self.config = config
        self.endpoint = config.get('endpoint', 'https://ws.uhin.org/webservices/core/soaptype4.asmx')
        self.session = requests.Session()
        
    def generate_uuid(self) -> str:
        """Generate a UUID v4 string (36 characters as required by UHIN)"""
        return str(uuid.uuid4())
    
    def generate_wsu_id(self) -> str:
        """Generate a unique WSU ID for UsernameToken"""
        return f"UsernameToken-{uuid.uuid4().hex[:8]}"
    
    def create_soap_envelope(self, x12_payload: str) -> str:
        """
        Create SOAP envelope with WS-Security headers
        
        Args:
            x12_payload: The X12 270 message to wrap
            
        Returns:
            Complete SOAP envelope as string
        """
        # UHIN timestamp format with milliseconds
        now = datetime.utcnow()
        timestamp = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'  # 3 decimal places for milliseconds
        
        # PayloadID must be exactly 36 characters - pad the control number
        control_number = str(int(now.timestamp()))[-9:]
        # Format: EHR_UHIN_[9 digits]_[date] then pad to 36 chars
        base_id = f"EHR_UHIN_{control_number}_{now.strftime('%Y%m%d')}"
        payload_id = base_id.ljust(36, '0')  # Pad with zeros to reach 36 chars
        
        # WSU ID format matching UHIN guide
        wsu_id = f"UsernameToken-{control_number[:8]}"
        
        # Escape the X12 payload for XML
        escaped_payload = escape(x12_payload)
        
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" 
               xmlns:cor="http://www.caqh.org/SOAP/WSDL/CORERule2.2.0.xsd">
    <soap:Header>
        <wsse:Security soap:mustUnderstand="true" 
                       xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
                       xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
            <wsse:UsernameToken wsu:Id="{wsu_id}">
                <wsse:Username>{self.config['username']}</wsse:Username>
                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{self.config['password']}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <cor:COREEnvelopeRealTimeRequest>
            <PayloadType>X12_270_Request_005010X279A1</PayloadType>
            <ProcessingMode>RealTime</ProcessingMode>
            <PayloadID>{payload_id}</PayloadID>
            <TimeStamp>{timestamp}</TimeStamp>
            <SenderID>{self.config['trading_partner']}</SenderID>
            <ReceiverID>{self.config['receiver_id']}</ReceiverID>
            <CORERuleVersion>2.2.0</CORERuleVersion>
            <Payload>{escaped_payload}</Payload>
        </cor:COREEnvelopeRealTimeRequest>
    </soap:Body>
</soap:Envelope>"""
        
        return soap_envelope
    
    def send_request(self, x12_payload: str, timeout: int = 30) -> Tuple[bool, str, Optional[str]]:
        """
        Send SOAP request to UHIN
        
        Args:
            x12_payload: The X12 270 message
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (success, response_text, error_message)
        """
        try:
            soap_envelope = self.create_soap_envelope(x12_payload)
            
            logger.info(f"Sending request to {self.endpoint}")
            logger.debug(f"SOAP envelope size: {len(soap_envelope)} bytes")
            
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': 'http://www.caqh.org/SOAP/WSDL/CORERule2.2.0.xsd/COREEnvelopeRealTimeRequest',
                'Accept': 'application/soap+xml, text/xml',
                'User-Agent': 'UHIN-Python-Client/1.0'
            }
            
            response = self.session.post(
                self.endpoint,
                data=soap_envelope.encode('utf-8'),
                headers=headers,
                timeout=timeout
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                return True, response.text, None
            else:
                error_msg = f"HTTP {response.status_code}: {response.reason}"
                logger.error(error_msg)
                return False, response.text, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after {timeout} seconds"
            logger.error(error_msg)
            return False, "", error_msg
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, "", error_msg
    
    def extract_x12_response(self, soap_response: str) -> Optional[str]:
        """
        Extract X12 271 response from SOAP envelope
        
        Args:
            soap_response: Complete SOAP response
            
        Returns:
            X12 271 message or None if not found
        """
        try:
            # Try regex extraction first (more forgiving)
            import re
            payload_match = re.search(r'<Payload[^>]*>(.*?)</Payload>', soap_response, re.DOTALL)
            if payload_match:
                x12_response = payload_match.group(1).strip()
                # Unescape XML entities
                x12_response = x12_response.replace('&lt;', '<')
                x12_response = x12_response.replace('&gt;', '>')
                x12_response = x12_response.replace('&amp;', '&')
                x12_response = x12_response.replace('&quot;', '"')
                x12_response = x12_response.replace('&apos;', "'")
                return x12_response
            
            # Fallback to XML parsing if regex fails
            # Remove namespace prefixes for easier parsing
            soap_clean = soap_response
            for ns in ['soap:', 'cor:', 'wsse:', 'wsu:']:
                soap_clean = soap_clean.replace(f'<{ns}', '<').replace(f'</{ns}', '</')
            
            root = ET.fromstring(soap_clean)
            
            # Find Payload element
            payload_elem = root.find('.//Payload')
            if payload_elem is not None and payload_elem.text:
                return payload_elem.text.strip()
            
            logger.warning("No Payload element found in SOAP response")
            return None
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error extracting X12 response: {str(e)}")
            return None
    
    def extract_error_info(self, soap_response: str) -> Optional[Dict[str, str]]:
        """
        Extract error information from SOAP fault response
        
        Args:
            soap_response: SOAP response that may contain fault
            
        Returns:
            Dictionary with error details or None
        """
        try:
            import re
            
            # Look for SOAP Fault
            fault_match = re.search(r'<.*?Fault>(.*?)</.*?Fault>', soap_response, re.DOTALL)
            if fault_match:
                fault_content = fault_match.group(1)
                
                error_info = {}
                
                # Extract fault code
                code_match = re.search(r'<.*?Code>(.*?)</.*?Code>', fault_content)
                if code_match:
                    error_info['code'] = code_match.group(1).strip()
                
                # Extract fault reason/string
                reason_match = re.search(r'<.*?(?:Reason|String)>(.*?)</.*?(?:Reason|String)>', fault_content)
                if reason_match:
                    error_info['reason'] = reason_match.group(1).strip()
                
                # Extract detail
                detail_match = re.search(r'<.*?Detail>(.*?)</.*?Detail>', fault_content)
                if detail_match:
                    error_info['detail'] = detail_match.group(1).strip()
                
                return error_info if error_info else None
            
            # Look for ErrorCode and ErrorMessage in response
            error_code_match = re.search(r'<ErrorCode>(.*?)</ErrorCode>', soap_response)
            error_msg_match = re.search(r'<ErrorMessage>(.*?)</ErrorMessage>', soap_response)
            
            if error_code_match or error_msg_match:
                return {
                    'code': error_code_match.group(1) if error_code_match else 'Unknown',
                    'message': error_msg_match.group(1) if error_msg_match else 'Unknown error'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting error info: {str(e)}")
            return None
    
    def check_eligibility(self, x12_270: str) -> Dict[str, any]:
        """
        High-level method to check eligibility
        
        Args:
            x12_270: Complete X12 270 message
            
        Returns:
            Dictionary with results including success status, X12 271 response, and any errors
        """
        result = {
            'success': False,
            'x12_271': None,
            'error': None,
            'soap_fault': None,
            'raw_response': None
        }
        
        # Send the request
        success, response_text, error = self.send_request(x12_270)
        result['raw_response'] = response_text
        
        if not success:
            result['error'] = error
            
            # Try to extract SOAP fault details
            if response_text:
                fault_info = self.extract_error_info(response_text)
                if fault_info:
                    result['soap_fault'] = fault_info
            
            return result
        
        # Extract X12 271 response
        x12_271 = self.extract_x12_response(response_text)
        
        if x12_271:
            result['success'] = True
            result['x12_271'] = x12_271
        else:
            result['error'] = "Could not extract X12 271 response from SOAP envelope"
            
            # Check for SOAP fault
            fault_info = self.extract_error_info(response_text)
            if fault_info:
                result['soap_fault'] = fault_info
        
        return result