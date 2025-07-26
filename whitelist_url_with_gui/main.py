#!/usr/bin/env python3
"""
Palo Alto Firewall URL Whitelisting Web Application
==================================================
Fixed version for server deployment with proper logging
"""

import os
import sys
import urllib3
import logging
import argparse
from flask import Flask

# Import configuration and modules
from config import config
from utils.ssl_helper import get_ssl_context
from web.routes import register_routes

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def setup_server_logging():
    """Setup proper logging for server environment"""
    # Ensure logs directory exists
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    # Configure root logger to prevent debug output mixing with responses
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Only warnings and errors to console
    
    # Configure application logger to file
    app_logger = logging.getLogger('palo_alto_app')
    app_logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # File handler for application logs
    file_handler = logging.FileHandler(config.APP_LOG_FILE)
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    file_formatter = logging.Formatter(config.LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    app_logger.addHandler(file_handler)
    
    # Separate handler for server errors
    error_handler = logging.FileHandler(os.path.join(config.LOG_DIR, 'server_errors.log'))
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    return app_logger

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configure Flask app
    app.secret_key = config.SECRET_KEY
    app.permanent_session_lifetime = config.PERMANENT_SESSION_LIFETIME
    
    # Disable Flask's default request logging in production
    if not config.DEBUG:
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)
    
    # Register routes
    register_routes(app)
    
    return app

def setup_directories():
    """Create necessary directories"""
    directories = [
        config.LOG_DIR,
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def print_startup_info(host, port, ssl_enabled, app_logger):
    """Print application startup information"""
    startup_msg = f"""
    ================================
    Palo Alto Whitelist Tool v{config.VERSION}
    ================================
    Host: {host}
    Port: {port}
    SSL: {'Enabled' if ssl_enabled else 'Disabled'}
    Debug: {config.DEBUG}
    Logs: {config.LOG_DIR}
    ================================
    """
    
    print(startup_msg)
    app_logger.info(f"Server starting on {host}:{port} (SSL: {ssl_enabled})")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Palo Alto Whitelist Tool')
    parser.add_argument('--host', default=config.HOST, help='Host to bind to')
    parser.add_argument('--port', type=int, default=config.PORT, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL')
    return parser.parse_args()

def main():
    """Main application entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Override config with command line arguments
    if args.debug:
        config.DEBUG = True
        config.LOG_LEVEL = 'DEBUG'
    
    # Setup directories and logging
    setup_directories()
    app_logger = setup_server_logging()
    
    # Create Flask app
    app = create_app()
    
    # Get SSL context
    ssl_context = None if args.no_ssl else get_ssl_context()
    ssl_enabled = ssl_context is not None
    
    # Print startup information
    print_startup_info(args.host, args.port, ssl_enabled, app_logger)
    
    # Log startup
    app_logger.info(f"Starting Palo Alto Whitelist Tool v{config.VERSION}")
    app_logger.info(f"Configuration: Debug={config.DEBUG}, SSL={ssl_enabled}")
    
    # Run Flask app
    try:
        print(f"🚀 Server starting... Access at: {'https' if ssl_enabled else 'http'}://{args.host}:{args.port}")
        
        # Force stdout flush for server environments
        sys.stdout.flush()
        sys.stderr.flush()
        
        app.run(
            debug=config.DEBUG,
            host=args.host,
            port=args.port,
            ssl_context=ssl_context,
            threaded=True,  # Enable threading for better performance
            use_reloader=False  # Disable reloader in production
        )
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        app_logger.info("Application stopped by user")
    except Exception as e:
        error_msg = f"Application failed to start: {e}"
        print(f"\n❌ {error_msg}")
        app_logger.error(error_msg, exc_info=True)
        return 1
    
    app_logger.info("Application shutdown complete")
    return 0

if __name__ == '__main__':
    exit(main())