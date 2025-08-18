"""
Enhanced HTML Templates for the web interface
Complete file with embedded JavaScript and proper function exports
Added ticket download functionality and optional ticket ID
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
            <small>Version {{ config.VERSION }} - Enhanced Multi-URL Search with Manual Input & Ticket Download</small>
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
        .btn-download { background: #17a2b8; }
        .btn-download:hover { background: #138496; }
        .url-list { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9; }
        .url-category { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background: #f8f9fa; }
        .url-category h4 { margin: 0 0 10px 0; color: #007cba; font-size: 16px; }
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
        .timing-info { background: #fff3cd; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 14px; font-weight: bold; }
        .multi-search-info { background: #e1f5fe; padding: 15px; border-radius: 4px; margin-bottom: 15px; border-left: 4px solid #01579b; }
        .manual-url-section { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 20px; border: 1px solid #dee2e6; }
        .validation-message { margin-top: 10px; padding: 8px; border-radius: 4px; font-size: 14px; }
        .validation-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .validation-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .validation-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .ticket-input-info { background: #e8f4fd; padding: 12px; border-radius: 4px; margin-bottom: 15px; border-left: 4px solid #2196f3; }
        .download-section { background: #f0f8ff; padding: 15px; border-radius: 4px; margin-top: 15px; border: 2px solid #17a2b8; }
        .download-section h3 { color: #17a2b8; margin-top: 0; }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Enhanced URL Whitelisting Dashboard</h1>
        <div class="info">Connected to: {{ session.hostname }} as {{ session.username }} | Version {{ config.VERSION }} - Automatische Suche + URL-Kategorisierung + Bedingter Download</div>
        <a href="{{ url_for('logout') }}" class="btn btn-secondary logout">Logout</a>
    </div>

    <!-- Step 1: Enhanced Search for Blocked URLs -->
    <div class="section step active" id="step1">
        <h2><span class="step-number">1</span>Automatische URL Suche</h2>
        
        <div class="timing-info">
            ⏱️ <strong>Suchdauer:</strong> Jede Suche dauert ca. 6-8 Minuten (beide Aktionstypen automatisch)
        </div>
        
        <div class="multi-search-info">
            🎯 <strong>Automatische Dual-Action Suche:</strong><br>
            • <strong>Automatisch:</strong> Sucht automatisch nach <code>block-url</code> UND <code>block-continue</code><br>
            • <strong>Einzelner Begriff:</strong> Einen Suchbegriff eingeben (z.B. "youtube")<br>
            • <strong>Mehrere Begriffe:</strong> Komma-getrennte Begriffe (z.B. "youtube, facebook, twitch")<br>
            • <strong>OR-Logik:</strong> System verwendet automatisch OR-Logik für mehrere Begriffe<br>
            • <strong>Manuelle URLs:</strong> Zusätzliche URLs nach der Suche manuell hinzufügen<br>
            • <strong>Zeitbereich:</strong> Sucht in den letzten 3 Monaten mit bis zu 3.000 Einträgen
        </div>
        
        <form id="searchForm" onsubmit="return handleSearchSubmit(event);">
            <div class="form-group">
                <label for="search_term">Suchbegriffe (einzeln oder komma-getrennt):</label>
                <input type="text" id="search_term" name="search_term" 
                       placeholder="Beispiele: youtube  ODER  youtube, facebook, activision, playstation">
                <small style="color: #666; font-size: 12px;">
                    💡 Für mehrere Begriffe mit Kommas trennen. System sucht automatisch BEIDE Aktionstypen.
                </small>
            </div>
            
            <div class="filtering-info">
                ℹ️ <strong>Automatische Suche:</strong> Das System sucht automatisch nach beiden Aktionstypen:
                <code>block-url</code> (komplett blockiert) und <code>block-continue</code> (blockiert aber Verbindung fortgesetzt)
            </div>
            
            <button type="submit" class="btn" id="searchButton">Automatische Suche starten (~6-8 Minuten)</button>
            <button type="button" class="btn btn-secondary" onclick="debugLogs()">Debug Verbindung</button>
        </form>
        
        <div id="debugResults" style="display: none; margin-top: 15px;"></div>
    </div>

    <!-- Step 2: Enhanced URL Selection with Category Display -->
    <div class="section step" id="step2">
        <h2><span class="step-number">2</span>URL Auswahl & Manuelle URLs</h2>
        
        <div id="urlSelection">
            <!-- Search results will appear here, organized by category -->
        </div>
        
        <div class="whitelist-options" id="whitelistOptions" style="display: none;">
            <h3>Whitelisting Optionen:</h3>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="exactMatch" checked onchange="updateUrlPreview()"> Exakte Domains hinzufügen (z.B. domain.com/)
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="wildcardMatch" checked onchange="updateUrlPreview()"> Wildcard Domains hinzufügen (z.B. *.domain.com/)
                </label>
            </div>
        </div>
        
        <div class="selected-urls" id="selectedUrlsPreview" style="display: none;">
            <h3>URLs die gewhitelistet werden:</h3>
            <div id="urlPreviewList"></div>
        </div>
        
        <button class="btn" onclick="proceedToCategories()" id="proceedBtn" style="display: none;">Weiter zur Kategorieauswahl</button>
    </div>

    <!-- Step 3: Select Category -->
    <div class="section step" id="step3">
        <h2><span class="step-number">3</span>URL Kategorie auswählen</h2>
        
        <div class="form-group">
            <label for="urlCategory">Custom URL Kategorie wählen:</label>
            <select id="urlCategory" name="urlCategory">
                <option value="">Kategorien werden geladen...</option>
            </select>
        </div>
        
        <button class="btn" onclick="proceedToTicket()" id="categoryProceedBtn" style="display: none;">Weiter</button>
    </div>

    <!-- Step 4: Ticket ID and Final Submission -->
    <div class="section step" id="step4">
        <h2><span class="step-number">4</span>Change Ticket & Absenden</h2>
        
        <div class="ticket-input-info">
            📋 <strong>Ticket ID Information:</strong><br>
            • <strong>Optional:</strong> Leer lassen für automatische Generierung<br>
            • <strong>Auto-Format:</strong> Ticket-27JUL2025-14-30-45 (aktuelles Datum und Zeit)<br>
            • <strong>Eigene ID:</strong> Bei Bedarf eigene Change/Ticket ID eingeben
        </div>
        
        <div class="form-group">
            <label for="ticketId">Change/Ticket ID (Optional - wird automatisch generiert wenn leer):</label>
            <input type="text" id="ticketId" name="ticketId" placeholder="Leer lassen für Auto-Generierung oder eigene ID eingeben (z.B. CHG-2024-001234)">
            <small style="color: #666; font-size: 12px;">
                💡 Auto-generiertes Format: Ticket-27JUL2025-14-30-45 (aktuelles Datum/Zeit)
            </small>
        </div>
        
        <div id="finalSummary"></div>
        
        <button class="btn btn-success" onclick="submitWhitelist()" id="submitBtn">Whitelist Request absenden</button>
    </div>

    <!-- Step 5: Results -->
    <div class="section step" id="step5">
        <h2><span class="step-number">5</span>Ergebnisse</h2>
        <div id="results"></div>
        <button class="btn" onclick="startOver()">Neue Anfrage starten</button>
    </div>

    <script>
        // Global variables
        var selectedUrls = [];
        var searchResults = [];
        var manualUrls = [];
        var categories = {};
        var currentTicketId = null;
        var urlsByCategory = {}; // Store URLs organized by category

        // Prevent form submission from reloading page
        function handleSearchSubmit(event) {
            event.preventDefault();
            event.stopPropagation();
            
            console.log('[DEBUG] Automatische Dual-Action Suche gestartet');
            
            var searchTerms = document.getElementById('search_term').value.trim();
            
            console.log('[DEBUG] Search terms:', searchTerms);
            
            if (!searchTerms) {
                alert('Bitte mindestens einen Suchbegriff eingeben');
                return false;
            }
            
            // Validate search terms
            var terms = searchTerms.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t.length > 0; });
            if (terms.length === 0) {
                alert('Bitte gültige Suchbegriffe eingeben');
                return false;
            }
            
            var resultsDiv = document.getElementById('urlSelection');
            var searchBtn = document.getElementById('searchButton');
            
            console.log('[DEBUG] Starting automatic dual-action search request...');
            
            searchBtn.disabled = true;
            searchBtn.textContent = 'Automatische Suche läuft... (~6-8 min)';
            
            activateStep(2);
            
            // Show different message based on number of terms
            var searchMessage = terms.length === 1 
                ? '🎯 Automatische Suche für "' + terms[0] + '" (block-url UND block-continue)'
                : '🎯 Automatische Multi-Begriff Suche für ' + terms.length + ' Begriffe (' + terms.join(', ') + ') mit OR-Logik (block-url UND block-continue)';
            
            resultsDiv.innerHTML = '<div class="loading">' + searchMessage + '...<br>' +
                                  '<small>⏱️ Läuft bis zu 8 Versuche mit erweiterten Timeouts<br>' +
                                  'Sucht in letzten 3 Monaten, bis zu 3.000 Einträge pro Aktion<br>' +
                                  '<strong>Geschätzte Zeit: ~6-8 Minuten - Bitte warten...</strong></small></div>';
            
            console.log('[DEBUG] Making fetch request to /search_urls with automatic dual search');
            
            fetch('/search_urls', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    search_term: searchTerms,
                    action_type: 'both' // This will be automatically handled
                })
            })
            .then(function(response) {
                console.log('[DEBUG] Got response:', response.status, response.statusText);
                
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
                    console.log('[DEBUG] Automatic dual search successful, found URLs:', data.urls);
                    searchResults = data.urls || [];
                    displaySearchResultsByCategory(searchResults, searchTerms, data.strategy_info);
                    showManualUrlInput();
                } else {
                    console.log('[DEBUG] Search failed:', data.error);
                    var errorMessage = data.error || 'Unknown error occurred';
                    
                    if (errorMessage.includes('no URLs were found') || errorMessage.includes('no matching URLs')) {
                        searchResults = [];
                        displaySearchResultsByCategory([], searchTerms, data.strategy_info);
                        showManualUrlInput();
                    } else {
                        resultsDiv.innerHTML = '<div class="error">Suche Fehler: ' + errorMessage + '</div>';
                        showManualUrlInput();
                    }
                }
            })
            .catch(function(error) {
                console.error('[DEBUG] Fetch error:', error);
                var errorMessage = 'Netzwerk Fehler: ' + error.message;
                
                if (error.message.includes('non-JSON response')) {
                    errorMessage = 'Server Fehler: Server hat unerwartete Antwort gesendet. Bitte Firewall-Verbindung prüfen.';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Verbindungsfehler: Konnte nicht zum Server verbinden. Bitte Netzwerkverbindung prüfen.';
                }
                
                resultsDiv.innerHTML = '<div class="error">' + errorMessage + '</div>';
                showManualUrlInput();
            })
            .finally(function() {
                console.log('[DEBUG] Search request completed');
                searchBtn.disabled = false;
                searchBtn.textContent = 'Automatische Suche starten (~6-8 Minuten)';
            });
            
            return false;
        }
        
        /**
         * Display search results organized by action category
         */
        function displaySearchResultsByCategory(urls, searchTerms, strategyInfo) {
            var resultsDiv = document.getElementById('urlSelection');
            var terms = searchTerms.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t.length > 0; });
            
            var html = '';
            
            if (urls.length === 0) {
                html = '<div style="text-align: center; padding: 20px; color: #666;">' +
                    '<h4>✅ Automatische Suche abgeschlossen - Keine URLs gefunden</h4>';
                
                if (terms.length === 1) {
                    html += '<p>Keine URLs mit "' + terms[0] + '" gefunden für block-url oder block-continue</p>';
                } else {
                    html += '<p>Keine URLs mit den Begriffen (' + terms.join(', ') + ') gefunden für block-url oder block-continue</p>';
                }
                
                html += '<p><small>✅ Automatische Suche erfolgreich abgeschlossen. Sie können unten manuell URLs hinzufügen.</small></p>' +
                    '</div>';
            } else {
                html = '<h3>🎯 Automatische Suche: ' + urls.length + ' URLs gefunden</h3>';
                
                // Show strategy info if available
                if (strategyInfo && strategyInfo.action_results) {
                    var blockUrlCount = strategyInfo.action_results['block-url'] ? strategyInfo.action_results['block-url'].count : 0;
                    var blockContinueCount = strategyInfo.action_results['block-continue'] ? strategyInfo.action_results['block-continue'].count : 0;
                    
                    html += '<div style="margin: 10px 0; padding: 10px; background: #f0f8ff; border-radius: 4px;">' +
                           '✅ <strong>Automatische Dual-Action Ergebnisse:</strong><br>' +
                           '🚫 <strong>block-url:</strong> ' + blockUrlCount + ' URLs (komplett blockiert)<br>' +
                           '⚠️ <strong>block-continue:</strong> ' + blockContinueCount + ' URLs (blockiert aber Verbindung fortgesetzt)<br>' +
                           '📅 <strong>Zeitbereich:</strong> Letzte 3 Monate, bis zu 3.000 Einträge pro Aktion<br>' +
                           'Wählen Sie die URLs aus, die Sie whitelisten möchten:</div>';
                    
                    // Organize URLs by action type for display
                    urlsByCategory = {
                        'block-url': strategyInfo.action_results['block-url'] ? strategyInfo.action_results['block-url'].urls : [],
                        'block-continue': strategyInfo.action_results['block-continue'] ? strategyInfo.action_results['block-continue'].urls : []
                    };
                    
                    // Display URLs by category
                    if (urlsByCategory['block-url'].length > 0) {
                        html += '<div class="url-category">';
                        html += '<h4>🚫 block-url (' + urlsByCategory['block-url'].length + ' URLs)</h4>';
                        html += '<small style="color: #666;">URLs die komplett blockiert wurden</small>';
                        for (var i = 0; i < urlsByCategory['block-url'].length; i++) {
                            var url = urlsByCategory['block-url'][i];
                            var uniqueId = 'blockurl_' + i;
                            html += '<div class="url-item">';
                            html += '<input type="checkbox" id="' + uniqueId + '" value="' + url + '" onchange="updateSelectedUrls()">';
                            html += '<label for="' + uniqueId + '">' + url + '</label>';
                            html += '</div>';
                        }
                        html += '</div>';
                    }
                    
                    if (urlsByCategory['block-continue'].length > 0) {
                        html += '<div class="url-category">';
                        html += '<h4>⚠️ block-continue (' + urlsByCategory['block-continue'].length + ' URLs)</h4>';
                        html += '<small style="color: #666;">URLs die blockiert wurden aber Verbindung fortgesetzt</small>';
                        for (var i = 0; i < urlsByCategory['block-continue'].length; i++) {
                            var url = urlsByCategory['block-continue'][i];
                            var uniqueId = 'blockcontinue_' + i;
                            html += '<div class="url-item">';
                            html += '<input type="checkbox" id="' + uniqueId + '" value="' + url + '" onchange="updateSelectedUrls()">';
                            html += '<label for="' + uniqueId + '">' + url + '</label>';
                            html += '</div>';
                        }
                        html += '</div>';
                    }
                } else {
                    // Fallback for older format
                    html += '<div style="margin: 10px 0; padding: 10px; background: #f0f8ff; border-radius: 4px;">' +
                           '✅ <strong>Suchergebnisse:</strong> Automatische Suche für block-url und block-continue<br>' +
                           'Wählen Sie die URLs aus, die Sie whitelisten möchten:</div>';
                    
                    for (var i = 0; i < urls.length; i++) {
                        var url = urls[i];
                        html += '<div class="url-item">';
                        html += '<input type="checkbox" id="url_' + i + '" value="' + url + '" onchange="updateSelectedUrls()">';
                        html += '<label for="url_' + i + '">' + url + '</label>';
                        html += '</div>';
                    }
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
                                '<h4>📝 Manuelle URLs hinzufügen</h4>' +
                                '<p>Sie können auch URLs manuell hinzufügen (eine pro Zeile oder komma-getrennt):</p>' +
                                '<textarea id="manualUrls" placeholder="Beispiel:&#10;youtube.com&#10;facebook.com&#10;*.google.com&#10;oder: youtube.com, facebook.com, *.google.com" ' +
                                'style="width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace;"></textarea>' +
                                '<div id="manualUrlValidation" style="margin-top: 10px;"></div>' +
                                '<button type="button" class="btn" onclick="addManualUrls()" style="margin-top: 10px;">Manuelle URLs hinzufügen</button>' +
                                '</div>';
                urlSelection.insertAdjacentHTML('afterend', manualHtml);
                
                var manualUrlInput = document.getElementById('manualUrls');
                if (manualUrlInput) {
                    manualUrlInput.addEventListener('input', validateManualUrls);
                }
            }
        }
        
        function updateSelectedUrls() {
            console.log('[DEBUG] Updating selected URLs');
            selectedUrls = [];
            
            // Add selected URLs from both categories
            var allCheckboxes = document.querySelectorAll('input[type="checkbox"][id^="blockurl_"], input[type="checkbox"][id^="blockcontinue_"], input[type="checkbox"][id^="url_"]');
            allCheckboxes.forEach(function(checkbox) {
                if (checkbox.checked) {
                    selectedUrls.push(checkbox.value);
                }
            });
            
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
                
                if (url.startsWith('*.')) {
                    if (wildcardMatch) {
                        html += '<li>' + url + '</li>';
                    }
                    if (exactMatch) {
                        var exactUrl = url.substring(2);
                        if (!exactUrl.endsWith('/')) {
                            exactUrl += '/';
                        }
                        html += '<li>' + exactUrl + '</li>';
                    }
                } else {
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
                        html += '<div style="color: green;">✅ Gültige URLs (' + data.valid_urls.length + '): ' + data.valid_urls.join(', ') + '</div>';
                    }
                    if (data.invalid_urls && data.invalid_urls.length > 0) {
                        html += '<div style="color: red;">❌ Ungültige URLs (' + data.invalid_urls.length + '): ' + data.invalid_urls.join(', ') + '</div>';
                    }
                    validationDiv.innerHTML = html;
                }
            })
            .catch(function(error) {
                validationDiv.innerHTML = '<div style="color: orange;">⚠️ Validierung vorübergehend nicht verfügbar</div>';
            });
        }
        
        function addManualUrls() {
            var input = document.getElementById('manualUrls').value.trim();
            if (!input) {
                alert('Bitte URLs eingeben');
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
                    data.valid_urls.forEach(function(url) {
                        if (manualUrls.indexOf(url) === -1) {
                            manualUrls.push(url);
                        }
                    });
                    
                    document.getElementById('manualUrls').value = '';
                    document.getElementById('manualUrlValidation').innerHTML = '';
                    
                    displayManualUrls();
                    updateSelectedUrls();
                    
                    alert(data.valid_urls.length + ' gültige URLs zur Auswahl hinzugefügt');
                    
                    if (data.invalid_urls && data.invalid_urls.length > 0) {
                        alert('Hinweis: ' + data.invalid_urls.length + ' ungültige URLs ignoriert: ' + data.invalid_urls.join(', '));
                    }
                } else {
                    alert('Keine gültigen URLs gefunden. Bitte Eingabe prüfen.');
                }
            })
            .catch(function(error) {
                alert('Fehler bei URL-Validierung: ' + error.message);
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
                          '<h5>📋 Manuelle URLs (' + manualUrls.length + '):</h5>';
                
                for (var i = 0; i < manualUrls.length; i++) {
                    html += '<div style="margin: 5px 0; padding: 5px; background: white; border-radius: 3px; display: flex; align-items: center;">' +
                           '<input type="checkbox" id="manual_' + i + '" checked style="margin-right: 10px;" onchange="updateSelectedUrls()">' +
                           '<span style="flex: 1;">' + manualUrls[i] + '</span>' +
                           '<button onclick="removeManualUrl(' + i + ')" style="padding: 2px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer;">Entfernen</button>' +
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
            resultsDiv.innerHTML = '<div class="loading">🔍 Teste Firewall-Verbindung...</div>';
            
            fetch('/debug_logs')
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    var html = '<div><h3>🔧 Debug Information</h3>';
                    
                    html += '<h4>API Konnektivität:</h4>';
                    if (data.connectivity.success) {
                        html += '<div style="color: green;">✅ ' + data.connectivity.message + '</div>';
                    } else {
                        html += '<div style="color: red;">❌ ' + data.connectivity.error + '</div>';
                    }
                    
                    html += '<h4>Verfügbare Log-Typen:</h4>';
                    html += '<table style="width: 100%; border-collapse: collapse;">';
                    html += '<tr><th style="border: 1px solid #ddd; padding: 8px;">Log Typ</th><th style="border: 1px solid #ddd; padding: 8px;">Status</th></tr>';
                    
                    Object.keys(data.log_types).forEach(function(logType) {
                        var status = data.log_types[logType];
                        var statusText = '';
                        var statusColor = 'black';
                        
                        if (typeof status === 'number') {
                            statusColor = status > 0 ? 'green' : 'orange';
                            statusText = status > 0 ? '✅ ' + status + ' Einträge' : '⚠️ 0 Einträge';
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
                    
                    if (data.enhanced_features) {
                        html += '<h4>Erweiterte Features:</h4>';
                        html += '<ul>';
                        if (data.enhanced_features.multi_term_search) {
                            html += '<li>✅ Multi-Begriff OR-Logik Suche</li>';
                        }
                        if (data.enhanced_features.manual_url_input) {
                            html += '<li>✅ Manuelle URL Eingabe</li>';
                        }
                        if (data.enhanced_features.automatic_ticket_generation) {
                            html += '<li>✅ Automatische Ticket-ID Generierung</li>';
                        }
                        if (data.enhanced_features.ticket_download) {
                            html += '<li>✅ Ticket-Log Download</li>';
                        }
                        html += '</ul>';
                    }
                    
                    html += '</div>';
                    
                    resultsDiv.innerHTML = html;
                } else {
                    resultsDiv.innerHTML = '<div class="error">Debug fehlgeschlagen: ' + data.error + '</div>';
                }
            })
            .catch(function(error) {
                resultsDiv.innerHTML = '<div class="error">Debug-Anfrage fehlgeschlagen: ' + error.message + '</div>';
            });
        }
        
        function proceedToCategories() {
            if (selectedUrls.length === 0) {
                alert('Bitte mindestens eine URL auswählen');
                return;
            }
            activateStep(3);
            loadCategories();
        }
        
        function loadCategories() {
            var categorySelect = document.getElementById('urlCategory');
            categorySelect.innerHTML = '<option value="">Kategorien werden geladen...</option>';
            
            fetch('/get_categories')
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    categories = data.categories;
                    categorySelect.innerHTML = '<option value="">Kategorie auswählen...</option>';
                    
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
                    categorySelect.innerHTML = '<option value="">Fehler: ' + data.error + '</option>';
                }
            })
            .catch(function(error) {
                categorySelect.innerHTML = '<option value="">Fehler: ' + error.message + '</option>';
            });
        }
        
        function proceedToTicket() {
            var categorySelect = document.getElementById('urlCategory');
            if (!categorySelect.value) {
                alert('Bitte eine URL-Kategorie auswählen');
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
            
            var searchInfo = searchResults.length > 0 ? ' (' + searchResults.length + ' aus Suche' : '';
            var manualInfo = manualUrls.length > 0 ? ', ' + manualUrls.length + ' manuell' : '';
            var sourceInfo = searchInfo + manualInfo + (searchInfo ? ')' : '');
            
            summaryDiv.innerHTML = '<div><h3>Zusammenfassung:</h3>' +
                                  '<p><strong>Kategorie:</strong> ' + categorySelect.value + '</p>' +
                                  '<p><strong>URLs ausgewählt:</strong> ' + selectedUrls.length + sourceInfo + '</p>' +
                                  '<p><strong>URLs hinzuzufügen:</strong></p><ul>' + urlsList + '</ul></div>';
        }
        
        function submitWhitelist() {
            var ticketId = document.getElementById('ticketId').value.trim();
            var categorySelect = document.getElementById('urlCategory');
            var exactMatch = document.getElementById('exactMatch').checked;
            var wildcardMatch = document.getElementById('wildcardMatch').checked;
            
            if (!exactMatch && !wildcardMatch) {
                alert('Bitte mindestens eine Whitelisting-Option auswählen');
                return;
            }
            
            if (!categorySelect.value) {
                alert('Bitte eine URL-Kategorie auswählen');
                return;
            }
            
            var urlsToAdd = [];
            for (var i = 0; i < selectedUrls.length; i++) {
                var url = selectedUrls[i];
                
                if (url.startsWith('*.')) {
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
                    var domain = url.endsWith('/') ? url : url + '/';
                    if (exactMatch) urlsToAdd.push(domain);
                    if (wildcardMatch) urlsToAdd.push('*.' + domain);
                }
            }
            
            if (urlsToAdd.length === 0) {
                alert('Keine URLs zum Hinzufügen. Bitte erst URLs auswählen.');
                return;
            }
            
            var submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Wird abgesendet...';
            
            var payload = {
                category: categorySelect.value,
                urls: urlsToAdd,
                ticket_id: ticketId,
                action_type: 'both'
            };
            
            console.log('[DEBUG] Submitting whitelist request:', payload);
            
            var submissionTimeout = setTimeout(function() {
                console.log('[DEBUG] Submission taking longer than expected');
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
                
                if (data.ticket_id) {
                    currentTicketId = data.ticket_id;
                }
                
                activateStep(5);
                displayResults(data);
            })
            .catch(function(error) {
                clearTimeout(submissionTimeout);
                console.error('[DEBUG] Submit error:', error);
                
                var errorMessage = 'Absendung fehlgeschlagen: ' + error.message;
                
                if (error.message.includes('non-JSON response')) {
                    errorMessage = 'Server Fehler: Server hat unerwartete Antwort gesendet. Die Absendung könnte im Hintergrund noch laufen.';
                } else if (error.message.includes('Failed to fetch')) {
                    errorMessage = 'Netzwerkfehler: Konnte nicht zum Server verbinden. Bitte Verbindung prüfen.';
                }
                
                activateStep(5);
                var resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="error">' + errorMessage + '</div>';
            })
            .finally(function() {
                clearTimeout(submissionTimeout);
                submitBtn.disabled = false;
                submitBtn.textContent = 'Whitelist Request absenden';
            });
        }
        
        function downloadTicket(ticketId) {
            console.log('[DEBUG] Downloading ticket:', ticketId);
            
            if (!ticketId) {
                alert('Keine Ticket-ID für Download verfügbar');
                return;
            }
            
            var downloadUrl = '/download_ticket/' + encodeURIComponent(ticketId);
            
            var link = document.createElement('a');
            link.href = downloadUrl;
            link.download = 'ticket_' + ticketId + '.log';
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log('[DEBUG] Download initiated for ticket:', ticketId);
        }
        
        function displayResults(data) {
            var resultsDiv = document.getElementById('results');
            
            if (data.success) {
                var html = '<div class="success">' + data.message + '</div>';
                
                var ticketId = data.ticket_id || currentTicketId;
                
                // Show commit status with live updates
                if (data.commit_job_id) {
                    html += '<div class="commit-status" id="commitStatusDiv">';
                    html += '<h3>🔄 Commit Status (Live Updates):</h3>';
                    html += '<p><strong>Job ID:</strong> ' + data.commit_job_id + '</p>';
                    html += '<div id="liveStatus">';
                    
                    if (data.immediate_response) {
                        html += '<p><strong>Status:</strong> <span style="color: blue;">🔄 ÜBERMITTELT</span></p>';
                        html += '<p><strong>Fortschritt:</strong> <span id="progressText">0%</span></p>';
                        html += '<p id="statusMessage">⏳ Commit erfolgreich gestartet. Status wird geprüft...</p>';
                        
                        setTimeout(function() {
                            startLivePolling(data.commit_job_id);
                        }, 1000);
                    } else if (data.auto_commit_status && data.auto_commit_status.auto_polled) {
                        var autoStatus = data.auto_commit_status;
                        
                        if (autoStatus.status === 'FIN') {
                            html += '<p><strong>Status:</strong> <span style="color: green;">✅ ABGESCHLOSSEN</span></p>';
                            html += '<p><strong>Fortschritt:</strong> 100%</p>';
                            html += '<p style="color: green;">🎉 Konfiguration wurde erfolgreich an die Firewall übertragen!</p>';
                        } else if (autoStatus.status === 'FAIL' || autoStatus.status === 'ERROR') {
                            html += '<p><strong>Status:</strong> <span style="color: red;">❌ FEHLGESCHLAGEN</span></p>';
                            html += '<p><strong>Fortschritt:</strong> ' + (autoStatus.progress || '0') + '%</p>';
                            html += '<p style="color: red;">⚠️ Commit fehlgeschlagen. Bitte Firewall-Logs prüfen.</p>';
                        } else {
                            html += '<p><strong>Status:</strong> <span style="color: orange;">⏳ ' + autoStatus.status + '</span></p>';
                            html += '<p><strong>Fortschritt:</strong> ' + (autoStatus.progress || '0') + '%</p>';
                            html += '<p>⏳ Wird noch verarbeitet...</p>';
                            
                            setTimeout(function() {
                                startLivePolling(data.commit_job_id);
                            }, 2000);
                        }
                    } else {
                        html += '<p><strong>Status:</strong> <span style="color: blue;">🔄 WIRD GEPRÜFT...</span></p>';
                        html += '<p><strong>Fortschritt:</strong> <span id="progressText">0%</span></p>';
                        html += '<p id="statusMessage">⏳ Commit-Status wird geprüft...</p>';
                        
                        setTimeout(function() {
                            startLivePolling(data.commit_job_id);
                        }, 2000);
                    }
                    
                    html += '</div>';
                    html += '<button class="btn" onclick="checkCommitStatus(' + "'" + data.commit_job_id + "'" + ')" id="refreshBtn">Status aktualisieren</button>';
                    html += '</div>';
                } else {
                    html += '<div style="background: #fff3cd; padding: 15px; border-radius: 4px; margin-top: 15px;">';
                    html += '<h3>⚠️ Commit-Status unbekannt</h3>';
                    html += '<p>URLs wurden erfolgreich aktualisiert, aber Commit-Status ist nicht verfügbar.</p>';
                    html += '</div>';
                }
                
                // Add download section - ONLY show when commit is at 100%
                if (ticketId) {
                    html += '<div class="download-section hidden" id="downloadSection">';
                    html += '<h3>📥 Ticket-Log herunterladen</h3>';
                    html += '<p><strong>Ticket ID:</strong> ' + ticketId + '</p>';
                    html += '<p>Laden Sie die vollständige Ticket-Log-Datei für Ihre Unterlagen und Audit-Trail herunter.</p>';
                    html += '<button class="btn btn-download" onclick="downloadTicket(' + "'" + ticketId + "'" + ')">📥 Ticket-Log herunterladen</button>';
                    html += '</div>';
                }
                
                if (data.ticket_log_file) {
                    html += '<div style="background: #e8f5e8; padding: 15px; border-radius: 4px; margin-top: 15px;">';
                    html += '<h3>📋 Ticket-Log erstellt:</h3>';
                    html += '<p><strong>Log-Datei:</strong> ' + data.ticket_log_file + '</p>';
                    html += '<p>✅ Individuelle Ticket-Log für Audit-Trail erstellt</p>';
                    html += '</div>';
                }
                
                resultsDiv.innerHTML = html;
            } else {
                resultsDiv.innerHTML = '<div class="error">Fehler: ' + (data.error || 'Unbekannter Fehler aufgetreten') + '</div>';
            }
        }
        
        // Live polling functionality
        var livePollingInterval = null;
        var livePollingAttempts = 0;
        var maxLivePollingAttempts = 50;
        
        function startLivePolling(jobId) {
            console.log('[DEBUG] Starting live polling for job:', jobId);
            livePollingAttempts = 0;
            
            if (livePollingInterval) {
                clearInterval(livePollingInterval);
            }
            
            checkCommitStatusLive(jobId);
            
            livePollingInterval = setInterval(function() {
                livePollingAttempts++;
                
                if (livePollingAttempts >= maxLivePollingAttempts) {
                    console.log('[DEBUG] Live polling timeout');
                    clearInterval(livePollingInterval);
                    updateLiveStatus('TIMEOUT', 'unknown', 'Live-Polling Timeout. Bitte Status-Button verwenden.');
                    return;
                }
                
                checkCommitStatusLive(jobId);
            }, 12000);
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
                if (!response.ok) {
                    throw new Error('HTTP error! status: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                if (data.success && data.status) {
                    var status = data.status;
                    console.log('[DEBUG] Live status update:', status.status, status.progress + '%');
                    
                    updateLiveStatus(status.status, status.progress, null, status.error);
                    
                    // Show download section when commit reaches 100%
                    if (status.status === 'FIN' && status.progress === '100') {
                        var downloadSection = document.getElementById('downloadSection');
                        if (downloadSection) {
                            downloadSection.classList.remove('hidden');
                        }
                    }
                    
                    if (status.status === 'FIN' || status.status === 'FAIL' || status.status === 'ERROR') {
                        console.log('[DEBUG] Live polling completed with final status:', status.status);
                        clearInterval(livePollingInterval);
                        
                        if (status.status === 'FIN') {
                            updateLiveStatus('FIN', '100', '🎉 Konfiguration wurde erfolgreich an die Firewall übertragen!');
                        }
                    }
                }
            })
            .catch(function(error) {
                console.error('[DEBUG] Live polling error:', error);
                updateLiveStatus('CHECKING', 'unknown', 'Status-Prüfung fehlgeschlagen: ' + error.message + ' (wird wiederholt...)');
            });
        }
        
        function updateLiveStatus(status, progress, message, error) {
            console.log('[DEBUG] Updating live status:', status, progress + '%', message);
            
            var liveStatusDiv = document.getElementById('liveStatus');
            if (!liveStatusDiv) {
                return;
            }
            
            var statusColor = 'orange';
            var statusIcon = '⏳';
            var statusText = status;
            
            if (status === 'FIN') {
                statusColor = 'green';
                statusIcon = '✅';
                statusText = 'ABGESCHLOSSEN';
                if (!message) message = '🎉 Konfiguration wurde erfolgreich an die Firewall übertragen!';
            } else if (status === 'FAIL' || status === 'ERROR') {
                statusColor = 'red';
                statusIcon = '❌';
                statusText = 'FEHLGESCHLAGEN';
                if (!message) message = '⚠️ Commit fehlgeschlagen. Bitte Firewall-Logs prüfen.';
            } else if (status === 'ACT') {
                statusColor = 'blue';
                statusIcon = '🔄';
                statusText = 'AKTIV';
                if (!message) message = '⚙️ Konfiguration wird auf Firewall angewendet...';
            } else if (status === 'PEND') {
                statusColor = 'orange';
                statusIcon = '⏳';
                statusText = 'WARTEND';
                if (!message) message = '📋 Commit ist in der Warteschlange...';
            }
            
            var newStatusHTML = '<p><strong>Status:</strong> <span style="color: ' + statusColor + ';">' + statusIcon + ' ' + statusText + '</span></p>';
            newStatusHTML += '<p><strong>Fortschritt:</strong> ' + progress + '%</p>';
            newStatusHTML += '<p id="statusMessage">' + message;
            
            if (error) {
                newStatusHTML += '<br><small style="color: red;">Fehler: ' + error + '</small>';
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
                if (!response.ok) {
                    throw new Error('HTTP error! status: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                if (data.success && data.status) {
                    var status = data.status;
                    updateLiveStatus(status.status, status.progress, null, status.error);
                    
                    // Show download section when commit reaches 100%
                    if (status.status === 'FIN' && status.progress === '100') {
                        var downloadSection = document.getElementById('downloadSection');
                        if (downloadSection) {
                            downloadSection.classList.remove('hidden');
                        }
                    }
                    
                    if (status.status === 'FIN' || status.status === 'FAIL' || status.status === 'ERROR') {
                        if (livePollingInterval) {
                            clearInterval(livePollingInterval);
                        }
                        
                        if (status.status === 'FIN') {
                            updateLiveStatus('FIN', '100', '🎉 Konfiguration wurde erfolgreich an die Firewall übertragen!');
                        }
                    }
                }
            })
            .catch(function(error) {
                console.error('[DEBUG] Manual commit status check failed:', error);
                updateLiveStatus('ERROR', 'unknown', 'Status-Prüfung fehlgeschlagen: ' + error.message);
            });
        }
        
        function startOver() {
            window.location.reload();
        }
        
        console.log('[DEBUG] Dashboard script loaded - Enhanced with automatic dual search, category display, and conditional download');
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