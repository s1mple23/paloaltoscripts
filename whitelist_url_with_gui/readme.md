# 🔒 Palo Alto Firewall URL Whitelisting Tool

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/yourusername/palo-alto-whitelist-tool)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3+-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

A powerful web-based tool for managing URL whitelisting on Palo Alto Firewalls via XML API. Features enhanced multi-URL search with OR logic, manual URL input, and comprehensive audit logging.

## ✨ Features

### 🎯 Enhanced Multi-URL Search
- **Single Term Search**: Search for individual terms (e.g., `youtube`)
- **Multi-Term Search**: Search multiple terms with OR logic (e.g., `youtube, facebook, activision`)
- **Automatic OR Logic**: System automatically builds queries like `(url contains 'term1') or (url contains 'term2')`
- **Multiple Timeout Attempts**: 4 attempts with increasing timeouts (10s, 15s, 25s, 35s) for reliability

### 📝 Manual URL Input
- **Flexible Input**: Add URLs manually via textarea (comma-separated or line-by-line)
- **Real-time Validation**: Instant validation of manually entered URLs
- **Wildcard Support**: Support for wildcard domains (e.g., `*.google.com`)
- **Mixed Sources**: Combine search results with manually entered URLs

### 🔍 Advanced Search Features
- **Targeted Action Filtering**: Search specifically for `block-url` or `block-continue` actions
- **Time-based Filtering**: Search last 3 months of logs (configurable)
- **High Volume Support**: Process up to 3,000 log entries per search
- **Exact Domain Extraction**: Smart extraction of exact domains from complex URL structures

### 🛡️ Security & Reliability
- **HTTPS Support**: Self-signed SSL certificates for secure communication
- **Session Management**: Secure session handling with timeout
- **Input Validation**: Comprehensive validation for all user inputs
- **Error Handling**: Robust error handling with user-friendly messages

### 📊 Audit & Compliance
- **Individual Ticket Logs**: Human-readable log file for each whitelist operation
- **Comprehensive Logging**: Application-wide logging for troubleshooting
- **Audit Trail**: Complete audit trail for compliance requirements
- **Debug Mode**: Built-in debugging tools for connection testing

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Palo Alto Firewall with XML API access
- Valid firewall credentials with appropriate permissions

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/palo-alto-whitelist-tool.git
   cd palo-alto-whitelist-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

4. **Access the web interface**
   - HTTPS: `https://localhost:5010` (recommended)
   - HTTP: `http://localhost:5010` (if SSL fails)

## 📋 Usage Guide

### 1. Login
- Enter your Palo Alto Firewall IP/hostname
- Provide your firewall credentials
- Click "Connect to Firewall"

### 2. Search for Blocked URLs

#### Single Term Search
```
youtube
```

#### Multi-Term Search (OR Logic)
```
youtube, facebook, activision, playstation, twitch
```

#### Action Type Selection
- **block-url**: URLs that were completely blocked
- **block-continue**: URLs that were blocked but connection continued

### 3. Manual URL Addition
After search completion, you can add additional URLs manually:

```
discord.com
*.steam.com
battle.net
epic.com
```

### 4. Configure Whitelisting Options
- **Exact Match**: Add domains as-is (e.g., `domain.com/`)
- **Wildcard Match**: Add wildcard versions (e.g., `*.domain.com/`)

### 5. Select URL Category
Choose from available custom URL categories on your firewall.

### 6. Submit with Ticket ID
Enter your change/ticket ID and submit the whitelist request.

## 📁 Project Structure

```
palo-alto-whitelist-tool/
├── main.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── api/
│   ├── __init__.py
│   └── palo_alto_client.py # Firewall API client
├── models/
│   ├── __init__.py
│   └── ticket.py          # Data models
├── services/
│   ├── __init__.py
│   ├── search_service.py   # Enhanced search logic
│   ├── whitelist_service.py # Whitelist management
│   └── logging_service.py  # Audit logging
├── utils/
│   ├── __init__.py
│   ├── validators.py      # Input validation
│   └── ssl_helper.py      # SSL certificate handling
├── web/
│   ├── __init__.py
│   ├── routes.py          # Flask routes
│   └── templates.py       # HTML templates
├── static/
│   └── js/
│       └── dashboard.js   # Enhanced frontend logic
└── logs/                  # Application and ticket logs
    ├── palo_alto_whitelist.log
    └── ticket_*.log
```

## ⚙️ Configuration

### Basic Configuration
Edit `config.py` to customize:

```python
# Server Configuration
HOST = '127.0.0.1'
PORT = 5010

# Search Configuration
LOOKBACK_MONTHS = 3
DEFAULT_MAX_RESULTS = 3000
SEARCH_TIMEOUT_ATTEMPTS = [10, 15, 25, 35]

# Multi-URL Configuration
MAX_SEARCH_TERMS = 10
MAX_MANUAL_URLS = 50
```

### Environment-Specific Configs
- **Development**: `DevelopmentConfig` - More lenient limits, debug mode
- **Production**: `ProductionConfig` - Stricter limits, optimized for production

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET/POST | Login page |
| `/dashboard` | GET | Main dashboard |
| `/search_urls` | POST | Execute multi-term URL search |
| `/validate_manual_urls` | POST | Validate manually entered URLs |
| `/get_categories` | GET | Fetch URL categories |
| `/submit_whitelist` | POST | Submit whitelist request |
| `/commit_status` | POST | Check commit status |
| `/debug_logs` | GET | Debug connection and logs |

## 📝 Logging

### Application Logs
- Location: `logs/palo_alto_whitelist.log`
- Contains: API calls, errors, user actions

### Individual Ticket Logs
- Location: `logs/ticket_[ID]_[timestamp].log`
- Contains: Human-readable audit trail for each whitelist operation
- Format: Structured text with all relevant details

### Example Ticket Log
```
================================================================================
                    PALO ALTO URL WHITELISTING - TICKET LOG
================================================================================

TICKET INFORMATION:
-------------------
Ticket ID:      CHG-2024-001234
Date & Time:    2024-07-26 - 14:30:25
Processed by:   admin
Firewall:       192.168.1.100

WHITELIST OPERATION:
-------------------
Category Name:  Gaming-Allowed
Category Type:  shared
Number of URLs: 8

URLs ADDED:
-----------
 1. youtube.com/
 2. *.youtube.com/
 3. twitch.tv/
 4. *.twitch.tv/
 5. steam.com/
 6. *.steam.com/
 7. battle.net/
 8. *.battle.net/

OPERATION STATUS:
-----------------
Success:        ✅ YES
Commit Job ID:  12345
Commit Status:  FIN
Commit Progress: 100%

SEARCH DETAILS:
---------------
Search Strategy: multi_term_or_logic_multiple_timeouts
Action Type:     block-url
Lookback Period: 3 months
Max Entries:     3000
```

## 🛠️ Troubleshooting

### Common Issues

#### Connection Issues
```bash
# Test firewall connectivity
curl -k "https://your-firewall-ip/api/?type=version"
```

#### SSL Certificate Issues
- Tool automatically generates self-signed certificates
- Browser will show security warning - click "Advanced" → "Proceed to localhost"

#### Search Timeouts
- Increase timeout values in `config.py`
- Use more specific search terms
- Check firewall log processing load

### Debug Mode
Enable debug mode for detailed logging:
```python
# In config.py
DEBUG = True
LOG_LEVEL = 'DEBUG'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
python main.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [Palo Alto Networks XML API Guide](https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-panorama-api)
- [Flask Documentation](https://flask.palletsprojects.com/)

### Getting Help
1. Check the [Issues](https://github.com/yourusername/palo-alto-whitelist-tool/issues) page
2. Review the troubleshooting section above
3. Enable debug mode for detailed error information
4. Create a new issue with:
   - Error messages from logs
   - Steps to reproduce
   - Environment details

## 🔄 Changelog

### v1.5.0 - Enhanced Multi-URL Search
- Improve commit status and fix issue with commit status.

### v1.4.0 - Enhanced Multi-URL Search
- ✨ Added multi-term search with OR logic
- 📝 Added manual URL input functionality  
- 🔍 Improved search query building
- 🎯 Enhanced user interface
- 📊 Better validation and error handling

### v1.3.0 - Modular Architecture
- 🏗️ Restructured to modular architecture
- 🔐 Added HTTPS support
- 📋 Individual ticket logging
- 🎯 Targeted single-action search

### v1.2.0 - Initial Release
- 🚀 Basic URL whitelisting functionality
- 🔍 Simple search capabilities
- 📊 Basic logging

## 🎯 Roadmap

- [ ] **Bulk Operations**: Support for bulk whitelist operations
- [ ] **Advanced Filtering**: Additional search filters (IP ranges, time ranges)
- [ ] **Category Management**: Create/modify custom URL categories
- [ ] **Reporting**: Generate compliance and usage reports
- [ ] **API Mode**: REST API for automation
- [ ] **Multi-Firewall**: Support for multiple firewall management
- [ ] **Rule Integration**: Integration with security policy rules

---

**⚠️ Security Notice**: This tool requires administrative access to Palo Alto Firewalls. Ensure proper access controls and audit procedures are in place before deployment in production environments.