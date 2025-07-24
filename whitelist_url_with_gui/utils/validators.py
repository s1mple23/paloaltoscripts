"""
Input validation utilities
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
    dangerous_chars = ['<', '>', '&', '"', "'", ';', '()', '--']
    if any(char in search_term for char in dangerous_chars):
        return False
    
    return True

def validate_action_type(action_type: str) -> bool:
    """
    Validate action type
    
    Args:
        action_type: The action type to validate
        
    Returns:
        True if valid, False otherwise
    """
    return action_type in config.VALID_ACTIONS

def validate_ticket_id(ticket_id: str) -> bool:
    """
    Validate ticket ID format
    
    Args:
        ticket_id: The ticket ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not ticket_id:
        return False
    
    # Allow alphanumeric, hyphens, underscores, and dots
    pattern = r'^[A-Za-z0-9\-_.]+$'
    if not re.match(pattern, ticket_id):
        return False
    
    if len(ticket_id) < 3 or len(ticket_id) > 50:
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
    Validate a single URL/domain
    
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
    
    # Basic domain/URL pattern validation
    # Allow domains with or without protocol, with wildcards
    pattern = r'^(\*\.)?([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(/.*)?$'
    
    # Remove common protocols for validation
    clean_url = url
    if clean_url.startswith(('http://', 'https://')):
        clean_url = clean_url.split('://', 1)[1]
    
    if not re.match(pattern, clean_url):
        return False
    
    return True

def validate_hostname(hostname: str) -> bool:
    """
    Validate firewall hostname/IP
    
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
    
    # Check if it's an IP address
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ip_pattern, hostname):
        # Validate IP ranges
        parts = hostname.split('.')
        for part in parts:
            if not (0 <= int(part) <= 255):
                return False
        return True
    
    # Check if it's a hostname
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return re.match(hostname_pattern, hostname) is not None

def validate_credentials(username: str, password: str) -> tuple[bool, str]:
    """
    Validate login credentials
    
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
    
    if len(username) < 2 or len(username) > 50:
        return False, "Username must be between 2 and 50 characters"
    
    if len(password) < 1:
        return False, "Password cannot be empty"
    
    # Check for basic username format (alphanumeric, dots, hyphens, underscores)
    username_pattern = r'^[a-zA-Z0-9._-]+$'
    if not re.match(username_pattern, username):
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