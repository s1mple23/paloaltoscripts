"""
Input validation utilities - Fixed validation patterns
Updated to support 'both' action type for automatic dual search
"""
import re
from typing import List
from config import config

def validate_search_term(search_term: str) -> bool:
    """
    Validate search term
    
    Args:
        search_term: The search term to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not search_term:
        return False
    
    if len(search_term.strip()) < config.MIN_SEARCH_TERM_LENGTH:
        return False
    
    # Check for potentially dangerous characters
    dangerous_chars = ['<', '>', '&', '"', "'", ';', '--']
    if any(char in search_term for char in dangerous_chars):
        return False
    
    return True

def validate_action_type(action_type: str) -> bool:
    """
    Validate action type - Updated to support 'both' for automatic dual search
    
    Args:
        action_type: The action type to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Extended valid actions to include 'both' for automatic dual search
    extended_valid_actions = config.VALID_ACTIONS + ['both']
    return action_type in extended_valid_actions

def validate_ticket_id(ticket_id: str) -> bool:
    """
    Validate ticket ID format - More flexible pattern
    
    Args:
        ticket_id: The ticket ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not ticket_id:
        return False
    
    # More flexible pattern - allow most characters except dangerous ones
    # Allow: letters, numbers, hyphens, underscores, dots, slashes, colons
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '`', '|', '\\', '*', '?']
    if any(char in ticket_id for char in dangerous_chars):
        return False
    
    if len(ticket_id) < 3 or len(ticket_id) > 100:  # Increased max length
        return False
    
    return True

def validate_urls(urls: List[str]) -> tuple[bool, List[str]]:
    """
    Validate list of URLs
    
    Args:
        urls: List of URLs to validate
        
    Returns:
        Tuple of (all_valid, invalid_urls)
    """
    if not urls:
        return False, ["URLs list is empty"]
    
    invalid_urls = []
    
    for url in urls:
        if not validate_single_url(url):
            invalid_urls.append(url)
    
    return len(invalid_urls) == 0, invalid_urls

def validate_single_url(url: str) -> bool:
    """
    Validate a single URL/domain - More flexible validation
    
    Args:
        url: The URL/domain to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    url = url.strip()
    
    if len(url) < config.MIN_DOMAIN_LENGTH:
        return False
    
    if len(url) > config.MAX_URL_LENGTH:
        return False
    
    # Check for dangerous characters
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '`', '|', '\\']
    if any(char in url for char in dangerous_chars):
        return False
    
    # More flexible domain/URL pattern validation
    # Allow domains with or without protocol, with wildcards, with paths
    clean_url = url
    if clean_url.startswith(('http://', 'https://')):
        clean_url = clean_url.split('://', 1)[1]
    
    # Basic checks for valid domain structure
    if clean_url.startswith('*.'):
        clean_url = clean_url[2:]  # Remove wildcard
    
    # Must contain at least one dot for TLD
    if '.' not in clean_url:
        return False
    
    # Split by slash to get domain part
    domain_part = clean_url.split('/')[0]
    
    # Basic domain validation - allow most characters
    if not domain_part or domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    
    # Check for consecutive dots
    if '..' in domain_part:
        return False
    
    return True

def validate_hostname(hostname: str) -> bool:
    """
    Validate firewall hostname/IP - More flexible
    
    Args:
        hostname: The hostname or IP to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not hostname:
        return False
    
    hostname = hostname.strip()
    
    if len(hostname) < 3 or len(hostname) > 255:
        return False
    
    # Check for dangerous characters
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '`', '|', '\\', ' ']
    if any(char in hostname for char in dangerous_chars):
        return False
    
    # Check if it's an IP address
    ip_parts = hostname.split('.')
    if len(ip_parts) == 4 and all(part.isdigit() for part in ip_parts):
        # Validate IP ranges
        for part in ip_parts:
            if not (0 <= int(part) <= 255):
                return False
        return True
    
    # Check if it's a hostname - more flexible pattern
    # Allow letters, numbers, dots, hyphens
    if not re.match(r'^[a-zA-Z0-9.-]+$', hostname):
        return False
    
    # Must not start or end with dot or hyphen
    if hostname.startswith(('.', '-')) or hostname.endswith(('.', '-')):
        return False
    
    return True

def validate_credentials(username: str, password: str) -> tuple[bool, str]:
    """
    Validate login credentials - More flexible
    
    Args:
        username: Username to validate
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "Username is required"
    
    if not password:
        return False, "Password is required"
    
    username = username.strip()
    
    if len(username) < 1 or len(username) > 100:  # More flexible length
        return False, "Username must be between 1 and 100 characters"
    
    if len(password) < 1:
        return False, "Password cannot be empty"
    
    # Check for dangerous characters in username only
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '`', '|', '\\']
    if any(char in username for char in dangerous_chars):
        return False, "Username contains invalid characters"
    
    return True, ""

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file creation
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unknown"
    
    # Remove or replace dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    # Ensure it's not empty after sanitization
    if not sanitized.strip():
        sanitized = "unknown"
    
    return sanitized.strip()

def validate_category_name(category_name: str) -> bool:
    """
    Validate URL category name
    
    Args:
        category_name: The category name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not category_name:
        return False
    
    category_name = category_name.strip()
    
    if len(category_name) < 1 or len(category_name) > 200:
        return False
    
    # Allow most characters except dangerous ones
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '`', '|', '\\']
    if any(char in category_name for char in dangerous_chars):
        return False
    
    return True