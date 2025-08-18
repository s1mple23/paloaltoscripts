"""
Production Configuration for Ubuntu Server
Enhanced logging and output handling
Updated to support automatic dual-action search
"""
import os
from datetime import timedelta

class ServerConfig:
    """Production server configuration"""
    
    # Application Info
    APP_NAME = "Palo Alto Firewall URL Whitelisting Tool"
    VERSION = "1.6.0-server"
    DESCRIPTION = "Automatic Dual-Action Search with Category Display and Conditional Download"
    
    # Flask Configuration
    SECRET_KEY = os.urandom(24)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # SSL Configuration
    SSL_CERT_FILE = 'cert.pem'
    SSL_KEY_FILE = 'key.pem'
    
    # Server Configuration - Production Settings
    HOST = '0.0.0.0'  # Bind to all interfaces
    PORT = 5010
    DEBUG = False
    
    # Enhanced Logging Configuration for Server
    LOG_DIR = 'logs'
    APP_LOG_FILE = os.path.join(LOG_DIR, 'palo_alto_whitelist.log')
    SERVER_LOG_FILE = os.path.join(LOG_DIR, 'server.log')
    ERROR_LOG_FILE = os.path.join(LOG_DIR, 'errors.log')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    
    # Server-specific logging
    SEPARATE_STDOUT_STDERR = True
    BUFFER_OUTPUT = False  # Disable buffering for real-time logs
    
    # Search Configuration
    DEFAULT_MAX_RESULTS = 3000
    LOOKBACK_MONTHS = 3
    SEARCH_TIMEOUT_ATTEMPTS = [15, 25, 35, 45]  # Longer timeouts for server
    ATTEMPT_WAIT_TIME = 5  # More wait time between attempts
    
    # Multi-URL Search Configuration
    MAX_SEARCH_TERMS = 10
    SEARCH_TERM_SEPARATOR = ','
    MIN_SEARCH_TERM_LENGTH_MULTI = 2
    
    # Manual URL Configuration
    MAX_MANUAL_URLS = 50
    MANUAL_URL_SEPARATORS = [',', '\n', '\r\n']
    ALLOW_WILDCARD_MANUAL = True
    
    # Commit Configuration - Extended for server
    COMMIT_MAX_POLLS = 30  # More polling attempts
    COMMIT_POLL_INTERVAL = 8  # Longer intervals
    COMMIT_TIMEOUT = 300  # 5 minutes timeout
    
    # URL Validation
    MIN_SEARCH_TERM_LENGTH = 2
    MIN_DOMAIN_LENGTH = 3
    MAX_URL_LENGTH = 500
    MAX_MANUAL_URL_LENGTH = 200
    
    # API Configuration - Extended timeouts for server
    API_TIMEOUT = 45  # Longer API timeout
    JOB_CHECK_INTERVAL = 3  # More conservative
    STATUS_CHECK_TIMEOUT = 15
    
    # Valid Actions - Extended to support automatic dual search
    VALID_ACTIONS = ['block-url', 'block-continue']
    EXTENDED_VALID_ACTIONS = ['block-url', 'block-continue', 'both']  # 'both' for automatic dual search
    
    # URL Sources
    URL_SOURCES = ['misc', 'url', 'src-location', 'dst-location', 'hostname', 'host']
    
    # URL Separators
    URL_SEPARATORS = [' ', '\t', '\n', '&r=', '&gdpr_consent=', '?r=']
    
    # Query Building
    USE_OR_LOGIC_FOR_MULTI_TERMS = True
    QUERY_OPTIMIZATION = True
    
    # Automatic Dual Search Configuration
    ENABLE_AUTOMATIC_DUAL_SEARCH = True
    DUAL_SEARCH_ACTIONS = ['block-url', 'block-continue']
    
    # Server-specific settings
    WERKZEUG_LOG_LEVEL = 'ERROR'  # Minimize Flask logs
    ENABLE_REQUEST_LOGGING = False  # Disable request logging in production
    JSON_ENSURE_ASCII = False  # Proper UTF-8 handling
    
    # Manual URL Validation
    MANUAL_URL_VALIDATION = {
        'allow_protocols': ['http://', 'https://'],
        'allow_wildcards': ['*.'],
        'forbidden_chars': ['<', '>', '"', "'", '&', ';'],
        'required_tld': True,
        'min_dots': 1
    }

# Use server config as default
config = ServerConfig()

# Environment-based configuration
if os.environ.get('FLASK_ENV') == 'development':
    config.DEBUG = True
    config.LOG_LEVEL = 'DEBUG'
    config.HOST = '127.0.0.1'
    config.ENABLE_REQUEST_LOGGING = True