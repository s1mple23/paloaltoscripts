"""
Enhanced Flask routes for the web interface
Fixed JSON response issues and improved error handling
"""
from flask import Flask, render_template_string, request, session, redirect, url_for, flash, jsonify
from datetime import datetime
import traceback
import json

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
            # Return the embedded JS content if file doesn't exist
            js_content = """
            // Embedded dashboard JavaScript
            console.log('[DEBUG] Using embedded dashboard.js');
            // Add your dashboard.js content here if static file is missing
            """
            return Response(js_content, mimetype='application/javascript')

    @app.route('/search_urls', methods=['POST'])
    def search_urls():
        """Enhanced URL search with better error handling"""
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
            action_type = data.get('action_type', 'block-url')
            
            print(f"[DEBUG] Search request: terms='{search_terms}', action='{action_type}'")
            
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
            
            print("[DEBUG] API connectivity OK, starting search...")
            
            # Execute enhanced search with multiple terms support
            search_result = search_service.search_blocked_urls(search_terms, action_type)
            
            # Parse terms for logging
            parsed_terms = [t.strip() for t in search_terms.split(',') if t.strip()]
            terms_count = len(parsed_terms)
            
            print(f"[DEBUG] Search completed: success={search_result.success}, urls_found={len(search_result.urls)}")
            
            # Log search operation
            logging_service.log_search_operation(
                search_terms, action_type, session['username'], 
                session['hostname'], len(search_result.urls), 
                search_result.success, search_result.error
            )
            
            if search_result.success:
                # Enhanced debug info
                strategy_info = search_result.strategy_info
                debug_info = f"Multi-term search on {session['hostname']}: {terms_count} terms, " \
                           f"{strategy_info.get('search_strategy', 'unknown')} strategy, " \
                           f"found {len(search_result.urls)} matching domains"
                
                response_data = {
                    'success': True,
                    'urls': search_result.urls,
                    'count': len(search_result.urls),
                    'search_term': search_result.search_term,
                    'action_type': search_result.action_type,
                    'strategy_info': strategy_info,
                    'debug_info': debug_info
                }
                
                print(f"[DEBUG] Returning success response with {len(search_result.urls)} URLs")
                return jsonify(response_data)
            else:
                # Provide helpful error messages
                error_msg = search_result.error if search_result.error else "Search completed but encountered issues"
                
                # More specific error handling
                if error_msg and "timeout" in error_msg.lower():
                    error_msg = "Search timed out. The firewall may be processing a large number of logs. Please try again with more specific search terms."
                elif error_msg and "connection" in error_msg.lower():
                    error_msg = "Could not connect to the firewall. Please check your connection and try again."
                elif error_msg and "unauthorized" in error_msg.lower() or (error_msg and "authentication" in error_msg.lower()):
                    error_msg = "Authentication expired. Please log in again."
                elif error_msg and "no valid search terms" in error_msg.lower():
                    error_msg = "Please provide valid search terms. Use comma-separated values for multiple terms."
                elif not error_msg or error_msg == "Unknown search error":
                    error_msg = "Search completed successfully but no URLs were found matching your criteria."
                
                print(f"[DEBUG] Returning error response: {error_msg}")
                return jsonify({'success': False, 'error': error_msg})
            
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON decode error: {e}")
            return jsonify({'success': False, 'error': 'Invalid JSON format in request'})
        except Exception as e:
            print(f"[DEBUG] Unexpected error in search_urls: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            logging_service.log_error(f"Enhanced search URLs failed for {session.get('username', 'unknown')}@{session.get('hostname', 'unknown')}", e)
            return jsonify({'success': False, 'error': f"Search failed: {str(e)}"})

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
            return jsonify({'success': False, 'error': f"Validation failed: {str(e)}"})

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
            
            # Validate ticket ID
            ticket_id = data.get('ticket_id', '').strip()
            if not validate_ticket_id(ticket_id):
                return jsonify({'success': False, 'error': 'Invalid ticket ID format'})
            
            # Create whitelist request
            whitelist_request = WhitelistRequest(
                category=data.get('category'),
                urls=data.get('urls', []),
                ticket_id=ticket_id,
                action_type=data.get('action_type', 'block-url')
            )
            
            # Initialize services
            api_client = PaloAltoAPI(session['hostname'], session['username'], '')
            api_client.api_key = session['api_key']
            whitelist_service = WhitelistService(api_client)
            
            # Submit whitelist request
            success, message, commit_data = whitelist_service.submit_whitelist_request(whitelist_request)
            
            if success:
                # Create ticket data for logging
                ticket_data = TicketData(
                    ticket_id=whitelist_request.ticket_id,
                    username=session['username'],
                    hostname=session['hostname'],
                    category=whitelist_request.category,
                    context='unknown',  # Will be set by whitelist service
                    urls_added=whitelist_request.urls,
                    success=True,
                    commit_job_id=commit_data.get('commit_job_id'),
                    commit_status=commit_data.get('commit_status'),
                    commit_progress=commit_data.get('commit_progress'),
                    action_type=whitelist_request.action_type
                )
                
                # Create ticket log
                ticket_log_file = logging_service.create_ticket_log(ticket_data)
                
                # Log operation
                logging_service.log_whitelist_operation(ticket_data)
                
                # Enhanced logging for multi-URL submissions
                url_count = len(whitelist_request.urls)
                logging_service.log_info(
                    f"Enhanced whitelist submission completed: {url_count} URLs added to {whitelist_request.category}",
                    {
                        'ticket_id': ticket_id,
                        'url_count': url_count,
                        'category': whitelist_request.category,
                        'action_type': whitelist_request.action_type,
                        'commit_job_id': commit_data.get('commit_job_id')
                    }
                )
                
                # Prepare response
                response_data = {
                    'success': True,
                    'message': message,
                    'commit_job_id': commit_data.get('commit_job_id'),
                    'log_entry': str(ticket_data.to_dict()),
                    'auto_commit_status': commit_data.get('auto_commit_status', {}),
                    'url_count': url_count
                }
                
                if ticket_log_file:
                    response_data['ticket_log_file'] = ticket_log_file
                
                return jsonify(response_data)
            else:
                return jsonify({'success': False, 'error': message})
                
        except Exception as e:
            print(f"[DEBUG] Whitelist submission error: {e}")
            logging_service.log_error("Enhanced whitelist submission failed", e)
            return jsonify({'success': False, 'error': str(e)})

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
            
            return jsonify({
                'success': True,
                'status': status.to_dict()
            })
            
        except Exception as e:
            print(f"[DEBUG] Commit status check error: {e}")
            logging_service.log_error("Commit status check failed", e)
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
                    'multi_term_search': True,
                    'manual_url_input': True,
                    'or_logic_support': True
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