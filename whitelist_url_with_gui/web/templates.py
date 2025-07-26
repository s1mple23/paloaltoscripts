"""
Enhanced HTML Templates for the web interface
Complete file with embedded JavaScript and proper function exports
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
            <small>Version {{ config.VERSION }} - Enhanced Multi-URL Search with Manual Input</small>
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
    <title>Enhanced URL Whitelisting Dashboard</title>
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
        .multi-search-info { background: #e1f5fe; padding: 15px; border-radius: 4px; margin-bottom: 15px; border-left: 4px solid #01579b; }
        .manual-url-section { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 20px; border: 1px solid #dee2e6; }
        .validation-message { margin-top: 10px; padding: 8px; border-radius: 4px; font-size: 14px; }
        .validation-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .validation-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .validation-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Enhanced URL Whitelisting Dashboard</h1>
        <div class="info">Connected to: {{ session.hostname }} as {{ session.username }} | Version {{ config.VERSION }} - Multi-URL Search + Manual Input</div>
        <a href="{{ url_for('logout') }}" class="btn btn-secondary logout">Logout</a>
    </div>

    <!-- Step 1: Enhanced Search for Blocked URLs -->
    <div class="section step active" id="step1">
        <h2><span class="step-number">1</span>Enhanced URL Search</h2>
        
        <div class="timing-info">
            ⏱️ <strong>Search Duration:</strong> Each search takes approximately 3-4 minutes (4 attempts with extended timeouts)
        </div>
        
        <div class="multi-search-info">
            🎯 <strong>Enhanced Multi-URL Search System:</strong><br>
            • <strong>Single Term:</strong> Enter one search term (e.g., "youtube")<br>
            • <strong>Multiple Terms:</strong> Enter comma-separated terms (e.g., "youtube, facebook, twitch")<br>
            • <strong>OR Logic:</strong> System automatically uses OR logic for multiple terms<br>
            • <strong>Manual URLs:</strong> Add additional URLs manually after search<br>
            • <strong>Time Range:</strong> Searches last 3 months with up to 3,000 entries
        </div>
        
        <form id="searchForm" onsubmit="return handleSearchSubmit(event);">
            <div class="form-group">
                <label for="search_term">Search Terms (single or comma-separated):</label>
                <input type="text" id="search_term" name="search_term" 
                       placeholder="Examples: youtube  OR  youtube, facebook, activision, playstation">
                <small style="color: #666; font-size: 12px;">
                    💡 For multiple terms, separate with commas. System will search for URLs containing ANY of these terms.
                </small>
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
            
            <button type="submit" class="btn" id="searchButton">Start Enhanced Search (~3-4 minutes)</button>
            <button type="button" class="btn btn-secondary" onclick="debugLogs()">Debug Connection</button>
        </form>
        
        <div id="debugResults" style="display: none; margin-top: 15px;"></div>
    </div>

    <!-- Step 2: Enhanced URL Selection with Manual Input -->
    <div class="section step" id="step2">
        <h2><span class="step-number">2</span>Select URLs & Add Manual URLs</h2>
        
        <div id="urlSelection">
            <!-- Search results will appear here -->
        </div>
        
        <div class="whitelist-options" id="whitelistOptions" style="display: none;">
            <h3>Whitelisting Options:</h3>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="exactMatch" checked onchange="updateUrlPreview()"> Add exact matches (e.g., domain.com/)
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="wildcardMatch" checked onchange="updateUrlPreview()"> Add wildcard matches (e.g., *.domain.com/)
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
        
        <button class="btn btn-success" onclick="submitWhitelist()" id="submitBtn">Submit Enhanced Whitelist Request</button>
    </div>

    <!-- Step 5: Results -->
    <div class="section step" id="step5">
        <h2><span class="step-number">5</span>Results</h2>
        <div id="results"></div>
        <button class="btn" onclick="startOver()">Start New Request</button>
    </div>

    <script>
        // Embedded JavaScript to avoid loading issues
        console.log('[DEBUG] Dashboard script starting...');
        
        // Global variables
        var selectedUrls = [];
        var searchResults = [];
        var manualUrls = [];
        var categories = {};
        var selectedActionType = 'block-url';

        // Prevent form submission from reloading page
        function handleSearchSubmit(event) {
            event.preventDefault();
            event.stopPropagation();
            
            console.log('[DEBUG] Search form submitted - preventing default');
            
            var searchTerms = document.getElementById('search_term').value.trim();
            selectedActionType = document.querySelector('input[name="action_type"]:checked').value;
            
            console.log('[DEBUG] Search terms:', searchTerms);
            console.log('[DEBUG] Action type:', selectedActionType);
            
            if (!searchTerms) {
                alert('Please enter at least one search term');
                return false;
            }
            
            // Validate search terms
            var terms = searchTerms.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t.length > 0; });
            if (terms.length === 0) {
                alert('Please enter valid search terms');
                return false;
            }
            
            var resultsDiv = document.getElementById('urlSelection');
            var searchBtn = document.getElementById('searchButton');
            
            console.log('[DEBUG] Starting enhanced multi-term search request...');
            
            searchBtn.disabled = true;
            searchBtn.textContent = 'Searching... (~3-4 min)';
            
            activateStep(2);
            
            // Show different message based on number of terms
            var searchMessage = terms.length === 1 
                ? '🎯 Targeted search for "' + terms[0] + '" with action "' + selectedActionType + '"'
                : '🎯 Multi-term search for ' + terms.length + ' terms (' + terms.join(', ') + ') with OR logic and action "' + selectedActionType + '"';
            
            resultsDiv.innerHTML = '<div class="loading">' + searchMessage + '...<br>' +
                                  '<small>⏱️ Running up to 4 attempts with extended timeouts<br>' +
                                  'Searching last 3 months, up to 3,000 entries<br>' +
                                  '<strong>Estimated time: ~3-4 minutes - Please wait...</strong></small></div>';
            
            console.log('[DEBUG] Making fetch request to /search_urls');
            
            fetch('/search_urls', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    search_term: searchTerms,
                    action_type: selectedActionType
                })
            })
            .then(function(response) {
                console.log('[DEBUG] Got response:', response.status, response.statusText);
                
                // Check if response is JSON
                var contentType = response.headers.get('Content-Type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned non-JSON response (got: ' + (contentType || 'unknown') + ')');
                }
                
                if (!response.ok) {
                    throw new Error('HTTP error! status: ' + response.status);
                }
                
                return response.json();
            })
            .then(function(data) {
                console.log('[DEBUG] Response data:', data);
                
                if (data.success) {
                    console.log('[DEBUG] Search successful, found URLs:', data.urls);
                    searchResults = data.urls || [];
                    displaySearchResults(searchResults, searchTerms, selectedActionType, data.debug_info);
                    showManualUrlInput();
                } else {
                    console.log('[DEBUG] Search failed:', data.error);
                    var errorMessage = data.error || 'Unknown error occurred';
                    
                    // Don't treat "no URLs found" as an error in the UI
                    if (errorMessage.includes('no URLs were found') || errorMessage.includes('no matching URLs')) {
                        searchResults = [];
                        displaySearchResults([], searchTerms, selectedActionType, data.debug_info);
                        showManualUrlInput();
                    } else {
                        resultsDiv.innerHTML = '<div class="error">Search Error: ' + errorMessage + '</div>';
                        showManualUrlInput();
                    }
                }
            })
            .catch(function(error) {
                console.error('[DEBUG] Fetch error:', error);
                var errorMessage = 'Network error: ' + error.message;
                
                if (error.message.includes('non-JSON response')) {
                    errorMessage = 'Server error: The server returned an unexpected response. Please check your firewall connection and try again.';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Connection error: Could not connect to the server. Please check your network connection.';
                }
                
                resultsDiv.innerHTML = '<div class="error">' + errorMessage + '</div>';
                showManualUrlInput();
            })
            .finally(function() {
                console.log('[DEBUG] Search request completed');
                searchBtn.disabled = false;
                searchBtn.textContent = 'Start Enhanced Search (~3-4 minutes)';
            });
            
            return false;
        }
        
        function displaySearchResults(urls, searchTerms, actionType, debugInfo) {
            var resultsDiv = document.getElementById('urlSelection');
            var terms = searchTerms.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t.length > 0; });
            
            var html = '';
            
            if (urls.length === 0) {
                html = '<div style="text-align: center; padding: 20px; color: #666;">' +
                    '<h4>✅ Search Completed - No URLs Found</h4>';
                
                if (terms.length === 1) {
                    html += '<p>No URLs containing "' + terms[0] + '" were found with action: <strong>' + actionType + '</strong></p>';
                } else {
                    html += '<p>No URLs containing any of the terms (' + terms.join(', ') + ') were found with action: <strong>' + actionType + '</strong></p>';
                }
                
                html += '<p><small>✅ Search completed successfully. You can add URLs manually below.</small></p>' +
                    '</div>';
            } else {
                html = '<h3>🎯 Found ' + urls.length + ' blocked URLs:</h3>';
                
                if (terms.length === 1) {
                    html += '<div style="margin: 10px 0; padding: 10px; background: #f0f8ff; border-radius: 4px;">' +
                           '✅ <strong>Single-term Results:</strong> Searched for "' + terms[0] + '" with action "' + actionType + '"<br>';
                } else {
                    html += '<div style="margin: 10px 0; padding: 10px; background: #f0f8ff; border-radius: 4px;">' +
                           '✅ <strong>Multi-term OR Results:</strong> Searched for ' + terms.length + ' terms (' + terms.join(', ') + ') with action "' + actionType + '"<br>';
                }
                
                html += '📅 <strong>Time Range:</strong> Last 3 months, up to 3,000 entries<br>' +
                       'Click the checkboxes below to select URLs for whitelisting:</div>';
                
                for (var i = 0; i < urls.length; i++) {
                    var url = urls[i];
                    html += '<div class="url-item" style="margin: 8px 0; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background: white;">';
                    html += '<input type="checkbox" id="url_' + i + '" value="' + url + '" style="margin-right: 10px; transform: scale(1.2);" onchange="updateSelectedUrls()">';
                    html += '<label for="url_' + i + '" style="cursor: pointer; user-select: none;">' + url + '</label>';
                    html += '</div>';
                }
            }
            
            resultsDiv.innerHTML = html;
        }
        
        function showManualUrlInput() {
            console.log('[DEBUG] Showing manual URL input section');
            var urlSelection = document.getElementById('urlSelection');
            var existing = document.getElementById('manualUrlSection');
            if (!existing) {
                var manualHtml = '<div id="manualUrlSection" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; border: 1px solid #dee2e6;">' +
                                '<h4>📝 Add Manual URLs</h4>' +
                                '<p>You can also add URLs manually (one per line or comma-separated):</p>' +
                                '<textarea id="manualUrls" placeholder="Example:&#10;youtube.com&#10;facebook.com&#10;*.google.com&#10;or: youtube.com, facebook.com, *.google.com" ' +
                                'style="width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace;"></textarea>' +
                                '<div id="manualUrlValidation" style="margin-top: 10px;"></div>' +
                                '<button type="button" class="btn" onclick="addManualUrls()" style="margin-top: 10px;">Add Manual URLs</button>' +
                                '</div>';
                urlSelection.insertAdjacentHTML('afterend', manualHtml);
                
                // Add event listener for validation
                var manualUrlInput = document.getElementById('manualUrls');
                if (manualUrlInput) {
                    manualUrlInput.addEventListener('input', validateManualUrls);
                }
            }
        }
        
        function validateManualUrls() {
            var input = document.getElementById('manualUrls').value.trim();
            var validationDiv = document.getElementById('manualUrlValidation');
            
            if (!input) {
                validationDiv.innerHTML = '';
                return;
            }
            
            fetch('/validate_manual_urls', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({manual_urls: input})
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    var html = '';
                    if (data.valid_urls && data.valid_urls.length > 0) {
                        html += '<div style="color: green;">✅ Valid URLs (' + data.valid_urls.length + '): ' + data.valid_urls.join(', ') + '</div>';
                    }
                    if (data.invalid_urls && data.invalid_urls.length > 0) {
                        html += '<div style="color: red;">❌ Invalid URLs (' + data.invalid_urls.length + '): ' + data.invalid_urls.join(', ') + '</div>';
                    }
                    validationDiv.innerHTML = html;
                }
            })
            .catch(function(error) {
                validationDiv.innerHTML = '<div style="color: orange;">⚠️ Validation temporarily unavailable</div>';
            });
        }
        
        function addManualUrls() {
            var input = document.getElementById('manualUrls').value.trim();
            if (!input) {
                alert('Please enter some URLs');
                return;
            }
            
            fetch('/validate_manual_urls', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({manual_urls: input})
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success && data.valid_urls && data.valid_urls.length > 0) {
                    // Add valid URLs to manual list
                    data.valid_urls.forEach(function(url) {
                        if (manualUrls.indexOf(url) === -1) {
                            manualUrls.push(url);
                        }
                    });
                    
                    // Clear input
                    document.getElementById('manualUrls').value = '';
                    document.getElementById('manualUrlValidation').innerHTML = '';
                    
                    // Update display
                    displayManualUrls();
                    updateSelectedUrls();
                    
                    alert('Added ' + data.valid_urls.length + ' valid URLs to selection');
                    
                    if (data.invalid_urls && data.invalid_urls.length > 0) {
                        alert('Note: ' + data.invalid_urls.length + ' invalid URLs were ignored: ' + data.invalid_urls.join(', '));
                    }
                } else {
                    alert('No valid URLs found. Please check your input.');
                }
            })
            .catch(function(error) {
                alert('Error validating URLs: ' + error.message);
            });
        }
        
        function displayManualUrls() {
            var manualSection = document.getElementById('manualUrlSection');
            var existingDisplay = document.getElementById('manualUrlDisplay');
            
            if (existingDisplay) {
                existingDisplay.remove();
            }
            
            if (manualUrls.length > 0) {
                var html = '<div id="manualUrlDisplay" style="margin-top: 15px; padding: 10px; background: #e8f5e8; border-radius: 4px;">' +
                          '<h5>📋 Manual URLs (' + manualUrls.length + '):</h5>';
                
                for (var i = 0; i < manualUrls.length; i++) {
                    html += '<div style="margin: 5px 0; padding: 5px; background: white; border-radius: 3px; display: flex; align-items: center;">' +
                           '<input type="checkbox" id="manual_' + i + '" checked style="margin-right: 10px;" onchange="updateSelectedUrls()">' +
                           '<span style="flex: 1;">' + manualUrls[i] + '</span>' +
                           '<button onclick="removeManualUrl(' + i + ')" style="padding: 2px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer;">Remove</button>' +
                           '</div>';
                }
                
                html += '</div>';
                manualSection.insertAdjacentHTML('afterend', html);
            }
        }
        
        function removeManualUrl(index) {
            manualUrls.splice(index, 1);
            displayManualUrls();
            updateSelectedUrls();
        }
        
        function updateSelectedUrls() {
            console.log('[DEBUG] Updating selected URLs');
            selectedUrls = [];
            
            // Add selected search results
            for (var i = 0; i < searchResults.length; i++) {
                var checkbox = document.getElementById('url_' + i);
                if (checkbox && checkbox.checked) {
                    selectedUrls.push(searchResults[i]);
                }
            }
            
            // Add selected manual URLs
            for (var i = 0; i < manualUrls.length; i++) {
                var checkbox = document.getElementById('manual_' + i);
                if (checkbox && checkbox.checked) {
                    selectedUrls.push(manualUrls[i]);
                }
            }
            
            var optionsDiv = document.getElementById('whitelistOptions');
            var previewDiv = document.getElementById('selectedUrlsPreview');
            var proceedBtn = document.getElementById('proceedBtn');
            
            if (selectedUrls.length > 0) {
                optionsDiv.style.display = 'block';
                updateUrlPreview();
                previewDiv.style.display = 'block';
                proceedBtn.style.display = 'inline-block';
            } else {
                optionsDiv.style.display = 'none';
                previewDiv.style.display = 'none';
                proceedBtn.style.display = 'none';
            }
        }
        
        function updateUrlPreview() {
            console.log('[DEBUG] Updating URL preview');
            var exactMatch = document.getElementById('exactMatch').checked;
            var wildcardMatch = document.getElementById('wildcardMatch').checked;
            var previewList = document.getElementById('urlPreviewList');
            
            var html = '<ul>';
            for (var i = 0; i < selectedUrls.length; i++) {
                var url = selectedUrls[i];
                
                // Handle different URL formats
                if (url.startsWith('*.')) {
                    // Already a wildcard
                    if (wildcardMatch) {
                        html += '<li>' + url + '</li>';
                    }
                    if (exactMatch) {
                        // Remove wildcard for exact match
                        var exactUrl = url.substring(2);
                        if (!exactUrl.endsWith('/')) {
                            exactUrl += '/';
                        }
                        html += '<li>' + exactUrl + '</li>';
                    }
                } else {
                    // Regular domain
                    var domain = url.endsWith('/') ? url : url + '/';
                    if (exactMatch) {
                        html += '<li>' + domain + '</li>';
                    }
                    if (wildcardMatch) {
                        html += '<li>*.' + domain + '</li>';
                    }
                }
            }
            html += '</ul>';
            
            previewList.innerHTML = html;
        }
        
        function activateStep(stepNumber) {
            console.log('[DEBUG] Activating step:', stepNumber);
            for (var i = 1; i <= 5; i++) {
                var step = document.getElementById('step' + i);
                if (step) {
                    step.classList.remove('active');
                }
            }
            
            var targetStep = document.getElementById('step' + stepNumber);
            if (targetStep) {
                targetStep.classList.add('active');
            }
        }
        
        function debugLogs() {
            console.log('[DEBUG] Debug button clicked');
            
            var resultsDiv = document.getElementById('debugResults');
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = '<div class="loading">🔍 Testing firewall connection...</div>';
            
            fetch('/debug_logs')
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    var html = '<div><h3>🔧 Debug Information</h3>';
                    
                    html += '<h4>API Connectivity:</h4>';
                    if (data.connectivity.success) {
                        html += '<div style="color: green;">✅ ' + data.connectivity.message + '</div>';
                    } else {
                        html += '<div style="color: red;">❌ ' + data.connectivity.error + '</div>';
                    }
                    
                    html += '<h4>Available Log Types:</h4>';
                    html += '<table style="width: 100%; border-collapse: collapse;">';
                    html += '<tr><th style="border: 1px solid #ddd; padding: 8px;">Log Type</th><th style="border: 1px solid #ddd; padding: 8px;">Status</th></tr>';
                    
                    Object.keys(data.log_types).forEach(function(logType) {
                        var status = data.log_types[logType];
                        var statusText = '';
                        var statusColor = 'black';
                        
                        if (typeof status === 'number') {
                            statusColor = status > 0 ? 'green' : 'orange';
                            statusText = status > 0 ? '✅ ' + status + ' entries' : '⚠️ 0 entries';
                        } else if (typeof status === 'string') {
                            if (status.includes('Error') || status.includes('Exception')) {
                                statusColor = 'red';
                                statusText = '❌ ' + status;
                            } else if (status.includes('Found')) {
                                statusColor = 'green';
                                statusText = '✅ ' + status;
                            } else {
                                statusColor = 'orange';
                                statusText = '⚠️ ' + status;
                            }
                        } else {
                            statusText = String(status);
                        }
                        
                        html += '<tr><td style="border: 1px solid #ddd; padding: 8px;">' + logType + '</td>';
                        html += '<td style="border: 1px solid #ddd; padding: 8px; color: ' + statusColor + ';">' + statusText + '</td></tr>';
                    });
                    html += '</table>';
                    html += '</div>';
                    
                    resultsDiv.innerHTML = html;
                } else {
                    resultsDiv.innerHTML = '<div class="error">Debug failed: ' + data.error + '</div>';
                }
            })
            .catch(function(error) {
                resultsDiv.innerHTML = '<div class="error">Debug request failed: ' + error.message + '</div>';
            });
        }
        
        function proceedToCategories() {
            if (selectedUrls.length === 0) {
                alert('Please select at least one URL');
                return;
            }
            activateStep(3);
            loadCategories();
        }
        
        function loadCategories() {
            var categorySelect = document.getElementById('urlCategory');
            categorySelect.innerHTML = '<option value="">Loading categories...</option>';
            
            fetch('/get_categories')
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    categories = data.categories;
                    categorySelect.innerHTML = '<option value="">Select a category...</option>';
                    
                    Object.keys(categories).forEach(function(displayName) {
                        var option = document.createElement('option');
                        option.value = displayName;
                        option.textContent = displayName;
                        categorySelect.appendChild(option);
                    });
                    
                    categorySelect.addEventListener('change', function() {
                        var proceedBtn = document.getElementById('categoryProceedBtn');
                        proceedBtn.style.display = this.value ? 'inline-block' : 'none';
                    });
                } else {
                    categorySelect.innerHTML = '<option value="">Error: ' + data.error + '</option>';
                }
            })
            .catch(function(error) {
                categorySelect.innerHTML = '<option value="">Error: ' + error.message + '</option>';
            });
        }
        
        function proceedToTicket() {
            var categorySelect = document.getElementById('urlCategory');
            if (!categorySelect.value) {
                alert('Please select a URL category');
                return;
            }
            activateStep(4);
            updateFinalSummary();
        }
        
        function updateFinalSummary() {
            var categorySelect = document.getElementById('urlCategory');
            var exactMatch = document.getElementById('exactMatch').checked;
            var wildcardMatch = document.getElementById('wildcardMatch').checked;
            
            var urlsToAdd = [];
            for (var i = 0; i < selectedUrls.length; i++) {
                var url = selectedUrls[i];
                
                if (url.startsWith('*.')) {
                    // Already a wildcard
                    if (wildcardMatch) {
                        urlsToAdd.push(url);
                    }
                    if (exactMatch) {
                        var exactUrl = url.substring(2);
                        if (!exactUrl.endsWith('/')) {
                            exactUrl += '/';
                        }
                        urlsToAdd.push(exactUrl);
                    }
                } else {
                    // Regular domain
                    var domain = url.endsWith('/') ? url : url + '/';
                    if (exactMatch) urlsToAdd.push(domain);
                    if (wildcardMatch) urlsToAdd.push('*.' + domain);
                }
            }
            
            var summaryDiv = document.getElementById('finalSummary');
            var urlsList = '';
            for (var i = 0; i < urlsToAdd.length; i++) {
                urlsList += '<li>' + urlsToAdd[i] + '</li>';
            }
            
            var searchInfo = searchResults.length > 0 ? ' (' + searchResults.length + ' from search' : '';
            var manualInfo = manualUrls.length > 0 ? ', ' + manualUrls.length + ' manual' : '';
            var sourceInfo = searchInfo + manualInfo + (searchInfo ? ')' : '');
            
            summaryDiv.innerHTML = '<div><h3>Summary:</h3>' +
                                  '<p><strong>Search Action:</strong> ' + selectedActionType + '</p>' +
                                  '<p><strong>Category:</strong> ' + categorySelect.value + '</p>' +
                                  '<p><strong>Total URLs selected:</strong> ' + selectedUrls.length + sourceInfo + '</p>' +
                                  '<p><strong>URLs to add:</strong></p><ul>' + urlsList + '</ul></div>';
        }
        
        function submitWhitelist() {
            var ticketId = document.getElementById('ticketId').value.trim();
            if (!ticketId) {
                alert('Please enter a Change/Ticket ID');
                return;
            }
            
            var categorySelect = document.getElementById('urlCategory');
            var exactMatch = document.getElementById('exactMatch').checked;
            var wildcardMatch = document.getElementById('wildcardMatch').checked;
            
            if (!exactMatch && !wildcardMatch) {
                alert('Please select at least one whitelisting option');
                return;
            }
            
            if (!categorySelect.value) {
                alert('Please select a URL category');
                return;
            }
            
            var urlsToAdd = [];
            for (var i = 0; i < selectedUrls.length; i++) {
                var url = selectedUrls[i];
                
                if (url.startsWith('*.')) {
                    // Already a wildcard
                    if (wildcardMatch) {
                        urlsToAdd.push(url);
                    }
                    if (exactMatch) {
                        var exactUrl = url.substring(2);
                        if (!exactUrl.endsWith('/')) {
                            exactUrl += '/';
                        }
                        urlsToAdd.push(exactUrl);
                    }
                } else {
                    // Regular domain
                    var domain = url.endsWith('/') ? url : url + '/';
                    if (exactMatch) urlsToAdd.push(domain);
                    if (wildcardMatch) urlsToAdd.push('*.' + domain);
                }
            }
            
            if (urlsToAdd.length === 0) {
                alert('No URLs to add. Please select some URLs first.');
                return;
            }
            
            var submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Submitting...';
            
            var payload = {
                category: categorySelect.value,
                urls: urlsToAdd,
                ticket_id: ticketId,
                action_type: selectedActionType
            };
            
            console.log('[DEBUG] Submitting whitelist request:', payload);
            
            // Set timeout for submission - increased for server environment
            var submissionTimeout = setTimeout(function() {
                console.log('[DEBUG] Submission taking longer than expected - this is normal for server environment');
                // Don't show timeout message immediately, the server might still be processing
            }, 30000);
            
            fetch('/submit_whitelist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(function(response) {
                clearTimeout(submissionTimeout);
                console.log('[DEBUG] Submit response status:', response.status);
                
                var contentType = response.headers.get('Content-Type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned non-JSON response. Expected JSON but got: ' + (contentType || 'unknown'));
                }
                
                if (!response.ok) {
                    throw new Error('HTTP error! status: ' + response.status);
                }
                
                return response.json();
            })
            .then(function(data) {
                clearTimeout(submissionTimeout);
                console.log('[DEBUG] Submit response data:', data);
                activateStep(5);
                displayResults(data);
            })
            .catch(function(error) {
                clearTimeout(submissionTimeout);
                console.error('[DEBUG] Submit error:', error);
                
                var errorMessage = 'Submission failed: ' + error.message;
                
                if (error.message.includes('non-JSON response')) {
                    errorMessage = 'Server error: The server returned an unexpected response. The submission may still be processing in the background. Please check the commit status manually.';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Network error: Could not connect to the server. Please check your connection and try again.';
                } else if (error.message.includes('string did not match the expected pattern')) {
                    errorMessage = 'Validation error: One of the input values (ticket ID, URLs, or category) contains invalid characters. Please check your inputs and try again.';
                }
                
                activateStep(5);
                var resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="error">' + errorMessage + 
                                     '<br><br><strong>Note:</strong> If you see this error on a server, the whitelist operation may have succeeded in the background. ' +
                                     'Check the server logs for confirmation.</div>';
            })
            .finally(function() {
                clearTimeout(submissionTimeout);
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Enhanced Whitelist Request';
            });
        }
        
        function displayResults(data) {
            var resultsDiv = document.getElementById('results');
            
            if (data.success) {
                var html = '<div class="success">' + data.message + '</div>';
                
                // Show commit status with live updates for immediate responses
                if (data.commit_job_id) {
                    html += '<div class="commit-status" id="commitStatusDiv">';
                    html += '<h3>🔄 Commit Status (Live Updates):</h3>';
                    html += '<p><strong>Job ID:</strong> ' + data.commit_job_id + '</p>';
                    html += '<div id="liveStatus">';
                    
                    if (data.immediate_response) {
                        // Server returned immediately, start live polling
                        html += '<p><strong>Status:</strong> <span style="color: blue;">🔄 SUBMITTED</span></p>';
                        html += '<p><strong>Progress:</strong> <span id="progressText">0%</span></p>';
                        html += '<p id="statusMessage">⏳ Commit started successfully. Checking status...</p>';
                        
                        // Start live polling immediately
                        setTimeout(function() {
                            startLivePolling(data.commit_job_id);
                        }, 1000);
                    } else if (data.auto_commit_status && data.auto_commit_status.auto_polled) {
                        // Backend completed polling
                        var autoStatus = data.auto_commit_status;
                        
                        if (autoStatus.status === 'FIN') {
                            html += '<p><strong>Status:</strong> <span style="color: green;">✅ COMPLETED</span></p>';
                            html += '<p><strong>Progress:</strong> 100%</p>';
                            html += '<p style="color: green;">🎉 Configuration has been successfully committed to the firewall!</p>';
                        } else if (autoStatus.status === 'FAIL' || autoStatus.status === 'ERROR') {
                            html += '<p><strong>Status:</strong> <span style="color: red;">❌ FAILED</span></p>';
                            html += '<p><strong>Progress:</strong> ' + (autoStatus.progress || '0') + '%</p>';
                            html += '<p style="color: red;">⚠️ Commit failed. Please check firewall logs.</p>';
                            if (autoStatus.error) {
                                html += '<p style="color: red; font-size: 12px;">Error: ' + autoStatus.error + '</p>';
                            }
                        } else {
                            html += '<p><strong>Status:</strong> <span style="color: orange;">⏳ ' + autoStatus.status + '</span></p>';
                            html += '<p><strong>Progress:</strong> ' + (autoStatus.progress || '0') + '%</p>';
                            html += '<p>⏳ Still processing...</p>';
                            
                            // Continue live polling for incomplete statuses
                            setTimeout(function() {
                                startLivePolling(data.commit_job_id);
                            }, 2000);
                        }
                    } else {
                        // Fallback - start live polling
                        html += '<p><strong>Status:</strong> <span style="color: blue;">🔄 CHECKING...</span></p>';
                        html += '<p><strong>Progress:</strong> <span id="progressText">0%</span></p>';
                        html += '<p id="statusMessage">⏳ Checking commit status...</p>';
                        
                        setTimeout(function() {
                            startLivePolling(data.commit_job_id);
                        }, 2000);
                    }
                    
                    html += '</div>';
                    html += '<button class="btn" onclick="checkCommitStatus(' + "'" + data.commit_job_id + "'" + ')" id="refreshBtn">Refresh Status</button>';
                    html += '</div>';
                } else {
                    // No commit job ID - show warning
                    html += '<div style="background: #fff3cd; padding: 15px; border-radius: 4px; margin-top: 15px;">';
                    html += '<h3>⚠️ Commit Status Unknown</h3>';
                    html += '<p>URLs were updated successfully, but commit status is not available.</p>';
                    html += '<p>The changes may take effect automatically or may require manual commit.</p>';
                    html += '</div>';
                }
                
                if (data.ticket_log_file) {
                    html += '<div style="background: #e8f5e8; padding: 15px; border-radius: 4px; margin-top: 15px;">';
                    html += '<h3>📋 Ticket Log Created:</h3>';
                    html += '<p><strong>Log File:</strong> ' + data.ticket_log_file + '</p>';
                    html += '<p>✅ Individual ticket log created for audit trail</p>';
                    html += '</div>';
                }
                
                resultsDiv.innerHTML = html;
            } else {
                resultsDiv.innerHTML = '<div class="error">Error: ' + (data.error || 'Unknown error occurred') + '</div>';
            }
        }
        
        var livePollingInterval = null;
        var livePollingAttempts = 0;
        var maxLivePollingAttempts = 50; // 8+ minutes with 10-second intervals
        
        function startLivePolling(jobId) {
            console.log('[DEBUG] Starting live polling for job:', jobId);
            livePollingAttempts = 0;
            
            // Clear any existing interval
            if (livePollingInterval) {
                clearInterval(livePollingInterval);
            }
            
            // Start immediate check
            checkCommitStatusLive(jobId);
            
            // Set up interval for continuous checking
            livePollingInterval = setInterval(function() {
                livePollingAttempts++;
                
                if (livePollingAttempts >= maxLivePollingAttempts) {
                    console.log('[DEBUG] Live polling timeout after', maxLivePollingAttempts, 'attempts');
                    clearInterval(livePollingInterval);
                    updateLiveStatus('TIMEOUT', 'unknown', 'Live polling timed out. Please use the Refresh Status button.');
                    return;
                }
                
                checkCommitStatusLive(jobId);
            }, 12000); // Check every 12 seconds (slightly longer intervals)
        }
        
        function checkCommitStatusLive(jobId) {
            console.log('[DEBUG] Live polling attempt', livePollingAttempts + 1, 'for job:', jobId);
            
            fetch('/commit_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({job_id: jobId})
            })
            .then(function(response) {
                console.log('[DEBUG] Live polling response status:', response.status);
                
                var contentType = response.headers.get('Content-Type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Non-JSON response from server');
                }
                
                if (!response.ok) {
                    throw new Error('HTTP error! status: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                console.log('[DEBUG] Live polling response data:', data);
                
                if (data.success && data.status) {
                    var status = data.status;
                    console.log('[DEBUG] Live status update:', status.status, status.progress + '%');
                    
                    updateLiveStatus(status.status, status.progress, null, status.error);
                    
                    // Stop polling if completed or failed
                    if (status.status === 'FIN' || status.status === 'FAIL' || status.status === 'ERROR') {
                        console.log('[DEBUG] Live polling completed with final status:', status.status);
                        clearInterval(livePollingInterval);
                        
                        // Show final completion message
                        if (status.status === 'FIN') {
                            updateLiveStatus('FIN', '100', '🎉 Configuration has been successfully committed to the firewall!');
                        }
                    }
                } else {
                    console.log('[DEBUG] Live polling: Invalid response structure:', data);
                    updateLiveStatus('ERROR', 'unknown', 'Invalid response from server');
                }
            })
            .catch(function(error) {
                console.error('[DEBUG] Live polling error:', error);
                
                // Don't stop polling on single errors, but show warning
                var errorMsg = 'Status check failed: ' + error.message + ' (retrying...)';
                updateLiveStatus('CHECKING', 'unknown', errorMsg);
                
                // Stop polling after too many consecutive errors
                if (error.message.includes('Non-JSON') || error.message.includes('HTTP error')) {
                    if (livePollingAttempts > 5) {  // Allow a few retries
                        console.log('[DEBUG] Too many errors, stopping live polling');
                        clearInterval(livePollingInterval);
                        updateLiveStatus('ERROR', 'unknown', 'Multiple status check failures. Please use the Refresh Status button.');
                    }
                }
            });
        }
        
        function updateLiveStatus(status, progress, message, error) {
            console.log('[DEBUG] Updating live status:', status, progress + '%', message);
            
            var liveStatusDiv = document.getElementById('liveStatus');
            if (!liveStatusDiv) {
                console.log('[DEBUG] Live status div not found');
                return;
            }
            
            var statusColor = 'orange';
            var statusIcon = '⏳';
            var statusText = status;
            
            if (status === 'FIN') {
                statusColor = 'green';
                statusIcon = '✅';
                statusText = 'COMPLETED';
                if (!message) message = '🎉 Configuration has been successfully committed to the firewall!';
            } else if (status === 'FAIL' || status === 'ERROR') {
                statusColor = 'red';
                statusIcon = '❌';
                statusText = 'FAILED';
                if (!message) message = '⚠️ Commit failed. Please check firewall logs.';
            } else if (status === 'ACT') {
                statusColor = 'blue';
                statusIcon = '🔄';
                statusText = 'ACTIVE';
                if (!message) message = '⚙️ Configuration is being applied to the firewall...';
            } else if (status === 'PEND') {
                statusColor = 'orange';
                statusIcon = '⏳';
                statusText = 'PENDING';
                if (!message) message = '📋 Commit is queued and waiting to start...';
            } else if (status === 'CHECKING') {
                statusColor = 'blue';
                statusIcon = '🔄';
                statusText = 'CHECKING';
                if (!message) message = '🔍 Checking commit status...';
            } else if (status === 'TIMEOUT') {
                statusColor = 'orange';
                statusIcon = '⏰';
                statusText = 'TIMEOUT';
                if (!message) message = '⏰ Live polling timed out. Please check manually.';
            }
            
            // Update the status display
            var newStatusHTML = '<p><strong>Status:</strong> <span style="color: ' + statusColor + ';">' + statusIcon + ' ' + statusText + '</span></p>';
            newStatusHTML += '<p><strong>Progress:</strong> ' + progress + '%</p>';
            newStatusHTML += '<p id="statusMessage">' + message;
            
            if (error) {
                newStatusHTML += '<br><small style="color: red;">Error: ' + error + '</small>';
            }
            
            newStatusHTML += '</p>';
            
            liveStatusDiv.innerHTML = newStatusHTML;
        }
        
        function checkCommitStatus(jobId) {
            console.log('[DEBUG] Manual commit status check for job:', jobId);
            
            fetch('/commit_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({job_id: jobId})
            })
            .then(function(response) {
                console.log('[DEBUG] Manual status response:', response.status);
                
                var contentType = response.headers.get('Content-Type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned non-JSON response for commit status');
                }
                
                if (!response.ok) {
                    throw new Error('HTTP error! status: ' + response.status);
                }
                
                return response.json();
            })
            .then(function(data) {
                console.log('[DEBUG] Manual status data:', data);
                
                if (data.success && data.status) {
                    var status = data.status;
                    console.log('[DEBUG] Manual status result:', status.status, status.progress + '%');
                    
                    // Update the live status display
                    updateLiveStatus(status.status, status.progress, null, status.error);
                    
                    // If completed, stop any live polling
                    if (status.status === 'FIN' || status.status === 'FAIL' || status.status === 'ERROR') {
                        console.log('[DEBUG] Final status reached, stopping live polling');
                        if (livePollingInterval) {
                            clearInterval(livePollingInterval);
                        }
                        
                        // Show completion message
                        if (status.status === 'FIN') {
                            updateLiveStatus('FIN', '100', '🎉 Configuration has been successfully committed to the firewall!');
                        }
                    } else {
                        // Status not complete, restart live polling if not running
                        if (!livePollingInterval) {
                            console.log('[DEBUG] Restarting live polling after manual check');
                            setTimeout(function() {
                                startLivePolling(jobId);
                            }, 2000);
                        }
                    }
                } else {
                    console.error('[DEBUG] Invalid commit status response:', data);
                    updateLiveStatus('ERROR', 'unknown', 'Could not get current status. Invalid response from server.');
                }
            })
            .catch(function(error) {
                console.error('[DEBUG] Manual commit status check failed:', error);
                
                var errorMsg = 'Status check failed: ' + error.message;
                if (error.message.includes('non-JSON response')) {
                    errorMsg = 'Server error: Could not get commit status. The job may still be processing.';
                }
                
                updateLiveStatus('ERROR', 'unknown', errorMsg);
            });
        }
        
        function startOver() {
            window.location.reload();
        }
        
        console.log('[DEBUG] Dashboard script loaded successfully');
    </script>
</body>
</html>
'''

def get_login_template():
    """Get login template with config injected"""
    return LOGIN_TEMPLATE

def get_dashboard_template():
    """Get enhanced dashboard template with config injected"""
    return DASHBOARD_TEMPLATE