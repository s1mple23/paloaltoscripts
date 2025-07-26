/**
 * Enhanced Dashboard JavaScript for Palo Alto Whitelist Tool
 * Supports multiple search terms and manual URL addition
 */

// Global variables
var selectedUrls = [];
var searchResults = [];
var manualUrls = [];
var categories = {};
var selectedActionType = 'block-url';

/**
 * Initialize the dashboard when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] Enhanced Dashboard initialized');
    
    // Attach event listeners
    document.getElementById('searchForm').addEventListener('submit', handleSearchSubmit);
    
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
 * Handle search form submission with multiple terms support
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
    var terms = searchTerms.split(',').map(t => t.trim()).filter(t => t.length > 0);
    if (terms.length === 0) {
        alert('Please enter valid search terms');
        return;
    }
    
    var resultsDiv = document.getElementById('urlSelection');
    var searchBtn = e.target.querySelector('button[type="submit"]');
    
    console.log('[DEBUG] Starting enhanced multi-term search request...');
    
    searchBtn.disabled = true;
    searchBtn.textContent = 'Searching... (~2 min)';
    
    activateStep(2);
    
    // Show different message based on number of terms
    var searchMessage = terms.length === 1 
        ? `🎯 Targeted search for "${terms[0]}" with action "${selectedActionType}"`
        : `🎯 Multi-term search for ${terms.length} terms (${terms.join(', ')}) with OR logic and action "${selectedActionType}"`;
    
    resultsDiv.innerHTML = '<div class="loading">' + searchMessage + '...<br>' +
                          '<small>⏱️ Running 4 attempts with timeouts: 10s, 15s, 25s, 35s<br>' +
                          'Searching last 3 months, up to 3,000 entries<br>' +
                          '<strong>Estimated time: ~2 minutes - Please wait...</strong></small></div>';
    
    console.log('[DEBUG] Making fetch request to /search_urls');
    
    fetch('/search_urls', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            search_term: searchTerms,
            action_type: selectedActionType
        })
    })
    .then(function(response) {
        console.log('[DEBUG] Got response:', response.status, response.statusText);
        return response.json();
    })
    .then(function(data) {
        console.log('[DEBUG] Response data:', data);
        
        if (data.success) {
            console.log('[DEBUG] Search successful, found URLs:', data.urls);
            searchResults = data.urls;
            displaySearchResults(data.urls, searchTerms, selectedActionType, data.debug_info);
            showManualUrlInput(); // Show manual URL input after search
        } else {
            console.log('[DEBUG] Search failed:', data.error);
            resultsDiv.innerHTML = '<div class="error">Error: ' + data.error + '</div>';
            showManualUrlInput(); // Show manual URL input even on search failure
        }
    })
    .catch(function(error) {
        console.error('[DEBUG] Fetch error:', error);
        resultsDiv.innerHTML = '<div class="error">Network error: ' + error.message + '</div>';
        showManualUrlInput(); // Show manual URL input on network error
    })
    .finally(function() {
        console.log('[DEBUG] Search request completed');
        searchBtn.disabled = false;
        searchBtn.textContent = 'Start Enhanced Search (~2 minutes)';
    });
}

/**
 * Display search results with enhanced information
 */
function displaySearchResults(urls, searchTerms, actionType, debugInfo) {
    var resultsDiv = document.getElementById('urlSelection');
    var terms = searchTerms.split(',').map(t => t.trim()).filter(t => t.length > 0);
    
    var html = '';
    
    if (urls.length === 0) {
        html = '<div style="text-align: center; padding: 20px; color: #666;">' +
            '<h4>No blocked URLs found</h4>';
        
        if (terms.length === 1) {
            html += '<p>No URLs containing "' + terms[0] + '" found with action: <strong>' + actionType + '</strong></p>';
        } else {
            html += '<p>No URLs containing any of the terms (' + terms.join(', ') + ') found with action: <strong>' + actionType + '</strong></p>';
        }
        
        html += '<p><small>Searched last 3 months with 4 timeout attempts and OR logic for multiple terms</small></p>' +
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
            html += '<input type="checkbox" id="url_' + i + '" value="' + url + '" style="margin-right: 10px; transform: scale(1.2);" onclick="updateSelectedUrls()">';
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
    var manualSection = document.getElementById('manualUrlSection');
    if (manualSection) {
        manualSection.style.display = 'block';
    } else {
        // Create manual URL input section if it doesn't exist
        var urlSelection = document.getElementById('urlSelection');
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
            if (data.valid_urls.length > 0) {
                html += '<div style="color: green;">✅ Valid URLs (' + data.valid_urls.length + '): ' + data.valid_urls.join(', ') + '</div>';
            }
            if (data.invalid_urls.length > 0) {
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
        if (data.success && data.valid_urls.length > 0) {
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
            
            if (data.invalid_urls.length > 0) {
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
                   '<input type="checkbox" id="manual_' + i + '" checked style="margin-right: 10px;" onclick="updateSelectedUrls()">' +
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
 * Submit whitelist request
 */
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
    
    var submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Submitting...';
    
    var payload = {
        category: categorySelect.value,
        urls: urlsToAdd,
        ticket_id: ticketId,
        action_type: selectedActionType
    };
    
    // Set timeout for submission
    var submissionTimeout = setTimeout(function() {
        console.log('[DEBUG] Submission taking longer than expected');
        activateStep(5);
        displayResults({
            success: true,
            message: 'Whitelist submission in progress...',
            timeout_occurred: true,
            commit_job_id: 'pending',
            auto_commit_status: {
                status: 'PROCESSING',
                progress: 'unknown',
                auto_polled: false
            }
        });
    }, 30000);
    
    fetch('/submit_whitelist', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(function(response) {
        clearTimeout(submissionTimeout);
        return response.json();
    })
    .then(function(data) {
        clearTimeout(submissionTimeout);
        activateStep(5);
        displayResults(data);
    })
    .catch(function(error) {
        clearTimeout(submissionTimeout);
        var resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<div class="error">Network error: ' + error.message + '</div>';
        activateStep(5);
    })
    .finally(function() {
        clearTimeout(submissionTimeout);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Whitelist Request';
    });
}

/**
 * Display submission results
 */
function displayResults(data) {
    var resultsDiv = document.getElementById('results');
    
    if (data.success) {
        var html = '<div class="success">' + data.message + '</div>';
        
        // Handle timeout case
        if (data.timeout_occurred) {
            html += '<div style="background: #fff3cd; padding: 15px; border-radius: 4px; margin-top: 15px;">';
            html += '<h3>⏳ Submission In Progress</h3>';
            html += '<p>Your whitelist request is being processed. This may take a few minutes.</p>';
            html += '<p><strong>What happens next:</strong></p>';
            html += '<ul>';
            html += '<li>URLs are being added to the category</li>';
            html += '<li>Configuration is being committed to the firewall</li>';
            html += '<li>Changes will be active once commit completes</li>';
            html += '</ul>';
            html += '</div>';
            
            if (data.ticket_log_file) {
                html += '<div style="background: #e8f5e8; padding: 15px; border-radius: 4px; margin-top: 15px;">';
                html += '<h3>📋 Ticket Log Created:</h3>';
                html += '<p><strong>Log File:</strong> ' + data.ticket_log_file + '</p>';
                html += '<p>✅ Individual ticket log created for audit trail</p>';
                html += '</div>';
            }
            
            resultsDiv.innerHTML = html;
            return;
        }
        
        // Show commit status if available
        if (data.auto_commit_status && data.auto_commit_status.auto_polled) {
            var autoStatus = data.auto_commit_status;
            html += '<div class="commit-status">';
            html += '<h3>🔄 Commit Status (Auto-Polled):</h3>';
            html += '<p><strong>Job ID:</strong> ' + data.commit_job_id + '</p>';
            
            if (autoStatus.status === 'FIN') {
                html += '<p><strong>Status:</strong> <span style="color: green;">✅ COMPLETED</span></p>';
                html += '<p><strong>Progress:</strong> 100%</p>';
                html += '<p style="color: green;">🎉 Configuration has been successfully committed to the firewall!</p>';
            } else if (autoStatus.status === 'FAIL') {
                html += '<p><strong>Status:</strong> <span style="color: red;">❌ FAILED</span></p>';
                html += '<p><strong>Progress:</strong> ' + (autoStatus.progress || '0') + '%</p>';
                html += '<p style="color: red;">⚠️ Commit failed. Please check firewall logs.</p>';
            } else {
                html += '<p><strong>Status:</strong> <span style="color: orange;">⏳ ' + autoStatus.status + '</span></p>';
                html += '<p><strong>Progress:</strong> ' + (autoStatus.progress || '0') + '%</p>';
                if (data.commit_job_id) {
                    html += '<button class="btn" onclick="checkCommitStatus(' + "'" + data.commit_job_id + "'" + ')">Check Current Status</button>';
                }
            }
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
        resultsDiv.innerHTML = '<div class="error">Error: ' + data.error + '</div>';
    }
}

/**
 * Check commit status
 */
function checkCommitStatus(jobId) {
    fetch('/commit_status', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({job_id: jobId})
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        var statusDiv = document.querySelector('.commit-status');
        if (data.success && statusDiv) {
            var status = data.status;
            var statusHTML = '<h3>Commit Status:</h3>';
            statusHTML += '<p><strong>Job ID:</strong> ' + jobId + '</p>';
            statusHTML += '<p><strong>Status:</strong> ' + status.status + '</p>';
            statusHTML += '<p><strong>Progress:</strong> ' + status.progress + '%</p>';
            
            if (status.status !== 'FIN') {
                statusHTML += '<button class="btn" onclick="checkCommitStatus(' + "'" + jobId + "'" + ')">Refresh Status</button>';
            }
            
            statusDiv.innerHTML = statusHTML;
        }
    })
    .catch(function(error) {
        console.error('Commit status check failed:', error);
    });
}

/**
 * Activate specific step
 */
function activateStep(stepNumber) {
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