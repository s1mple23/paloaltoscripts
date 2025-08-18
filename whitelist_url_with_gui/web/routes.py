"""
Enhanced Flask routes for the web interface
Updated to support automatic dual-action search and conditional download
"""
from flask import Flask, render_template_string, request, session, redirect, url_for, flash, jsonify, send_file
from datetime import datetime
import traceback
import json
import os
import tempfile

from config import config
from api.palo_alto_client import PaloAltoAPI, PaloAltoAPIError
from services.search_service import SearchService
from services.whitelist_service import WhitelistService
from services.logging_service import LoggingService
from models.ticket import TicketData, WhitelistRequest
from utils.validators import validate_credentials, validate_hostname, validate_ticket_id
from web.templates import get_login_template, get_dashboard_template

# Initialize services
logging_service = LoggingService()

def generate_automatic_ticket_id():
    """
    Generate automatic ticket ID with current date and time
    Format: Ticket-27JUL2025-01-06-10 (DD MMM YYYY - HH-MM-SS)
    """
    now = datetime.now()
    date_part = now.strftime("%d%b%Y").upper()
    time_part = now.strftime("%H-%M-%S")
    return f"Ticket-{date_part}-{time_part}"

def register_routes(app: Flask):
    """Register all Flask routes"""
    
    @app.route('/', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            hostname = request.form.get('hostname', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            # Validate inputs
            if not validate_hostname(hostname):
                return render_template_string(get_login_template(), 
                                            error='Invalid hostname or IP address', 
                                            config=config)
            
            is_valid, error_msg = validate_credentials(username, password)
            if not is_valid:
                return render_template_string(get_login_template(), 
                                            error=error_msg, 
                                            config=config)
            
            try:
                # Initialize API client and authenticate
                api_client = PaloAltoAPI(hostname, username, password)
                api_client.get_api_key()
                
                # Store only necessary data in session (no passwords)
                session['hostname'] = hostname
                session['username'] = username
                session['api_key'] = api_client.api_key
                session.permanent = True
                
                # Log successful login
                logging_service.log_login_attempt(username, hostname, True)
                
                return redirect(url_for('dashboard'))
                
            except PaloAltoAPIError as e:
                error_msg = "Authentication failed. Please check your credentials and firewall connectivity."
                logging_service.log_login_attempt(username, hostname, False, str(e))
                return render_template_string(get_login_template(), 
                                            error=error_msg, 
                                            config=config)
            except Exception as e:
                error_msg = "Connection error. Please check your firewall connectivity."
                logging_service.log_login_attempt(username, hostname, False, str(e))
                return render_template_string(get_login_template(), 
                                            error=error_msg, 
                                            config=config)
        
        return render_template_string(get_login_template(), config=config)

    @app.route('/dashboard')
    def dashboard():
        if 'api_key' not in session:
            return redirect(url_for('login'))
        
        return render_template_string(get_dashboard_template(), 
                                    config=config, 
                                    session=session)

    @app.route('/static/js/dashboard.js')
    def dashboard_js():
        """Serve dashboard JavaScript file"""
        from flask import Response
        try:
            with open('static/js/dashboard.js', 'r') as f:
                js_content = f.read()
            return Response(js_content, mimetype='application/javascript')
        except FileNotFoundError:
            js_content = """
            // Embedded dashboard JavaScript
            console.log('[DEBUG] Using embedded dashboard.js');
            """
            return Response(js_content, mimetype='application/javascript')

    @app.route('/search_urls', methods=['POST'])
    def search_urls():
        """Enhanced URL search with automatic dual-action search"""
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            # Validate request content type
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Invalid request format. Expected JSON.'})
            
            data = request.get_json()
            if data is None:
                return jsonify({'success': False, 'error': 'No JSON data received'})
                
            search_terms = data.get('search_term', '').strip()
            # Note: action_type is now ignored as we automatically search both
            
            print(f"[DEBUG] Automatic dual-action search request: terms='{search_terms}'")
            
            if not search_terms:
                return jsonify({'success': False, 'error': 'Search terms are required'})
            
            # Initialize services
            api_client = PaloAltoAPI(session['hostname'], session['username'], '')
            api_client.api_key = session['api_key']
            search_service = SearchService(api_client)
            
            # Test connectivity first
            print("[DEBUG] Testing API connectivity...")
            connectivity = api_client.test_connectivity()
            if not connectivity['success']:
                return jsonify({
                    'success': False, 
                    'error': f"API connectivity failed: {connectivity.get('error', 'Unknown error')}"
                })
            
            print("[DEBUG] API connectivity OK, starting automatic dual-action search...")
            
            # Execute automatic dual-action search (searches both block-url and block-continue)
            search_result = search_service.search_blocked_urls(search_terms, 'both')
            
            # Parse terms for logging
            parsed_terms = [t.strip() for t in search_terms.split(',') if t.strip()]
            terms_count = len(parsed_terms)
            
            print(f"[DEBUG] Automatic dual search completed: success={search_result.success}, urls_found={len(search_result.urls)}")
            
            # Log search operation
            logging_service.log_search_operation(
                search_terms, 'both', session['username'], 
                session['hostname'], len(search_result.urls), 
                search_result.success, search_result.error
            )
            
            if search_result.success:
                # Enhanced debug info for dual search
                strategy_info = search_result.strategy_info
                debug_info = f"Automatic dual-action search on {session['hostname']}: {terms_count} terms, " \
                           f"{strategy_info.get('search_strategy', 'unknown')} strategy, " \
                           f"found {len(search_result.urls)} matching domains"
                
                # Extract action-specific results if available
                action_results = strategy_info.get('action_results', {})
                block_url_count = len(action_results.get('block-url', {}).get('urls', []))
                block_continue_count = len(action_results.get('block-continue', {}).get('urls', []))
                
                response_data = {
                    'success': True,
                    'urls': search_result.urls,
                    'count': len(search_result.urls),
                    'search_term': search_result.search_term,
                    'action_type': 'both',
                    'strategy_info': strategy_info,
                    'debug_info': debug_info,
                    'message': f"Automatische Suche erfolgreich abgeschlossen. Gefunden: {len(search_result.urls)} URLs (block-url: {block_url_count}, block-continue: {block_continue_count})." if len(search_result.urls) > 0 else "Automatische Suche erfolgreich abgeschlossen. Keine blockierten URLs gefunden, die Ihren Kriterien entsprechen."
                }
                
                print(f"[DEBUG] Returning success response with {len(search_result.urls)} URLs")
                return jsonify(response_data)
            else:
                # Provide helpful error messages
                error_msg = search_result.error if search_result.error else "Search encountered technical issues"
                
                if error_msg and "timed out" in error_msg.lower():
                    error_msg = "Suche Timeout. Die Firewall verarbeitet möglicherweise viele Log-Einträge. Bitte versuchen Sie es mit spezifischeren Suchbegriffen."
                elif error_msg and "connection" in error_msg.lower():
                    error_msg = "Konnte nicht zur Firewall verbinden. Bitte prüfen Sie Ihre Verbindung."
                elif error_msg and "authentication" in error_msg.lower():
                    error_msg = "Authentifizierung abgelaufen. Bitte melden Sie sich erneut an."
                
                print(f"[DEBUG] Returning error response: {error_msg}")
                return jsonify({'success': False, 'error': error_msg})
            
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON decode error: {e}")
            return jsonify({'success': False, 'error': 'Invalid JSON format in request'})
        except Exception as e:
            print(f"[DEBUG] Unexpected error in search_urls: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            logging_service.log_error(f"Automatic dual search failed for {session.get('username', 'unknown')}@{session.get('hostname', 'unknown')}", e)
            return jsonify({'success': False, 'error': f"Suche fehlgeschlagen: {str(e)}"})

    @app.route('/validate_manual_urls', methods=['POST'])
    def validate_manual_urls():
        """Validate manually entered URLs"""
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Invalid request format. Expected JSON.'})
                
            data = request.get_json()
            if data is None:
                return jsonify({'success': False, 'error': 'No JSON data received'})
                
            manual_urls = data.get('manual_urls', '').strip()
            
            if not manual_urls:
                return jsonify({
                    'success': True,
                    'valid_urls': [],
                    'invalid_urls': []
                })
            
            # Initialize services
            api_client = PaloAltoAPI(session['hostname'], session['username'], '')
            api_client.api_key = session['api_key']
            search_service = SearchService(api_client)
            
            # Validate URLs
            valid_urls, invalid_urls = search_service.validate_manual_urls(manual_urls)
            
            # Log validation attempt
            logging_service.log_info(
                f"Manual URL validation by {session['username']}@{session['hostname']}: "
                f"{len(valid_urls)} valid, {len(invalid_urls)} invalid",
                {
                    'valid_count': len(valid_urls),
                    'invalid_count': len(invalid_urls),
                    'valid_urls': valid_urls,
                    'invalid_urls': invalid_urls
                }
            )
            
            return jsonify({
                'success': True,
                'valid_urls': valid_urls,
                'invalid_urls': invalid_urls,
                'total_input': len(valid_urls) + len(invalid_urls)
            })
            
        except Exception as e:
            print(f"[DEBUG] Manual URL validation error: {e}")
            logging_service.log_error("Manual URL validation failed", e)
            return jsonify({'success': False, 'error': f"Validierung fehlgeschlagen: {str(e)}"})

    @app.route('/get_categories')
    def get_categories():
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            # Initialize services
            api_client = PaloAltoAPI(session['hostname'], session['username'], '')
            api_client.api_key = session['api_key']
            whitelist_service = WhitelistService(api_client)
            
            categories = whitelist_service.get_categories()
            
            return jsonify({
                'success': True,
                'categories': categories
            })
            
        except Exception as e:
            print(f"[DEBUG] Category retrieval error: {e}")
            logging_service.log_error("Category retrieval failed", e)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/submit_whitelist', methods=['POST'])
    def submit_whitelist():
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Invalid request format. Expected JSON.'})
                
            data = request.get_json()
            if data is None:
                return jsonify({'success': False, 'error': 'No JSON data received'})
            
            # Extract and validate data
            ticket_id = data.get('ticket_id', '').strip()
            category = data.get('category', '').strip()
            urls = data.get('urls', [])
            action_type = data.get('action_type', 'both')  # Now supports 'both'
            
            # Generate automatic ticket ID if none provided
            if not ticket_id:
                ticket_id = generate_automatic_ticket_id()
                print(f"[DEBUG] Generated automatic ticket ID: {ticket_id}")
            
            print(f"[DEBUG] Whitelist submission data: ticket_id='{ticket_id}', category='{category}', urls_count={len(urls)}, action_type='{action_type}'")
            
            # Validate ticket ID
            if not validate_ticket_id(ticket_id):
                return jsonify({'success': False, 'error': 'Invalid ticket ID format. Please use alphanumeric characters, hyphens, underscores, and dots only.'})
            
            # Validate category
            if not category:
                return jsonify({'success': False, 'error': 'Category is required'})
            
            # Validate URLs
            if not urls or len(urls) == 0:
                return jsonify({'success': False, 'error': 'At least one URL is required'})
            
            # Validate each URL
            from utils.validators import validate_single_url
            invalid_urls = []
            for url in urls:
                if not validate_single_url(str(url)):
                    invalid_urls.append(str(url))
            
            if invalid_urls:
                return jsonify({'success': False, 'error': f'Invalid URLs found: {", ".join(invalid_urls[:3])}{"..." if len(invalid_urls) > 3 else ""}'})
            
            # Create whitelist request
            try:
                whitelist_request = WhitelistRequest(
                    category=category,
                    urls=urls,
                    ticket_id=ticket_id,
                    action_type=action_type
                )
            except Exception as e:
                print(f"[DEBUG] Error creating whitelist request: {e}")
                return jsonify({'success': False, 'error': f'Invalid request data: {str(e)}'})
            
            # Initialize services
            api_client = PaloAltoAPI(session['hostname'], session['username'], '')
            api_client.api_key = session['api_key']
            whitelist_service = WhitelistService(api_client)
            
            # Submit whitelist request
            success, message, commit_data = whitelist_service.submit_whitelist_request(whitelist_request)
            
            if success:
                # Create ticket data for logging - with INITIAL status
                ticket_data = TicketData(
                    ticket_id=whitelist_request.ticket_id,
                    username=session['username'],
                    hostname=session['hostname'],
                    category=whitelist_request.category,
                    context='unknown',  # Will be set by whitelist service
                    urls_added=whitelist_request.urls,
                    success=True,
                    commit_job_id=commit_data.get('commit_job_id'),
                    commit_status='SUBMITTED',  # Initial status
                    commit_progress='0',         # Initial progress
                    action_type=whitelist_request.action_type
                )
                
                # Create ticket log with initial status
                ticket_log_file = logging_service.create_ticket_log(ticket_data)
                
                # Store ticket log file path in session for later updates
                if ticket_log_file:
                    session['last_ticket_log'] = ticket_log_file
                    session['last_ticket_id'] = ticket_id
                
                # Log operation
                logging_service.log_whitelist_operation(ticket_data)
                
                # Enhanced logging for automatic dual-action submissions
                url_count = len(whitelist_request.urls)
                logging_service.log_info(
                    f"Automatic dual-action whitelist submission completed: {url_count} URLs added to {whitelist_request.category}",
                    {
                        'ticket_id': ticket_id,
                        'url_count': url_count,
                        'category': whitelist_request.category,
                        'action_type': whitelist_request.action_type,
                        'commit_job_id': commit_data.get('commit_job_id'),
                        'ticket_log_file': ticket_log_file
                    }
                )
                
                # Prepare response
                response_data = {
                    'success': True,
                    'message': message,
                    'commit_job_id': commit_data.get('commit_job_id'),
                    'log_entry': str(ticket_data.to_dict()),
                    'auto_commit_status': commit_data.get('auto_commit_status', {}),
                    'url_count': url_count,
                    'ticket_id': ticket_id,  # Include ticket ID in response
                    'immediate_response': commit_data.get('immediate_response', False)
                }
                
                if ticket_log_file:
                    response_data['ticket_log_file'] = ticket_log_file
                
                return jsonify(response_data)
            else:
                return jsonify({'success': False, 'error': message})
                
        except Exception as e:
            print(f"[DEBUG] Whitelist submission error: {e}")
            print(f"[DEBUG] Error type: {type(e).__name__}")
            print(f"[DEBUG] Error details: {str(e)}")
            
            # Check for specific error types
            error_message = str(e)
            if "string did not match the expected pattern" in error_message.lower():
                error_message = "Validierungsfehler: Ein Eingabewert enthält ungültige Zeichen. Bitte prüfen Sie Ticket-ID, URLs und Kategoriename."
            elif "invalid" in error_message.lower() and "pattern" in error_message.lower():
                error_message = "Eingabe-Validierung fehlgeschlagen. Bitte prüfen Sie, dass Ihre Ticket-ID nur Buchstaben, Zahlen, Bindestriche und Unterstriche verwendet."
            
            logging_service.log_error("Automatic dual-action whitelist submission failed", e)
            return jsonify({'success': False, 'error': error_message})

    @app.route('/download_ticket/<ticket_id>')
    def download_ticket(ticket_id):
        """Download ticket log file"""
        if 'api_key' not in session:
            return redirect(url_for('login'))
        
        try:
            # Find the most recent ticket log file for this ticket ID
            log_files = []
            
            # Check if we have the file path in session
            if 'last_ticket_log' in session:
                ticket_file = session['last_ticket_log']
                if os.path.exists(ticket_file) and ticket_id in ticket_file:
                    return send_file(
                        ticket_file,
                        as_attachment=True,
                        download_name=f"ticket_{ticket_id}.log",
                        mimetype='text/plain'
                    )
            
            # Search for ticket log files in log directory
            import glob
            pattern = os.path.join(config.LOG_DIR, f"ticket_{ticket_id}_*.log")
            log_files = glob.glob(pattern)
            
            if log_files:
                # Get the most recent file
                latest_file = max(log_files, key=os.path.getctime)
                
                return send_file(
                    latest_file,
                    as_attachment=True,
                    download_name=f"ticket_{ticket_id}.log",
                    mimetype='text/plain'
                )
            else:
                # Create a temporary file with basic info if log not found
                temp_content = f"""
================================================================================
                    PALO ALTO URL WHITELISTING - TICKET LOG
================================================================================

TICKET INFORMATION:
-------------------
Ticket ID:      {ticket_id}
Date & Time:    {datetime.now().strftime('%Y-%m-%d - %H:%M:%S')}
Processed by:   {session.get('username', 'Unknown')}
Firewall:       {session.get('hostname', 'Unknown')}

STATUS:
-------
Note: Original ticket log file not found.
This is a basic ticket information file.

================================================================================
                              END OF LOG
================================================================================
"""
                
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
                temp_file.write(temp_content)
                temp_file.close()
                
                return send_file(
                    temp_file.name,
                    as_attachment=True,
                    download_name=f"ticket_{ticket_id}_basic.log",
                    mimetype='text/plain'
                )
                
        except Exception as e:
            print(f"[DEBUG] Download ticket error: {e}")
            return jsonify({'success': False, 'error': f'Download fehlgeschlagen: {str(e)}'})

    @app.route('/commit_status', methods=['POST'])
    def commit_status():
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Invalid request format. Expected JSON.'})
                
            data = request.get_json()
            if data is None:
                return jsonify({'success': False, 'error': 'No JSON data received'})
                
            job_id = data.get('job_id')
            
            if not job_id:
                return jsonify({'success': False, 'error': 'Job ID required'})
            
            # Initialize services
            api_client = PaloAltoAPI(session['hostname'], session['username'], '')
            api_client.api_key = session['api_key']
            whitelist_service = WhitelistService(api_client)
            
            status = whitelist_service.get_commit_status(job_id)
            
            # Update ticket log if we have one in session and status is final
            if status.status in ['FIN', 'FAIL'] and 'last_ticket_log' in session:
                ticket_log_file = session['last_ticket_log']
                progress = status.progress if status.progress.endswith('%') else f"{status.progress}%"
                
                print(f"[DEBUG] Updating ticket log with final status: {status.status}, progress: {progress}")
                logging_service.update_ticket_log_commit_status(
                    ticket_log_file, 
                    status.status, 
                    progress
                )
            
            return jsonify({
                'success': True,
                'status': status.to_dict()
            })
            
        except Exception as e:
            print(f"[DEBUG] Commit status check error: {e}")
            logging_service.log_error("Commit status check failed", e)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/update_ticket_commit_status', methods=['POST'])
    def update_ticket_commit_status():
        """Update ticket log with final commit status - called from frontend"""
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Invalid request format. Expected JSON.'})
                
            data = request.get_json()
            if data is None:
                return jsonify({'success': False, 'error': 'No JSON data received'})
                
            commit_status = data.get('commit_status')
            commit_progress = data.get('commit_progress', '0')
            
            if not commit_status:
                return jsonify({'success': False, 'error': 'Commit status required'})
            
            # Get ticket log file from session
            if 'last_ticket_log' not in session:
                return jsonify({'success': False, 'error': 'No ticket log file found in session'})
            
            ticket_log_file = session['last_ticket_log']
            
            # Ensure progress has % symbol
            if not commit_progress.endswith('%'):
                commit_progress = f"{commit_progress}%"
            
            print(f"[DEBUG] Manual update of ticket log: status={commit_status}, progress={commit_progress}")
            
            # Update the ticket log
            logging_service.update_ticket_log_commit_status(
                ticket_log_file, 
                commit_status, 
                commit_progress
            )
            
            return jsonify({
                'success': True,
                'message': f'Ticket log updated with status: {commit_status}'
            })
            
        except Exception as e:
            print(f"[DEBUG] Update ticket commit status error: {e}")
            logging_service.log_error("Update ticket commit status failed", e)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/debug_logs')
    def debug_logs():
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            # Initialize API client
            api_client = PaloAltoAPI(session['hostname'], session['username'], '')
            api_client.api_key = session['api_key']
            
            # Test API connectivity
            connectivity = api_client.test_connectivity()
            
            # Check available log types
            log_types = api_client.get_log_types_available()
            
            return jsonify({
                'success': True,
                'connectivity': connectivity,
                'log_types': log_types,
                'hostname': session['hostname'],
                'username': session['username'],
                'enhanced_features': {
                    'automatic_dual_search': True,
                    'multi_term_search': True,
                    'manual_url_input': True,
                    'or_logic_support': True,
                    'automatic_ticket_generation': True,
                    'ticket_download': True,
                    'conditional_download': True,
                    'live_commit_status_updates': True
                }
            })
            
        except Exception as e:
            print(f"[DEBUG] Debug logs error: {e}")
            logging_service.log_error("Debug logs failed", e)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/favicon.ico')
    def favicon():
        from flask import Response
        return Response(status=204)  # No content

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))