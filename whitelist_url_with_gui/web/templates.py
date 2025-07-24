"""
HTML Templates for the web interface
"""
from config import config

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.APP_NAME }}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .btn { width: 100%; padding: 12px; background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #005a87; }
        .error { color: #d32f2f; margin-top: 10px; padding: 10px; background: #ffebee; border-radius: 4px; }
        .info { color: #1976d2; text-align: center; margin-top: 20px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Palo Alto Firewall<br>URL Whitelisting Tool</h1>
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="hostname">Firewall IP/Hostname:</label>
                <input type="text" id="hostname" name="hostname" required value="{{ request.form.hostname or '' }}">
            </div>
            
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required value="{{ request.form.username or '' }}">
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn">Connect to Firewall</button>
        </form>
        
        <div class="info">
            Enter your firewall credentials to begin URL whitelisting management<br>
            <small>Version {{ config.VERSION }} - {{ config.DESCRIPTION }}</small>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Whitelisting Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .header h1 { margin: 0; color: #333; }
        .header .info { color: #666; margin-top: 5px; }
        .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .section h2 { color: #333; margin-top: 0; border-bottom: 2px solid #007cba; padding-bottom: 10px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
        input[type="text"], select, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .btn { padding: 10px 20px; background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; margin-bottom: 10px; }
        .btn:hover { background: #005a87; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #545b62; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #1e7e34; }
        .url-list { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9; }
        .url-item { display: flex; align-items: center; margin-bottom: 8px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background: white; }
        .url-item:hover { background: #f8f9fa; }
        .url-item input[type="checkbox"] { margin-right: 10px; transform: scale(1.2); cursor: pointer; }
        .url-item label { cursor: pointer; user-select: none; flex: 1; }
        .selected-urls { background: #e3f2fd; padding: 15px; border-radius: 4px; margin-top: 15px; }
        .loading { text-align: center; padding: 20px; color: #666; }
        .error { color: #d32f2f; padding: 10px; background: #ffebee; border-radius: 4px; margin-bottom: 15px; }
        .success { color: #2e7d32; padding: 10px; background: #e8f5e8; border-radius: 4px; margin-bottom: 15px; }
        .step { opacity: 0.5; pointer-events: none; }
        .step.active { opacity: 1; pointer-events: auto; }
        .step-number { display: inline-block; background: #007cba; color: white; width: 25px; height: 25px; border-radius: 50%; text-align: center; line-height: 25px; margin-right: 10px; }
        .logout { float: right; }
        .whitelist-options { background: #f0f8ff; padding: 15px; border-radius: 4px; margin-top: 15px; }
        .whitelist-options label { font-weight: normal; }
        .commit-status { background: #fff3cd; padding: 15px; border-radius: 4px; margin-top: 15px; }
        .filtering-info { background: #e8f5e8; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 14px; }
        .action-selection { background: #f0f8ff; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
        .action-selection label { font-weight: normal; display: inline-block; margin-right: 20px; }
        .action-selection input[type="radio"] { margin-right: 5px; }
        .timing-info { background: #fff3cd; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 14px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 URL Whitelisting Dashboard</h1>
        <div class="info">Connected to: {{ session.hostname }} as {{ session.username }} | Version {{ config.VERSION }} - Targeted Search</div>
        <a href="{{ url_for('logout') }}" class="btn btn-secondary logout">Logout</a>
    </div>

    <!-- Step 1: Search for Blocked URLs -->
    <div class="section step active" id="step1">
        <h2><span class="step-number">1</span>Search Blocked URLs</h2>
        
        <div class="timing-info">
            ⏱️ <strong>Search Duration:</strong> Each search takes approximately 2 minutes (4 attempts with timeouts: {{ config.SEARCH_TIMEOUT_ATTEMPTS|join(', ') }}s + processing time)
        </div>
        
        <div class="filtering-info">
            ℹ️ <strong>Targeted Search System:</strong> Choose ONE action type to search for. The system will run {{ config.SEARCH_TIMEOUT_ATTEMPTS|length }} attempts with different timeouts to ensure reliable results. Searches the last {{ config.LOOKBACK_MONTHS }} months with up to {{ config.DEFAULT_MAX_RESULTS }} entries.
        </div>
        
        {% if messages %}
            {% for category, message in messages %}
                <div class="{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
        
        <form id="searchForm">
            <div class="form-group">
                <label for="search_term">Search Term (partial URL/domain):</label>
                <input type="text" id="search_term" name="search_term" placeholder="e.g., youtube, facebook, google">
            </div>
            
            <div class="action-selection">
                <strong>Select Action Type to Search:</strong><br><br>
                <label>
                    <input type="radio" name="action_type" value="block-url" checked> 
                    <strong>block-url</strong> - URLs that were completely blocked
                </label>
                <label>
                    <input type="radio" name="action_type" value="block-continue"> 
                    <strong>block-continue</strong> - URLs that were blocked but connection continued
                </label>
            </div>
            
            <button type="submit" class="btn">Start Targeted Search (~2 minutes)</button>
            <button type="button" class="btn btn-secondary" onclick="debugLogs()">Debug Connection</button>
        </form>
        
        <div id="debugResults" style="display: none; margin-top: 15px;"></div>
    </div>

    <!-- Step 2: Select URLs and Options -->
    <div class="section step" id="step2">
        <h2><span class="step-number">2</span>Select URLs to Whitelist</h2>
        
        <div id="urlSelection">
            <!-- Search results will appear here -->
        </div>
        
        <div class="whitelist-options" id="whitelistOptions" style="display: none;">
            <h3>Whitelisting Options:</h3>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="exactMatch" checked> Add exact matches (e.g., domain.com/)
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="wildcardMatch" checked> Add wildcard matches (e.g., *.domain.com/)
                </label>
            </div>
        </div>
        
        <div class="selected-urls" id="selectedUrlsPreview" style="display: none;">
            <h3>URLs to be whitelisted:</h3>
            <div id="urlPreviewList"></div>
        </div>
        
        <button class="btn" onclick="proceedToCategories()" id="proceedBtn" style="display: none;">Proceed to Category Selection</button>
    </div>

    <!-- Step 3: Select Category -->
    <div class="section step" id="step3">
        <h2><span class="step-number">3</span>Select URL Category</h2>
        
        <div class="form-group">
            <label for="urlCategory">Choose Custom URL Category:</label>
            <select id="urlCategory" name="urlCategory">
                <option value="">Loading categories...</option>
            </select>
        </div>
        
        <button class="btn" onclick="proceedToTicket()" id="categoryProceedBtn" style="display: none;">Continue</button>
    </div>

    <!-- Step 4: Ticket ID and Final Submission -->
    <div class="section step" id="step4">
        <h2><span class="step-number">4</span>Change Ticket & Submit</h2>
        
        <div class="form-group">
            <label for="ticketId">Change/Ticket ID:</label>
            <input type="text" id="ticketId" name="ticketId" required placeholder="e.g., CHG-2024-001234">
        </div>
        
        <div id="finalSummary"></div>
        
        <button class="btn btn-success" onclick="submitWhitelist()" id="submitBtn">Submit Whitelist Request</button>
    </div>

    <!-- Step 5: Results -->
    <div class="section step" id="step5">
        <h2><span class="step-number">5</span>Results</h2>
        <div id="results"></div>
        <button class="btn" onclick="startOver()">Start New Request</button>
    </div>

    <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
</body>
</html>
'''

def get_login_template():
    """Get login template with config injected"""
    return LOGIN_TEMPLATE

def get_dashboard_template():
    """Get dashboard template with config injected"""
    return DASHBOARD_TEMPLATE