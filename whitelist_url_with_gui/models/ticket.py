"""
Data models for tickets and logging
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
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
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
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the whitelist request"""
        if not self.category:
            return False, "Category is required"
        
        if not self.urls:
            return False, "URLs list cannot be empty"
        
        if not self.ticket_id:
            return False, "Ticket ID is required"
        
        if self.action_type not in ['block-url', 'block-continue']:
            return False, "Invalid action type"
        
        return True, None

@dataclass
class SearchAttempt:
    """Data model for individual search attempts"""
    attempt_number: int
    timeout: int
    nlogs: int
    success: bool
    urls_found: int
    error: Optional[str] = None
    
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