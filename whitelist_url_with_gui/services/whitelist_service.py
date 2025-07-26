"""
Whitelist Service
Handles URL category management and commit operations
Fixed error handling and commit status reporting
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
            
            # Commit changes with improved error handling
            commit_data = self._handle_commit_improved()
            
            return True, update_message, commit_data
            
        except Exception as e:
            print(f"[DEBUG] Whitelist request exception: {e}")
            return False, f"Whitelist request failed: {str(e)}", {}
    
    def _handle_commit_improved(self) -> Dict[str, Any]:
        """Handle commit operation with improved error handling"""
        commit_data = {
            'commit_job_id': None,
            'commit_status': None,
            'commit_progress': None,
            'auto_commit_status': {
                'status': 'STARTING',
                'progress': '0',
                'auto_polled': False,
                'polling_completed': False
            }
        }
        
        try:
            print("[DEBUG] Starting commit operation...")
            
            # Start commit
            commit_success, job_id = self.api_client.commit_changes()
            if not commit_success:
                commit_data['auto_commit_status']['status'] = 'FAILED'
                commit_data['auto_commit_status']['error'] = 'Failed to start commit'
                print("[DEBUG] Failed to start commit")
                return commit_data
            
            commit_data['commit_job_id'] = job_id
            commit_data['auto_commit_status']['status'] = 'SUBMITTED'
            print(f"[DEBUG] Commit job {job_id} started successfully")
            
            # Auto-poll commit status with better error handling
            try:
                status_result = self._poll_commit_status_improved(job_id)
                commit_data.update(status_result)
            except Exception as poll_error:
                print(f"[DEBUG] Polling failed but commit was submitted: {poll_error}")
                # Don't fail the whole operation if polling fails
                commit_data['auto_commit_status'] = {
                    'status': 'SUBMITTED',
                    'progress': 'unknown',
                    'auto_polled': False,
                    'polling_completed': False,
                    'error': f"Commit submitted but status polling failed: {str(poll_error)}"
                }
            
        except Exception as e:
            print(f"[DEBUG] Commit handling error: {e}")
            commit_data['auto_commit_status']['status'] = 'ERROR'
            commit_data['auto_commit_status']['error'] = str(e)
        
        return commit_data
    
    def _poll_commit_status_improved(self, job_id: str) -> Dict[str, Any]:
        """Poll commit status with improved error handling"""
        print(f"[DEBUG] Starting improved commit status polling for job {job_id}")
        
        commit_status = None
        commit_progress = None
        polling_attempts = 0
        last_error = None
        
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
                last_error = status_result.get('error')
                
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
                elif commit_status == 'Error':
                    print(f"[DEBUG] ❌ Commit job {job_id} has error status")
                    if last_error:
                        print(f"[DEBUG] Error details: {last_error}")
                    break
                else:
                    print(f"[DEBUG] ℹ️ Commit job {job_id} has status: {commit_status}")
                
                # Check if progress indicates completion
                if commit_progress == '100' and commit_status not in ['FIN', 'FAIL']:
                    print(f"[DEBUG] Progress is 100% but status is {commit_status} - waiting for final status...")
                    time.sleep(3)
                    
                    # One more check
                    try:
                        final_check = self.api_client.get_commit_status(job_id)
                        final_status = final_check.get('status', commit_status)
                        print(f"[DEBUG] Final status check: {final_status}")
                        if final_status == 'FIN':
                            commit_status = final_status
                            break
                    except Exception as final_error:
                        print(f"[DEBUG] Final status check failed: {final_error}")
                
                # Progressive wait times - start fast, then slow down
                if poll_count < 3:
                    wait_time = config.COMMIT_POLL_INTERVAL  # 6 seconds
                elif poll_count < 8:
                    wait_time = config.COMMIT_POLL_INTERVAL + 2  # 8 seconds
                else:
                    wait_time = config.COMMIT_POLL_INTERVAL + 4  # 10 seconds
                
                print(f"[DEBUG] Waiting {wait_time} seconds before next poll...")
                time.sleep(wait_time)
                    
            except Exception as e:
                print(f"[DEBUG] Error during auto-polling attempt {polling_attempts}: {e}")
                last_error = str(e)
                
                # Don't give up immediately on errors, try a few more times
                if poll_count < config.COMMIT_MAX_POLLS - 3:
                    print(f"[DEBUG] Will retry polling in {config.COMMIT_POLL_INTERVAL} seconds...")
                    time.sleep(config.COMMIT_POLL_INTERVAL)
                    continue
                else:
                    print(f"[DEBUG] Too many polling errors, stopping polling")
                    break
        
        # Final status determination
        if commit_status is None:
            print(f"[DEBUG] ⚠️ Auto-polling completed but no status received")
            commit_status = 'UNKNOWN'
            commit_progress = '0'
            if last_error:
                commit_status = 'ERROR'
        
        print(f"[DEBUG] ✅ Auto-polling finished. Final status: {commit_status}, Progress: {commit_progress}%")
        
        # Determine if polling was truly completed
        polling_completed = commit_status in ['FIN', 'FAIL', 'ERROR']
        
        auto_commit_status = {
            'status': commit_status,
            'progress': commit_progress,
            'auto_polled': True,
            'polling_completed': polling_completed,
            'polling_attempts': polling_attempts
        }
        
        if last_error and commit_status in ['ERROR', 'FAIL']:
            auto_commit_status['error'] = last_error
        
        return {
            'commit_status': commit_status,
            'commit_progress': commit_progress,
            'auto_commit_status': auto_commit_status
        }
    
    def get_commit_status(self, job_id: str) -> CommitStatus:
        """Get current commit status with better error handling"""
        try:
            print(f"[DEBUG] Manual status check for job {job_id}")
            status_result = self.api_client.get_commit_status(job_id)
            
            status = status_result.get('status', 'Unknown')
            progress = status_result.get('progress', '0')
            error = status_result.get('error')
            
            print(f"[DEBUG] Manual status check result: Status={status}, Progress={progress}%")
            
            return CommitStatus(
                job_id=job_id,
                status=status,
                progress=progress,
                error=error
            )
            
        except Exception as e:
            print(f"[DEBUG] Manual status check failed for job {job_id}: {e}")
            return CommitStatus(
                job_id=job_id,
                status='Error',
                progress='0',
                error=str(e)
            )