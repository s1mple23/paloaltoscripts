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
                commit_data['auto_commit_status']['status'] = 'FAILED'
                commit_data['auto_commit_status']['error'] = 'Failed to start commit'
                return commit_data
            
            commit_data['commit_job_id'] = job_id
            print(f"[DEBUG] Commit job {job_id} started successfully")
            
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
        polling_attempts = 0
        
        # Wait a bit before first poll to let the job initialize
        print(f"[DEBUG] Waiting 3 seconds for job {job_id} to initialize...")
        time.sleep(3)
        
        for poll_count in range(config.COMMIT_MAX_POLLS):
            polling_attempts += 1
            
            try:
                print(f"[DEBUG] Polling attempt {polling_attempts}: Getting status for job {job_id}")
                status_result = self.api_client.get_commit_status(job_id)
                
                commit_status = status_result.get('status', 'Unknown')
                commit_progress = status_result.get('progress', '0')
                
                print(f"[DEBUG] Auto-poll {poll_count + 1}/{config.COMMIT_MAX_POLLS}: Job={job_id}, Status={commit_status}, Progress={commit_progress}%")
                
                # Handle different status values
                if commit_status == 'FIN':
                    print(f"[DEBUG] ✅ Commit job {job_id} COMPLETED successfully!")
                    break
                elif commit_status == 'FAIL':
                    print(f"[DEBUG] ❌ Commit job {job_id} FAILED")
                    break
                elif commit_status in ['ACT', 'PEND', 'QUEUED']:
                    print(f"[DEBUG] ⏳ Commit job {job_id} is {commit_status} - continuing to poll")
                elif commit_status == 'Unknown':
                    print(f"[DEBUG] ⚠️ Commit job {job_id} status unknown - may still be processing")
                else:
                    print(f"[DEBUG] ℹ️ Commit job {job_id} has status: {commit_status}")
                
                # Check if progress indicates completion even if status isn't FIN yet
                if commit_progress == '100' and commit_status not in ['FIN', 'FAIL']:
                    print(f"[DEBUG] Progress is 100% but status is {commit_status} - waiting for final status...")
                    # Give it a bit more time to update to FIN
                    time.sleep(3)
                    
                    # One more check
                    try:
                        final_check = self.api_client.get_commit_status(job_id)
                        final_status = final_check.get('status', commit_status)
                        print(f"[DEBUG] Final status check: {final_status}")
                        if final_status == 'FIN':
                            commit_status = final_status
                            break
                    except:
                        print(f"[DEBUG] Final status check failed, keeping current status")
                
                # If we've been polling for a while and no completion, check less frequently
                if poll_count >= 5:
                    print(f"[DEBUG] Been polling for {(poll_count + 1) * config.COMMIT_POLL_INTERVAL} seconds...")
                    if poll_count >= 8:  # After ~50 seconds, reduce frequency
                        print(f"[DEBUG] Reducing polling frequency after {(poll_count + 1) * config.COMMIT_POLL_INTERVAL} seconds")
                        time.sleep(config.COMMIT_POLL_INTERVAL * 2)  # Wait longer between polls
                    else:
                        time.sleep(config.COMMIT_POLL_INTERVAL)
                else:
                    time.sleep(config.COMMIT_POLL_INTERVAL)
                    
            except Exception as e:
                print(f"[DEBUG] Error during auto-polling attempt {polling_attempts}: {e}")
                # Continue trying other polls even if one fails
                time.sleep(config.COMMIT_POLL_INTERVAL)
                continue
        
        # Final status determination
        if commit_status is None:
            print(f"[DEBUG] ⚠️ Auto-polling completed but no status received - job may still be processing")
            commit_status = 'IN_PROGRESS'
            commit_progress = 'Unknown'
        else:
            print(f"[DEBUG] ✅ Auto-polling finished. Final status: {commit_status}, Progress: {commit_progress}%")
        
        # Determine if polling was truly completed
        polling_completed = commit_status in ['FIN', 'FAIL']
        
        return {
            'commit_status': commit_status,
            'commit_progress': commit_progress,
            'auto_commit_status': {
                'status': commit_status,
                'progress': commit_progress,
                'auto_polled': True,
                'polling_completed': polling_completed,
                'polling_attempts': polling_attempts
            }
        }
    
    def get_commit_status(self, job_id: str) -> CommitStatus:
        """Get current commit status"""
        try:
            print(f"[DEBUG] Manual status check for job {job_id}")
            status_result = self.api_client.get_commit_status(job_id)
            
            status = status_result.get('status', 'Unknown')
            progress = status_result.get('progress', '0')
            
            print(f"[DEBUG] Manual status check result: Status={status}, Progress={progress}%")
            
            return CommitStatus(
                job_id=job_id,
                status=status,
                progress=progress,
                error=status_result.get('error')
            )
            
        except Exception as e:
            print(f"[DEBUG] Manual status check failed for job {job_id}: {e}")
            return CommitStatus(
                job_id=job_id,
                status='Error',
                progress='0',
                error=str(e)
            )