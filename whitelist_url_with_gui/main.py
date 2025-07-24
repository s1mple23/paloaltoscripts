#!/usr/bin/env python3
"""
Palo Alto Firewall URL Whitelisting Web Application
==================================================
A modular Flask-based web application for managing URL whitelisting on 
Palo Alto Firewalls via XML API with targeted search capabilities.

Features:
- Modular architecture for maintainability
- Targeted single-action search (block-url OR block-continue)
- Multiple timeout attempts for reliability
- Individual ticket logging for audit trails
- HTTPS support with self-signed certificates

Author: Security Operations Team
Version: 1.3.0 - Modular Architecture
License: MIT
"""

import os
import urllib3
from flask import Flask

# Import configuration and modules
from config import config
from utils.ssl_helper import get_ssl_context
from web.routes import register_routes

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configure Flask app
    app.secret_key = config.SECRET_KEY
    app.permanent_session_lifetime = config.PERMANENT_SESSION_LIFETIME
    
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
        print(f"✅ Directory ensured: {directory}")

def print_startup_info():
    """Print application startup information"""
    print("=" * 60)
    print(f"🔒 {config.APP_NAME} v{config.VERSION}")
    print("=" * 60)
    print("🎯 Modular Architecture Features:")
    print("   • Separated concerns (API, Services, Web, Utils)")
    print("   • Individual module testing capability")
    print("   • Enhanced maintainability and scalability")
    print("   • Targeted single-action search strategy")
    print("   • Multiple timeout attempts for reliability")
    print("   • Human-readable audit logging")
    print("")
    print("📁 Project Structure:")
    print("   • api/          - Firewall API communication")
    print("   • services/     - Business logic (search, whitelist, logging)")
    print("   • models/       - Data models and structures")
    print("   • web/          - Flask routes and templates")
    print("   • utils/        - Utility functions and validators")
    print("   • static/       - CSS and JavaScript files")
    print("   • logs/         - Application and ticket logs")
    print("")

def main():
    """Main application entry point"""
    # Setup directories
    setup_directories()
    
    # Print startup information
    print_startup_info()
    
    # Create Flask app
    app = create_app()
    
    # Get SSL context
    ssl_context = get_ssl_context()
    
    if ssl_context:
        print("🔐 HTTPS enabled")
        print(f"Access the tool at: https://{config.HOST}:{config.PORT}")
        print("⚠️  You may see a security warning - click 'Advanced' -> 'Proceed to localhost'")
    else:
        print("⚠️  Running in HTTP mode (less secure)")
        print(f"Access the tool at: http://{config.HOST}:{config.PORT}")
    
    print("")
    print("📁 Logs will be saved to:")
    print(f"   • Application log: {config.APP_LOG_FILE}")
    print(f"   • Individual tickets: {config.LOG_DIR}/ticket_[ID]_[timestamp].log")
    print("=" * 60)
    print("🚀 Starting Flask web application...")
    print("")
    
    # Run Flask app
    try:
        app.run(
            debug=config.DEBUG,
            host=config.HOST,
            port=config.PORT,
            ssl_context=ssl_context
        )
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Application failed to start: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())