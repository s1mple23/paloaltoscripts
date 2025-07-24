"""
Whitelist Service
Handles URL category management and commit operations
"""
import time
from typing import Tuple, Dict, Any

from config import config
from models.ticket import CommitStatus, WhitelistRequest
from api.palo_alto_client import PaloAltoAPIError

class WhitelistService:
    """Service for managing URL whitelisting operations"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def get_categories(self) -> Dict[str, Any]:
        """Get all available custom URL categories"""
        try:
            return self.api_client.get_custom_url_categories()
        except PaloAltoAPIError as e:
            raise Exception(f"Failed to retrieve categories: {str(e)}")
    
    def submit_whitelist_request(self, request: WhitelistRequest) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Submit a whitelist request
        
        Args:
            request: WhitelistRequest object
            
        Returns:
            Tuple of (success, message, additional_data)
        """
        try:
            # Validate request
            is_valid, error_msg = request.validate()
            if not is_valid:
                return False, error_msg, {}
            
            # Get categories
            categories = self.get_categories()
            if request.category not in categories:
                return False, "Invalid category selected", {}
            
            category_info = categories[request.category]
            
            # Update category with new URLs
            update_success, update_message = self.api_client.update_category_urls(category_info, request.urls)
            
            if not update_success:
                return False, update_message, {}
            
            # Commit changes
            commit_data = self._handle_commit()
            
            return True, update_message, commit_data
            
        except Exception as e:
            return False, f"Whitelist request failed: {str(e)}", {}
    
    def _handle_commit(self) -> Dict[str, Any]:
        """Handle commit operation with automatic status polling"""
        commit_data = {
            'commit_job_id': None,
            'commit_status': None,
            'commit_progress': None,
            'auto_commit_status': {
                'status': 'SUBMITTED',
                'progress': '0',
                'auto_polled': False,
                'polling_completed': False
            }
        }
        
        try:
            # Start commit
            commit_success, job_id = self.api_client.commit_changes()
            if not commit_success:
                return commit_data
            
            commit_data['commit_job_id'] = job_id
            
            # Auto-poll commit status
            status_result = self._poll_commit_status(job_id)
            commit_data.update(status_result)
            
        except Exception as e:
            print(f"[DEBUG] Commit handling error: {e}")
            commit_data['auto_commit_status']['status'] = 'ERROR'
            commit_data['auto_commit_status']['error'] = str(e)
        
        return commit_data
    
    def _poll_commit_status(self, job_id: str) -> Dict[str, Any]:
        """Poll commit status with optimized timing"""
        print(f"[DEBUG] Starting optimized commit status polling for job {job_id}")
        
        commit_status = None
        commit_progress = None
        
        for poll_count in range(config.COMMIT_MAX_POLLS):
            time.sleep(config.COMMIT_POLL_INTERVAL)
            
            try:
                status_result = self.api_client.get_commit_status(job_id)
                commit_status = status_result.get('status', 'Unknown')
                commit_progress = status_result.get('progress', '0')
                
                print(f"[DEBUG] Auto-poll {poll_count + 1}/{config.COMMIT_MAX_POLLS}: Status={commit_status}, Progress={commit_progress}%")
                
                # If job is completed or failed, stop polling immediately
                if commit_status in ['FIN', 'FAIL']:
                    print(f"[DEBUG] Commit job completed with status: {commit_status}")
                    break
                    
                # If progress is 100%, give it one more quick check and exit
                if commit_progress == '100':
                    print(f"[DEBUG] Commit at 100%, doing final check...")
                    time.sleep(3)
                    try:
                        final_status = self.api_client.get_commit_status(job_id)
                        commit_status = final_status.get('status', commit_status)
                        print(f"[DEBUG] Final status check: {commit_status}")
                    except:
                        pass  # Don't fail if final check fails
                    break
                    
                # After 5 polls (30 seconds), check less frequently
                if poll_count >= 5:
                    print(f"[DEBUG] Switching to background mode after 30 seconds")
                    break  # Let user check manually if needed
                    
            except Exception as e:
                print(f"[DEBUG] Error during auto-polling: {e}")
                continue
        
        # Always provide a status, even if polling incomplete
        if commit_status is None:
            commit_status = 'IN_PROGRESS'
            commit_progress = 'Unknown'
            print(f"[DEBUG] Auto-polling completed with partial status")
        else:
            print(f"[DEBUG] Auto-polling finished with final status: {commit_status}")
        
        return {
            'commit_status': commit_status,
            'commit_progress': commit_progress,
            'auto_commit_status': {
                'status': commit_status or 'SUBMITTED',
                'progress': commit_progress or '0',
                'auto_polled': True,
                'polling_completed': commit_status in ['FIN', 'FAIL'] if commit_status else False
            }
        }
    
    def get_commit_status(self, job_id: str) -> CommitStatus:
        """Get current commit status"""
        try:
            status_result = self.api_client.get_commit_status(job_id)
            
            return CommitStatus(
                job_id=job_id,
                status=status_result.get('status', 'Unknown'),
                progress=status_result.get('progress', '0'),
                error=status_result.get('error')
            )
            
        except Exception as e:
            return CommitStatus(
                job_id=job_id,
                status='Error',
                progress='0',
                error=str(e)
            )