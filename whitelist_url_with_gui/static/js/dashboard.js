/**
 * Enhanced Dashboard JavaScript for Palo Alto Whitelist Tool
 * Fixed error handling and status checking
 * Added live ticket log updates for commit status
 * Complete version with all functions
 */

// Global variables
var selectedUrls = [];
var searchResults = [];
var manualUrls = [];
var categories = {};
var selectedActionType = 'block-url';
var currentTicketId = null; // Store current ticket ID for download

/**
 * Initialize the dashboard when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] Enhanced Dashboard initialized with live ticket updates');
    
    // Attach event listeners
    var searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }
    
    var exactMatch = document.getElementById('exactMatch');
    var wildcardMatch = document.getElementById('wildcardMatch');
    if (exactMatch) exactMatch.addEventListener('change', updateUrlPreview);
    if (wildcardMatch) wildcardMatch.addEventListener('change', updateUrlPreview);
    
    // Add manual URL input handlers
    var manualUrlInput = document.getElementById('manualUrls');
    if (manualUrlInput) {
        manualUrlInput.addEventListener('input', validateManualUrls);
    }
});

/**
 * Handle search form submission with better error handling
 */
function handleSearchSubmit(e) {
    e.preventDefault();
    console.log('[DEBUG] Search form submitted with enhanced multi-term strategy');
    
    var searchTerms = document.getElementById('search_term').value.trim();
    selectedActionType = document.querySelector('input[name="action_type"]:checked').value;
    
    console.log('[DEBUG] Search terms:', searchTerms);
    console.log('[DEBUG] Action type:', selectedActionType);
    
    if (!searchTerms) {
        alert('Please enter at least one search term');
        return;
    }
    
    // Validate search terms
    var terms = searchTerms.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t.length > 0; });
    if (terms.length === 0) {
        alert('Please enter valid search terms');
        return;
    }
    
    var resultsDiv = document.getElementById('urlSelection');
    var searchBtn = e.target.querySelector('button[type="submit"]');
    
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
            showManualUrlInput(); // Show manual URL input after search
        } else {
            console.log('[DEBUG] Search failed:', data.error);
            var errorMessage = data.error || 'Unknown error occurred';
            
            // Don't treat "no URLs found" as an error in the UI
            if (errorMessage.includes('no URLs were found') || errorMessage.includes('no matching URLs')) {
                // This is actually a successful search with no results
                searchResults = [];
                displaySearchResults([], searchTerms, selectedActionType, data.debug_info);
                showManualUrlInput();
            } else {
                // This is a real error
                resultsDiv.innerHTML = '<div class="error">Search Error: ' + errorMessage + '</div>';
                showManualUrlInput(); // Still show manual URL input
            }
        }
    })
    .catch(function(error) {
        console.error('[DEBUG] Fetch error:', error);
        var errorMessage = 'Network error: ' + error.message;
        
        // Provide helpful error messages
        if (error.message.includes('non-JSON response')) {
            errorMessage = 'Server error: The server returned an unexpected response. Please check your firewall connection and try again.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Connection error: Could not connect to the server. Please check your network connection.';
        }
        
        resultsDiv.innerHTML = '<div class="error">' + errorMessage + '</div>';
        showManualUrlInput(); // Show manual URL input on network error
    })
    .finally(function() {
        console.log('[DEBUG] Search request completed');
        searchBtn.disabled = false;
        searchBtn.textContent = 'Start Enhanced Search (~3-4 minutes)';
    });
}

/**
 * Display search results with enhanced information
 */
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
        
        html += '<p><small>✅ Search completed successfully. You can still add URLs manually below.</small></p>' +
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
    
    // Add click handlers for labels
    setTimeout(function() {
        for (var i = 0; i < urls.length; i++) {
            attachLabelClickHandler(i);
        }
    }, 100);
}

/**
 * Show manual URL input section
 */
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

/**
 * Validate manual URLs as user types
 */
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

/**
 * Add manual URLs to the selection
 */
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

/**
 * Display manual URLs
 */
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

/**
 * Remove manual URL
 */
function removeManualUrl(index) {
    manualUrls.splice(index, 1);
    displayManualUrls();
    updateSelectedUrls();
}

/**
 * Attach click handler to labels
 */
function attachLabelClickHandler(index) {
    var label = document.querySelector('label[for="url_' + index + '"]');
    var checkbox = document.getElementById('url_' + index);
    
    if (label && checkbox) {
        label.addEventListener('click', function(e) {
            var targetId = e.target.getAttribute('for');
            var targetCheckbox = document.getElementById(targetId);
            if (targetCheckbox) {
                targetCheckbox.checked = !targetCheckbox.checked;
                updateSelectedUrls();
            }
        });
    }
}

/**
 * Update selected URLs (both search results and manual URLs)
 */
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

/**
 * Update URL preview
 */
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

/**
 * Proceed to categories selection
 */
function proceedToCategories() {
    if (selectedUrls.length === 0) {
        alert('Please select at least one URL');
        return;
    }
    activateStep(3);
    loadCategories();
}

/**
 * Load categories from server
 */
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

/**
 * Proceed to ticket input
 */
function proceedToTicket() {
    var categorySelect = document.getElementById('urlCategory');
    if (!categorySelect.value) {
        alert('Please select a URL category');
        return;
    }
    activateStep(4);
    updateFinalSummary();
}

/**
 * Update final summary
 */
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

/**
 * Submit whitelist request with enhanced error handling
 */
function submitWhitelist() {
    var ticketId = document.getElementById('ticketId').value.trim();
    var categorySelect = document.getElementById('urlCategory');
    var exactMatch = document.getElementById('exactMatch').checked;
    var wildcardMatch = document.getElementById('wildcardMatch').checked;
    
    // Note: ticketId is now optional and will be auto-generated if empty
    
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
        ticket_id: ticketId, // Can be empty for auto-generation
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
        
        // Store ticket ID for download
        if (data.ticket_id) {
            currentTicketId = data.ticket_id;
        }
        
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

/**
 * Download ticket log file
 */
function downloadTicket(ticketId) {
    console.log('[DEBUG] Downloading ticket:', ticketId);
    
    if (!ticketId) {
        alert('No ticket ID available for download');
        return;
    }
    
    // Create download link and trigger download
    var downloadUrl = '/download_ticket/' + encodeURIComponent(ticketId);
    
    // Create temporary link element and click it
    var link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'ticket_' + ticketId + '.log';
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('[DEBUG] Download initiated for ticket:', ticketId);
}

/**
 * Update ticket log with final commit status
 */
function updateTicketLogStatus(commitStatus, commitProgress) {
    console.log('[DEBUG] Updating ticket log with final status:', commitStatus, commitProgress);
    
    // Only update for final statuses
    if (!['FIN', 'FAIL', 'ERROR'].includes(commitStatus)) {
        console.log('[DEBUG] Not a final status, skipping ticket log update');
        return;
    }
    
    fetch('/update_ticket_commit_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            commit_status: commitStatus,
            commit_progress: commitProgress
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            console.log('[DEBUG] Ticket log successfully updated with final status');
        } else {
            console.log('[DEBUG] Failed to update ticket log:', data.error);
        }
    })
    .catch(function(error) {
        console.error('[DEBUG] Error updating ticket log:', error);
    });
}

/**
 * Display submission results with better error handling
 */
function displayResults(data) {
    var resultsDiv = document.getElementById('results');
    
    if (data.success) {
        var html = '<div class="success">' + data.message + '</div>';
        
        // Store ticket ID for download functionality
        var ticketId = data.ticket_id || currentTicketId;
        
        // Add download section if ticket ID available
        if (ticketId) {
            html += '<div class="download-section">';
            html += '<h3>📥 Download Ticket Log</h3>';
            html += '<p><strong>Ticket ID:</strong> ' + ticketId + '</p>';
            html += '<p>Download the complete ticket log file for your records and audit trail.</p>';
            html += '<button class="btn btn-download" onclick="downloadTicket(' + "'" + ticketId + "'" + ')">📥 Download Ticket Log</button>';
            html += '</div>';
        }
        
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

/**
 * Check commit status with better error handling and ticket log updates
 */
function checkCommitStatus(jobId) {
    console.log('[DEBUG] Checking commit status for job:', jobId);
    
    fetch('/commit_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({job_id: jobId})
    })
    .then(function(response) {
        console.log('[DEBUG] Commit status response:', response.status);
        
        // Check if response is JSON
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
        console.log('[DEBUG] Commit status data:', data);
        
        var statusDiv = document.querySelector('.commit-status');
        if (data.success && statusDiv && data.status) {
            var status = data.status;
            var statusHTML = '<h3>🔄 Commit Status (Updated):</h3>';
            statusHTML += '<p><strong>Job ID:</strong> ' + jobId + '</p>';
            statusHTML += '<p><strong>Status:</strong> ' + status.status + '</p>';
            statusHTML += '<p><strong>Progress:</strong> ' + status.progress + '%</p>';
            
            if (status.status === 'FIN') {
                statusHTML += '<p style="color: green;">✅ Commit completed successfully!</p>';
                // Update ticket log with final status
                updateTicketLogStatus('FIN', status.progress);
            } else if (status.status === 'FAIL' || status.status === 'ERROR') {
                statusHTML += '<p style="color: red;">❌ Commit failed</p>';
                if (status.error) {
                    statusHTML += '<p style="color: red; font-size: 12px;">Error: ' + status.error + '</p>';
                }
                // Update ticket log with final status
                updateTicketLogStatus(status.status, status.progress);
            } else if (status.status !== 'FIN') {
                statusHTML += '<button class="btn" onclick="checkCommitStatus(' + "'" + jobId + "'" + ')">Refresh Status</button>';
            }
            
            statusDiv.innerHTML = statusHTML;
        } else {
            console.error('[DEBUG] Invalid commit status response:', data);
            var statusDiv = document.querySelector('.commit-status');
            if (statusDiv) {
                statusDiv.innerHTML = '<p style="color: orange;">⚠️ Could not get current status. Job may still be processing.</p>';
            }
        }
    })
    .catch(function(error) {
        console.error('[DEBUG] Commit status check failed:', error);
        var statusDiv = document.querySelector('.commit-status');
        if (statusDiv) {
            var errorMsg = 'Status check failed: ' + error.message;
            if (error.message.includes('non-JSON response')) {
                errorMsg = 'Server error: Could not get commit status. The job may still be processing.';
            }
            statusDiv.innerHTML = '<p style="color: orange;">⚠️ ' + errorMsg + '</p>' +
                                '<button class="btn" onclick="checkCommitStatus(' + "'" + jobId + "'" + ')">Try Again</button>';
        }
    });
}

/**
 * Activate specific step
 */
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

/**
 * Start over - reload page
 */
function startOver() {
    window.location.reload();
}

/**
 * Debug logs functionality
 */
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
            
            // Enhanced features info
            if (data.enhanced_features) {
                html += '<h4>Enhanced Features:</h4>';
                html += '<ul>';
                if (data.enhanced_features.multi_term_search) {
                    html += '<li>✅ Multi-term OR logic search</li>';
                }
                if (data.enhanced_features.manual_url_input) {
                    html += '<li>✅ Manual URL input</li>';
                }
                if (data.enhanced_features.automatic_ticket_generation) {
                    html += '<li>✅ Automatic ticket ID generation</li>';
                }
                if (data.enhanced_features.ticket_download) {
                    html += '<li>✅ Ticket log download</li>';
                }
                if (data.enhanced_features.live_commit_status_updates) {
                    html += '<li>✅ Live commit status updates in ticket logs</li>';
                }
                html += '</ul>';
            }
            
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

// Live polling functionality
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
        
        // Update ticket log with final status
        updateTicketLogStatus('FIN', progress);
    } else if (status === 'FAIL' || status === 'ERROR') {
        statusColor = 'red';
        statusIcon = '❌';
        statusText = 'FAILED';
        if (!message) message = '⚠️ Commit failed. Please check firewall logs.';
        
        // Update ticket log with final status
        updateTicketLogStatus(status, progress);
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

console.log('[DEBUG] Dashboard script loaded successfully - Enhanced with live ticket log updates');