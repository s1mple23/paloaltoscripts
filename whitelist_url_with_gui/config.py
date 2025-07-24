"""
Configuration settings for Palo Alto Whitelist Tool
"""
import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Application Info
    APP_NAME = "Palo Alto Firewall URL Whitelisting Tool"
    VERSION = "1.3.0"
    DESCRIPTION = "Targeted Single Strategy Search"
    
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
    
    # Search Configuration
    DEFAULT_MAX_RESULTS = 3000
    LOOKBACK_MONTHS = 3
    SEARCH_TIMEOUT_ATTEMPTS = [10, 15, 25, 35]  # seconds
    ATTEMPT_WAIT_TIME = 3  # seconds between attempts
    
    # Commit Configuration
    COMMIT_MAX_POLLS = 10
    COMMIT_POLL_INTERVAL = 6  # seconds
    COMMIT_TIMEOUT = 60  # seconds
    
    # URL Validation
    MIN_SEARCH_TERM_LENGTH = 2
    MIN_DOMAIN_LENGTH = 3
    MAX_URL_LENGTH = 500
    
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

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'

# Default configuration
config = Config()