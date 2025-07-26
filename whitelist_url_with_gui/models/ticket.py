"""
Data models for tickets and logging
Enhanced with better validation and error handling
"""
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class TicketData:
    """Data model for whitelist ticket information"""
    ticket_id: str
    username: str
    hostname: str
    category: str
    context: str
    urls_added: List[str]
    success: bool
    timestamp: Optional[str] = None
    commit_job_id: Optional[str] = None
    commit_status: Optional[str] = None
    commit_progress: Optional[str] = None
    search_strategy: str = 'targeted_single_action'
    action_type: str = 'block-url'
    
    def __post_init__(self):
        """Set timestamp if not provided and clean data"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        
        # Clean string data
        if self.ticket_id:
            self.ticket_id = str(self.ticket_id).strip()
        if self.username:
            self.username = str(self.username).strip()
        if self.hostname:
            self.hostname = str(self.hostname).strip()
        if self.category:
            self.category = str(self.category).strip()
        if self.context:
            self.context = str(self.context).strip()
        
        # Ensure urls_added is a list of strings
        if self.urls_added:
            self.urls_added = [str(url).strip() for url in self.urls_added if url]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'ticket_id': self.ticket_id,
            'username': self.username,
            'hostname': self.hostname,
            'category': self.category,
            'context': self.context,
            'urls_added': self.urls_added,
            'success': self.success,
            'timestamp': self.timestamp,
            'commit_job_id': self.commit_job_id,
            'commit_status': self.commit_status,
            'commit_progress': self.commit_progress,
            'search_strategy': self.search_strategy,
            'action_type': self.action_type
        }

@dataclass
class SearchResult:
    """Data model for search results"""
    urls: List[str]
    search_term: str
    action_type: str
    strategy_info: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    
    def __post_init__(self):
        """Clean data after initialization"""
        # Ensure urls is a list of strings
        if self.urls:
            self.urls = [str(url).strip() for url in self.urls if url]
        else:
            self.urls = []
        
        # Clean string fields
        if self.search_term:
            self.search_term = str(self.search_term).strip()
        if self.action_type:
            self.action_type = str(self.action_type).strip()
        if self.error:
            self.error = str(self.error).strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'urls': self.urls,
            'search_term': self.search_term,
            'action_type': self.action_type,
            'strategy_info': self.strategy_info,
            'success': self.success,
            'error': self.error,
            'count': len(self.urls)
        }

@dataclass
class CommitStatus:
    """Data model for commit status"""
    job_id: str
    status: str
    progress: str
    auto_polled: bool = False
    polling_completed: bool = False
    error: Optional[str] = None
    
    def __post_init__(self):
        """Clean data after initialization"""
        if self.job_id:
            self.job_id = str(self.job_id).strip()
        if self.status:
            self.status = str(self.status).strip()
        if self.progress:
            self.progress = str(self.progress).strip()
        if self.error:
            self.error = str(self.error).strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'progress': self.progress,
            'auto_polled': self.auto_polled,
            'polling_completed': self.polling_completed,
            'error': self.error
        }

@dataclass
class WhitelistRequest:
    """Data model for whitelist requests"""
    category: str
    urls: List[str]
    ticket_id: str
    action_type: str = 'block-url'
    
    def __post_init__(self):
        """Clean and validate data after initialization"""
        # Clean strings
        if self.category:
            self.category = str(self.category).strip()
        if self.ticket_id:
            self.ticket_id = str(self.ticket_id).strip()
        if self.action_type:
            self.action_type = str(self.action_type).strip()
        
        # Ensure urls is a list of strings
        if self.urls:
            self.urls = [str(url).strip() for url in self.urls if url]
        else:
            self.urls = []
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the whitelist request"""
        try:
            if not self.category or len(self.category.strip()) == 0:
                return False, "Category is required"
            
            if not self.urls or len(self.urls) == 0:
                return False, "URLs list cannot be empty"
            
            if not self.ticket_id or len(self.ticket_id.strip()) == 0:
                return False, "Ticket ID is required"
            
            if self.action_type not in ['block-url', 'block-continue']:
                return False, "Invalid action type"
            
            # Additional validation
            if len(self.category) > 200:
                return False, "Category name is too long"
            
            if len(self.ticket_id) > 100:
                return False, "Ticket ID is too long"
            
            if len(self.urls) > 200:
                return False, "Too many URLs (maximum: 200)"
            
            # Check for dangerous characters in strings
            dangerous_chars = ['<', '>', '"', "'", ';', '&', '`', '|', '\\']
            
            for char in dangerous_chars:
                if char in self.category:
                    return False, f"Category contains invalid character: {char}"
                if char in self.ticket_id:
                    return False, f"Ticket ID contains invalid character: {char}"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

@dataclass
class SearchAttempt:
    """Data model for individual search attempts"""
    attempt_number: int
    timeout: int
    nlogs: int
    success: bool
    urls_found: int = 0  # Default value
    error: Optional[str] = None
    
    def __post_init__(self):
        """Clean data after initialization"""
        if self.error:
            self.error = str(self.error).strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'attempt_number': self.attempt_number,
            'timeout': self.timeout,
            'nlogs': self.nlogs,
            'success': self.success,
            'urls_found': self.urls_found,
            'error': self.error
        }

# Additional utility classes for enhanced functionality

@dataclass
class ValidationResult:
    """Data model for validation results"""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        """Initialize warnings list if None"""
        if self.warnings is None:
            self.warnings = []
    
    def add_warning(self, warning: str):
        """Add a warning message"""
        if warning and warning.strip():
            self.warnings.append(warning.strip())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'is_valid': self.is_valid,
            'error_message': self.error_message,
            'warnings': self.warnings
        }

@dataclass
class APIConnectionInfo:
    """Data model for API connection information"""
    hostname: str
    username: str
    connected: bool
    api_key_valid: bool
    last_test_time: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Set last test time if not provided"""
        if self.last_test_time is None:
            self.last_test_time = datetime.now().isoformat()
        
        # Clean string data
        if self.hostname:
            self.hostname = str(self.hostname).strip()
        if self.username:
            self.username = str(self.username).strip()
        if self.error_message:
            self.error_message = str(self.error_message).strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'hostname': self.hostname,
            'username': self.username,
            'connected': self.connected,
            'api_key_valid': self.api_key_valid,
            'last_test_time': self.last_test_time,
            'error_message': self.error_message
        }

@dataclass
class LogQueryResult:
    """Data model for log query results"""
    query: str
    result_type: str  # 'direct', 'job', 'empty'
    entries_found: int
    job_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    
    def __post_init__(self):
        """Clean data after initialization"""
        if self.query:
            self.query = str(self.query).strip()
        if self.result_type:
            self.result_type = str(self.result_type).strip()
        if self.job_id:
            self.job_id = str(self.job_id).strip()
        if self.error_message:
            self.error_message = str(self.error_message).strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'query': self.query,
            'result_type': self.result_type,
            'entries_found': self.entries_found,
            'job_id': self.job_id,
            'success': self.success,
            'error_message': self.error_message,
            'execution_time': self.execution_time
        }