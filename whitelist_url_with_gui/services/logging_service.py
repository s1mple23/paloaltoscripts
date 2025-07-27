"""
Logging Service
Handles ticket logging and audit trail creation
Enhanced to update ticket logs with final commit status
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional

from config import config
from models.ticket import TicketData

class LoggingService:
    """Service for handling application and ticket logging"""
    
    def __init__(self):
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup application logging"""
        # Create logs directory if it doesn't exist
        os.makedirs(config.LOG_DIR, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            filename=config.APP_LOG_FILE,
            level=getattr(logging, config.LOG_LEVEL),
            format=config.LOG_FORMAT,
            filemode='a'
        )
        
        self.logger = logging.getLogger(__name__)
    
    def log_info(self, message: str, extra_data: dict = None):
        """Log info message"""
        if extra_data:
            message = f"{message} | Data: {json.dumps(extra_data)}"
        self.logger.info(message)
    
    def log_error(self, message: str, error: Exception = None, extra_data: dict = None):
        """Log error message"""
        if error:
            message = f"{message} | Error: {str(error)}"
        if extra_data:
            message = f"{message} | Data: {json.dumps(extra_data)}"
        self.logger.error(message)
    
    def log_debug(self, message: str, extra_data: dict = None):
        """Log debug message"""
        if extra_data:
            message = f"{message} | Data: {json.dumps(extra_data)}"
        self.logger.debug(message)
    
    def create_ticket_log(self, ticket_data: TicketData) -> Optional[str]:
        """
        Create a human-readable individual ticket log file
        
        Args:
            ticket_data: TicketData object containing ticket information
            
        Returns:
            Filename of created log file or None if failed
        """
        try:
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_ticket_id = ticket_data.ticket_id.replace('/', '_').replace('\\', '_')
            
            # Create filename
            filename = os.path.join(config.LOG_DIR, f"ticket_{safe_ticket_id}_{timestamp}.log")
            
            # Create human-readable content
            log_content = self._generate_ticket_log_content(ticket_data)
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            print(f"[LOG] Human-readable ticket log created: {filename}")
            
            # Also log to application log
            self.log_info(f"Ticket log created: {filename}", ticket_data.to_dict())
            
            return filename
            
        except Exception as e:
            print(f"[ERROR] Failed to create individual ticket log: {e}")
            self.log_error("Failed to create ticket log", e, ticket_data.to_dict())
            return None
    
    def update_ticket_log_commit_status(self, ticket_log_file: str, commit_status: str, commit_progress: str):
        """
        Update existing ticket log file with final commit status
        
        Args:
            ticket_log_file: Path to the ticket log file
            commit_status: Final commit status (e.g., 'FIN', 'FAIL')
            commit_progress: Final commit progress (e.g., '100%')
        """
        try:
            if not ticket_log_file or not os.path.exists(ticket_log_file):
                print(f"[DEBUG] Ticket log file not found for update: {ticket_log_file}")
                return
            
            # Read current content
            with open(ticket_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find and update the commit status section
            lines = content.split('\n')
            updated_lines = []
            in_operation_status = False
            status_updated = False
            progress_updated = False
            
            for line in lines:
                if 'OPERATION STATUS:' in line:
                    in_operation_status = True
                    updated_lines.append(line)
                elif in_operation_status and 'Commit Status:' in line:
                    updated_lines.append(f"Commit Status:  {commit_status}")
                    status_updated = True
                elif in_operation_status and 'Commit Progress:' in line:
                    updated_lines.append(f"Commit Progress: {commit_progress}")
                    progress_updated = True
                elif in_operation_status and line.startswith('SEARCH DETAILS:'):
                    # End of operation status section
                    in_operation_status = False
                    updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Write updated content back to file
            updated_content = '\n'.join(updated_lines)
            with open(ticket_log_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"[LOG] Updated ticket log with final commit status: {commit_status}, progress: {commit_progress}")
            
            # Log the update
            self.log_info(f"Ticket log updated with commit status", {
                'file': ticket_log_file,
                'status': commit_status,
                'progress': commit_progress
            })
            
        except Exception as e:
            print(f"[ERROR] Failed to update ticket log commit status: {e}")
            self.log_error("Failed to update ticket log commit status", e)
    
    def _generate_ticket_log_content(self, ticket_data: TicketData) -> str:
        """Generate human-readable ticket log content"""
        
        # Parse timestamp for display
        try:
            parsed_time = datetime.fromisoformat(ticket_data.timestamp)
            formatted_time = parsed_time.strftime('%Y-%m-%d - %H:%M:%S')
        except (ValueError, TypeError):
            formatted_time = ticket_data.timestamp or "Unknown"
        
        # Determine initial commit status display
        commit_status_display = ticket_data.commit_status or 'SUBMITTED'
        commit_progress_display = ticket_data.commit_progress or '0%'
        
        # Add progress % if not already included
        if commit_progress_display and not commit_progress_display.endswith('%'):
            commit_progress_display += '%'
        
        log_content = f"""
================================================================================
                    PALO ALTO URL WHITELISTING - TICKET LOG
================================================================================

TICKET INFORMATION:
-------------------
Ticket ID:      {ticket_data.ticket_id}
Date & Time:    {formatted_time}
Processed by:   {ticket_data.username}
Firewall:       {ticket_data.hostname}

WHITELIST OPERATION:
-------------------
Category Name:  {ticket_data.category}
Category Type:  {ticket_data.context}
Number of URLs: {len(ticket_data.urls_added)}

URLs ADDED:
-----------"""
        
        # Add each URL on a separate line with numbering
        for i, url in enumerate(ticket_data.urls_added, 1):
            log_content += f"\n{i:2d}. {url}"
        
        log_content += f"""

OPERATION STATUS:
-----------------
Success:        {'✅ YES' if ticket_data.success else '❌ NO'}
Commit Job ID:  {ticket_data.commit_job_id or 'N/A'}
Commit Status:  {commit_status_display}
Commit Progress: {commit_progress_display}
"""
        
        log_content += f"""
SEARCH DETAILS:
---------------
Search Strategy: {ticket_data.search_strategy}
Action Type:     {ticket_data.action_type}
Lookback Period: {config.LOOKBACK_MONTHS} months
Max Entries:     {config.DEFAULT_MAX_RESULTS}

TECHNICAL DETAILS:
------------------
Log Version:    {config.VERSION}
Search Method:  Targeted with Multiple Timeouts
Log Format:     Human Readable Text
Created for:    Audit Trail & Compliance
Tool Version:   {config.APP_NAME} v{config.VERSION}
Log Updated:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

NOTES:
------
• This log file may be updated with final commit status once the firewall 
  configuration commit is completed.
• Initial status shows submission time. Final status shows completion.
• For audit purposes, keep this log file as proof of configuration changes.

================================================================================
                              END OF LOG
================================================================================
"""
        
        return log_content
    
    def log_search_operation(self, search_term: str, action_type: str, username: str, 
                           hostname: str, results_count: int, success: bool, error: str = None):
        """Log search operation"""
        operation_data = {
            'operation': 'search',
            'search_term': search_term,
            'action_type': action_type,
            'username': username,
            'hostname': hostname,
            'results_count': results_count,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if error:
            operation_data['error'] = error
            self.log_error(f"Search operation failed for '{search_term}' by {username}@{hostname}", 
                          extra_data=operation_data)
        else:
            self.log_info(f"Search operation completed for '{search_term}' by {username}@{hostname}: {results_count} results", 
                         extra_data=operation_data)
    
    def log_whitelist_operation(self, ticket_data: TicketData):
        """Log whitelist operation"""
        operation_data = {
            'operation': 'whitelist',
            **ticket_data.to_dict()
        }
        
        if ticket_data.success:
            self.log_info(f"Whitelist operation successful for ticket {ticket_data.ticket_id}", 
                         extra_data=operation_data)
        else:
            self.log_error(f"Whitelist operation failed for ticket {ticket_data.ticket_id}", 
                          extra_data=operation_data)
    
    def log_login_attempt(self, username: str, hostname: str, success: bool, error: str = None):
        """Log login attempt"""
        login_data = {
            'operation': 'login',
            'username': username,
            'hostname': hostname,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if error:
            login_data['error'] = error
            self.log_error(f"Login failed for {username}@{hostname}", extra_data=login_data)
        else:
            self.log_info(f"Login successful for {username}@{hostname}", extra_data=login_data)