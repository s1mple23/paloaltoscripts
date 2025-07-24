/**
 * Dashboard JavaScript for Palo Alto Whitelist Tool
 */

// Global variables
var selectedUrls = [];
var searchResults = [];
var categories = {};
var selectedActionType = 'block-url';

/**
 * Initialize the dashboard when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] Dashboard initialized');
    
    // Attach event listeners
    document.getElementById('searchForm').addEventListener('submit', handleSearchSubmit);
    
    var exactMatch = document.getElementById('exactMatch');
    var wildcardMatch = document.getElementById('wildcardMatch');
    if (exactMatch) exactMatch.addEventListener('change', updateUrlPreview);
    if (wildcardMatch) wildcardMatch.addEventListener('change', updateUrlPreview);
});

/**
 * Handle search form submission
 */
function handleSearchSubmit(e) {
    e.preventDefault();
    console.log('[DEBUG] Search form submitted with targeted strategy');
    
    var searchTerm = document.getElementById('search_term').value.trim();
    selectedActionType = document.querySelector('input[name="action_type"]:checked').value;
    
    console.log('[DEBUG] Search term:', searchTerm);
    console.log('[DEBUG] Action type:', selectedActionType);
    
    if (!searchTerm) {
        alert('Please enter a search term');
        return;
    }
    
    var resultsDiv = document.getElementById('urlSelection');
    var searchBtn = e.target.querySelector('button[type="submit"]');
    
    console.log('[DEBUG] Starting targeted search request...');
    
    searchBtn.disabled = true;
    searchBtn.textContent = 'Searching... (~2 min)';
    
    activateStep(2);
    
    resultsDiv.innerHTML = '<div class="loading">🎯 Targeted search for "' + searchTerm + '" with action "' + selectedActionType + '"...<br>' +
                          '<small>⏱️ Running 4 attempts with timeouts: 10s, 15s, 25s, 35s<br>' +
                          'Searching last 3 months, up to 3,000 entries<br>' +
                          '<strong>Estimated time: ~2 minutes - Please wait...</strong></small></div>';
    
    console.log('[DEBUG] Making fetch request to /search_urls');
    
    fetch('/search_urls', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            search_term: searchTerm,
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
            displaySearchResults(data.urls, searchTerm, selectedActionType);
        } else {
            console.log('[DEBUG] Search failed:', data.error);
            resultsDiv.innerHTML = '<div class="error">Error: ' + data.error + '</div>';
        }
    })
    .catch(function(error) {
        console.error('[DEBUG] Fetch error:', error);
        resultsDiv.innerHTML = '<div class="error">Network error: ' + error.message + '</div>';
    })
    .finally(function() {
        console.log('[DEBUG] Search request completed');
        searchBtn.disabled = false;
        searchBtn.textContent = 'Start Targeted Search (~2 minutes)';
    });
}

/**
 * Display search results
 */
function displaySearchResults(urls, searchTerm, actionType) {
    var resultsDiv = document.getElementById('urlSelection');
    
    if (urls.length === 0) {
        resultsDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">' +
            '<h4>No blocked URLs found</h4>' +
            '<p>No URLs containing "' + searchTerm + '" found with action: <strong>' + actionType + '</strong></p>' +
            '<p><small>Searched last 3 months with 4 timeout attempts (10s, 15s, 25s, 35s)</small></p>' +
            '</div>';
        return;
    }
    
    var html = '<h3>🎯 Found ' + urls.length + ' blocked URLs (targeted search - action: ' + actionType + '):</h3>';
    html += '<div style="margin: 10px 0; padding: 10px; background: #f0f8ff; border-radius: 4px;">' +
           '✅ <strong>Targeted Results:</strong> Searched specifically for action "' + actionType + '" with 4 timeout attempts for reliability.<br>' +
           '📅 <strong>Time Range:</strong> Last 3 months, up to 3,000 entries<br>' +
           'Click the checkboxes below to select URLs for whitelisting:</div>';
    
    for (var i = 0; i < urls.length; i++) {
        var url = urls[i];
        html += '<div class="url-item" style="margin: 8px 0; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background: white;">';
        html += '<input type="checkbox" id="url_' + i + '" value="' + url + '" style="margin-right: 10px; transform: scale(1.2);" onclick="updateSelectedUrls()">';
        html += '<label for="url_' + i + '" style="cursor: pointer; user-select: none;">' + url + '</label>';
        html += '</div>';
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
 * Update selected URLs
 */
function updateSelectedUrls() {
    selectedUrls = [];
    for (var i = 0; i < searchResults.length; i++) {
        var checkbox = document.getElementById('url_' + i);
        if (checkbox && checkbox.checked) {
            selectedUrls.push(searchResults[i]);
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
        var domain = url.endsWith('/') ? url : url + '/';
        if (exactMatch) {
            html += '<li>' + domain + '</li>';
        }
        if (wildcardMatch) {
            html += '<li>*.' + domain + '</li>';
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
        var domain = url.endsWith('/') ? url : url + '/';
        if (exactMatch) urlsToAdd.push(domain);
        if (wildcardMatch) urlsToAdd.push('*.' + domain);
    }
    
    var summaryDiv = document.getElementById('finalSummary');
    var urlsList = '';
    for (var i = 0; i < urlsToAdd.length; i++) {
        urlsList += '<li>' + urlsToAdd[i] + '</li>';
    }
    
    summaryDiv.innerHTML = '<div><h3>Summary:</h3>' +
                          '<p><strong>Search Action:</strong> ' + selectedActionType + '</p>' +
                          '<p><strong>Category:</strong> ' + categorySelect.value + '</p>' +
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
        var domain = url.endsWith('/') ? url : url + '/';
        if (exactMatch) urlsToAdd.push(domain);
        if (wildcardMatch) urlsToAdd.push('*.' + domain);
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