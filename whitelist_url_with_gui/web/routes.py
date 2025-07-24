"""
Flask routes for the web interface
"""
from flask import Flask, render_template_string, request, session, redirect, url_for, flash, jsonify
from datetime import datetime

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
        
        return render_template_string(get_dashboard_template(), config=config)

    @app.route('/search_urls', methods=['POST'])
    def search_urls():
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            data = request.get_json()
            search_term = data.get('search_term', '').strip()
            action_type = data.get('action_type', 'block-url')
            
            # Initialize services
            api_client = PaloAltoAPI(session['hostname'], session['username'], '')
            api_client.api_key = session['api_key']
            search_service = SearchService(api_client)
            
            # Test connectivity first
            connectivity = api_client.test_connectivity()
            if not connectivity['success']:
                return jsonify({
                    'success': False, 
                    'error': f"API connectivity failed: {connectivity['error']}"
                })
            
            # Execute search
            search_result = search_service.search_blocked_urls(search_term, action_type)
            
            # Log search operation
            logging_service.log_search_operation(
                search_term, action_type, session['username'], 
                session['hostname'], len(search_result.urls), 
                search_result.success, search_result.error
            )
            
            if search_result.success:
                return jsonify({
                    'success': True,
                    'urls': search_result.urls,
                    'count': len(search_result.urls),
                    'search_term': search_result.search_term,
                    'action_type': search_result.action_type,
                    'debug_info': f"Searched firewall {session['hostname']} with targeted strategy (action: {action_type}) and found {len(search_result.urls)} matching domains"
                })
            else:
                # Provide helpful error messages
                error_msg = search_result.error
                if "timeout" in error_msg.lower():
                    error_msg = "Search timed out. The firewall may be processing a large number of logs. Please try again with a more specific search term."
                elif "connection" in error_msg.lower():
                    error_msg = "Could not connect to the firewall. Please check your connection and try again."
                elif "unauthorized" in error_msg.lower() or "authentication" in error_msg.lower():
                    error_msg = "Authentication expired. Please log in again."
                
                return jsonify({'success': False, 'error': error_msg})
            
        except Exception as e:
            logging_service.log_error(f"Search URLs failed for {session.get('username', 'unknown')}@{session.get('hostname', 'unknown')}", e)
            return jsonify({'success': False, 'error': f"Search failed: {str(e)}"})

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
            logging_service.log_error("Category retrieval failed", e)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/submit_whitelist', methods=['POST'])
    def submit_whitelist():
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            data = request.get_json()
            
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
                
                # Prepare response
                response_data = {
                    'success': True,
                    'message': message,
                    'commit_job_id': commit_data.get('commit_job_id'),
                    'log_entry': str(ticket_data.to_dict()),
                    'auto_commit_status': commit_data.get('auto_commit_status', {})
                }
                
                if ticket_log_file:
                    response_data['ticket_log_file'] = ticket_log_file
                
                return jsonify(response_data)
            else:
                return jsonify({'success': False, 'error': message})
                
        except Exception as e:
            logging_service.log_error("Whitelist submission failed", e)
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/commit_status', methods=['POST'])
    def commit_status():
        if 'api_key' not in session:
            return jsonify({'success': False, 'error': 'Not authenticated'})
        
        try:
            data = request.get_json()
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
                'username': session['username']
            })
            
        except Exception as e:
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