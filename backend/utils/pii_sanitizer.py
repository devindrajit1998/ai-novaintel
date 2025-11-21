"""
PII (Personally Identifiable Information) Sanitization Utility.
Removes or masks sensitive information before sending to AI models.
"""
import re
from typing import Dict, Any, List

class PIISanitizer:
    """Sanitize PII from text before sending to AI models."""
    
    # Common email pattern
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    # Phone number patterns (various formats)
    PHONE_PATTERNS = [
        re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),  # US format
        re.compile(r'\b\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'),  # International
        re.compile(r'\b\d{10}\b'),  # 10 digits
    ]
    
    # Credit card pattern (basic)
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
    
    # SSN pattern (US)
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    
    # IP address pattern
    IP_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    
    @classmethod
    def sanitize_text(cls, text: str, mask_char: str = "*") -> str:
        """
        Sanitize PII from text by replacing with masked values.
        
        Args:
            text: Input text to sanitize
            mask_char: Character to use for masking
        
        Returns:
            Sanitized text
        """
        if not text:
            return text
        
        sanitized = text
        
        # Replace emails
        sanitized = cls.EMAIL_PATTERN.sub(f'{mask_char * 5}@example.com', sanitized)
        
        # Replace phone numbers
        for pattern in cls.PHONE_PATTERNS:
            sanitized = pattern.sub(f'{mask_char * 10}', sanitized)
        
        # Replace credit cards
        sanitized = cls.CREDIT_CARD_PATTERN.sub(f'{mask_char * 16}', sanitized)
        
        # Replace SSN
        sanitized = cls.SSN_PATTERN.sub(f'{mask_char * 3}-{mask_char * 2}-{mask_char * 4}', sanitized)
        
        # Replace IP addresses
        sanitized = cls.IP_PATTERN.sub(f'{mask_char * 3}.{mask_char * 3}.{mask_char * 3}.{mask_char * 3}', sanitized)
        
        return sanitized
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], mask_char: str = "*") -> Dict[str, Any]:
        """
        Recursively sanitize PII from dictionary values.
        
        Args:
            data: Dictionary to sanitize
            mask_char: Character to use for masking
        
        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_text(value, mask_char)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value, mask_char)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_dict(item, mask_char) if isinstance(item, dict)
                    else cls.sanitize_text(item, mask_char) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @classmethod
    def sanitize_insights(cls, insights: Dict[str, Any], mask_char: str = "*") -> Dict[str, Any]:
        """
        Sanitize insights data before sending to AI.
        
        Args:
            insights: Insights dictionary
            mask_char: Character to use for masking
        
        Returns:
            Sanitized insights
        """
        return cls.sanitize_dict(insights, mask_char)

