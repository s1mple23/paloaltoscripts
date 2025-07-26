"""
Enhanced Configuration settings for Palo Alto Whitelist Tool
Now supports multi-URL search and manual input features
"""
import os
from datetime import timedelta

class Config:
    """Enhanced application configuration"""
    
    # Application Info
    APP_NAME = "Palo Alto Firewall URL Whitelisting Tool"
    VERSION = "1.4.0"
    DESCRIPTION = "Enhanced Multi-URL Search with Manual Input"
    
    # Flask Configuration
    SECRET_KEY = os.urandom(24)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # SSL Configuration
    SSL_CERT_FILE = 'cert.pem'
    SSL_KEY_FILE = 'key.pem'
    
    # Server Configuration
    HOST = '127.0.0.1'
    PORT = 5010
    DEBUG = False
    
    # Logging Configuration
    LOG_DIR = 'logs'
    APP_LOG_FILE = os.path.join(LOG_DIR, 'palo_alto_whitelist.log')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Enhanced Search Configuration
    DEFAULT_MAX_RESULTS = 3000
    LOOKBACK_MONTHS = 3
    SEARCH_TIMEOUT_ATTEMPTS = [10, 15, 25, 35]  # seconds
    ATTEMPT_WAIT_TIME = 3  # seconds between attempts
    
    # Multi-URL Search Configuration
    MAX_SEARCH_TERMS = 10  # Maximum number of search terms allowed
    SEARCH_TERM_SEPARATOR = ','  # Separator for multiple search terms
    MIN_SEARCH_TERM_LENGTH_MULTI = 2  # Minimum length for each term in multi-search
    
    # Manual URL Configuration
    MAX_MANUAL_URLS = 50  # Maximum number of manually entered URLs
    MANUAL_URL_SEPARATORS = [',', '\n', '\r\n']  # Separators for manual URL input
    ALLOW_WILDCARD_MANUAL = True  # Allow wildcard domains in manual input
    
    # Commit Configuration - INCREASED POLLING
    COMMIT_MAX_POLLS = 25  # Increased from 10 to 25
    COMMIT_POLL_INTERVAL = 6  # seconds
    COMMIT_TIMEOUT = 180  # Increased from 60 to 180 seconds
    
    # Enhanced URL Validation
    MIN_SEARCH_TERM_LENGTH = 2
    MIN_DOMAIN_LENGTH = 3
    MAX_URL_LENGTH = 500
    MAX_MANUAL_URL_LENGTH = 200  # Specific limit for manually entered URLs
    
    # API Configuration
    API_TIMEOUT = 30  # seconds
    JOB_CHECK_INTERVAL = 2  # seconds
    STATUS_CHECK_TIMEOUT = 10  # seconds
    
    # Valid Actions
    VALID_ACTIONS = ['block-url', 'block-continue']
    
    # URL Sources (fields to check in log entries)
    URL_SOURCES = ['misc', 'url', 'src-location', 'dst-location', 'hostname', 'host']
    
    # URL Separators (for splitting multiple URLs in one field)
    URL_SEPARATORS = [' ', '\t', '\n', '&r=', '&gdpr_consent=', '?r=']
    
    # Enhanced Query Building
    USE_OR_LOGIC_FOR_MULTI_TERMS = True  # Use OR logic for multiple search terms
    QUERY_OPTIMIZATION = True  # Enable query optimization for better performance
    
    # Manual URL Validation Patterns
    MANUAL_URL_VALIDATION = {
        'allow_protocols': ['http://', 'https://'],
        'allow_wildcards': ['*.'],
        'forbidden_chars': ['<', '>', '"', "'", '&', ';'],
        'required_tld': True,  # Require valid TLD for domains
        'min_dots': 1  # Minimum number of dots in domain
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    # Allow more lenient validation in development
    MAX_SEARCH_TERMS = 15
    MAX_MANUAL_URLS = 100
    # Even more polling attempts for development
    COMMIT_MAX_POLLS = 30
    COMMIT_TIMEOUT = 240

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    # Stricter limits in production
    MAX_SEARCH_TERMS = 8
    MAX_MANUAL_URLS = 30
    # Increased production polling for better reliability
    COMMIT_MAX_POLLS = 20
    COMMIT_TIMEOUT = 150

# Default configuration
config = Config()