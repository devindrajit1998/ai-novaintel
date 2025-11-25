"""
Utility functions for proposal processing.
"""
from typing import Dict, Any, Optional


def replace_company_placeholders(text: str, company_name: Optional[str] = None) -> str:
    """
    Replace company name placeholders in text with actual company name.
    
    Args:
        text: Text that may contain placeholders
        company_name: Company name to replace placeholders with
    
    Returns:
        Text with placeholders replaced, or original text if company_name is None/empty
    """
    if not text or not isinstance(text, str):
        return text
    
    if not company_name or not company_name.strip():
        return text
    
    # List of placeholder patterns to replace (case-insensitive)
    placeholders = [
        "[company name]",
        "[your company name]",
        "[COMPANY_NAME]",
        "[COMPANY NAME]",
        "[Company Name]",
        "{company_name}",
        "{company name}",
        "{COMPANY_NAME}",
        "{{company_name}}",
        "{{company name}}",
    ]
    
    result = text
    for placeholder in placeholders:
        # Case-insensitive replacement
        import re
        pattern = re.escape(placeholder)
        result = re.sub(pattern, company_name, result, flags=re.IGNORECASE)
    
    return result


def replace_placeholders_in_proposal_draft(
    proposal_draft: Dict[str, Any], 
    company_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Replace company name placeholders in all string fields of a proposal draft.
    
    Args:
        proposal_draft: Proposal draft dictionary
        company_name: Company name to replace placeholders with
    
    Returns:
        Proposal draft with placeholders replaced
    """
    if not proposal_draft or not isinstance(proposal_draft, dict):
        return proposal_draft
    
    if not company_name or not company_name.strip():
        return proposal_draft
    
    # Create a copy to avoid modifying the original
    result = {}
    
    for key, value in proposal_draft.items():
        if isinstance(value, str):
            result[key] = replace_company_placeholders(value, company_name)
        elif isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = replace_placeholders_in_proposal_draft(value, company_name)
        elif isinstance(value, list):
            # Process list items if they're strings
            result[key] = [
                replace_company_placeholders(item, company_name) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result

