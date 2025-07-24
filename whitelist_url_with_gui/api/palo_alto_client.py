"""
Palo Alto Firewall API Client
Handles all communication with Palo Alto firewalls via XML API
"""
import requests
import xml.etree.ElementTree as ET
import urllib3
from urllib.parse import quote
from config import config

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PaloAltoAPIError(Exception):
    """Custom exception for Palo Alto API errors"""
    pass

class PaloAltoAPI:
    """Palo Alto Firewall API Client"""
    
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.api_key = None
        self.base_url = f"https://{hostname}/api"
        
    def get_api_key(self):
        """Authenticate and retrieve API key"""
        try:
            auth_url = f"{self.base_url}/?type=keygen&user={self.username}&password={self.password}"
            response = requests.get(auth_url, verify=False, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                self.api_key = root.find('.//key').text
                return True
            else:
                error_msg = root.find('.//msg')
                raise PaloAltoAPIError(f"Authentication failed: {error_msg.text if error_msg is not None else 'Unknown error'}")
                
        except requests.exceptions.RequestException as e:
            raise PaloAltoAPIError(f"Connection error: {str(e)}")
        except ET.ParseError as e:
            raise PaloAltoAPIError(f"XML parsing error: {str(e)}")
    
    def test_connectivity(self):
        """Test basic API connectivity and permissions"""
        try:
            test_url = f"{self.base_url}/?type=op&cmd=<show><system><info></info></system></show>&key={self.api_key}"
            response = requests.get(test_url, verify=False, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                return {'success': True, 'message': 'API connectivity OK'}
            else:
                error_msg = root.find('.//msg')
                error_text = error_msg.text if error_msg is not None else 'Unknown error'
                
                # Try version check as fallback
                simple_test_url = f"{self.base_url}/?type=version&key={self.api_key}"
                simple_response = requests.get(simple_test_url, verify=False, timeout=config.API_TIMEOUT)
                simple_response.raise_for_status()
                
                simple_root = ET.fromstring(simple_response.text)
                if simple_root.get('status') == 'success':
                    return {'success': True, 'message': 'API connectivity OK (version check)'}
                else:
                    return {'success': False, 'error': f"API test failed: {error_text}"}
                
        except Exception as e:
            return {'success': False, 'error': f"Connectivity test failed: {str(e)}"}
    
    def execute_log_query(self, query, nlogs, timeout):
        """Execute a log query and return results"""
        try:
            log_url = f"{self.base_url}/?type=log&log-type=url&key={self.api_key}&query={quote(query)}&nlogs={nlogs}"
            
            response = requests.get(log_url, verify=False, timeout=timeout)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                # Check for direct results first
                logs = root.findall('.//entry')
                if len(logs) > 0:
                    return {'type': 'direct', 'data': root, 'entries': logs}
                else:
                    # Job required
                    job_elem = root.find('.//job')
                    if job_elem is not None:
                        return {'type': 'job', 'job_id': job_elem.text}
                    else:
                        return {'type': 'empty', 'data': None}
            else:
                error_msg = root.find('.//msg')
                error_text = error_msg.text if error_msg is not None else 'Unknown'
                raise PaloAltoAPIError(f"Log query failed: {error_text}")
                
        except requests.exceptions.RequestException as e:
            raise PaloAltoAPIError(f"Log query request failed: {str(e)}")
        except ET.ParseError as e:
            raise PaloAltoAPIError(f"Log query XML parsing error: {str(e)}")
    
    def wait_for_job(self, job_id, max_wait, job_name="Job"):
        """Wait for a job to complete and return results"""
        import time
        
        print(f"[DEBUG] {job_name}: Waiting for job {job_id} (max: {max_wait}s)...")
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                status_url = f"{self.base_url}/?type=op&cmd=<show><jobs><id>{job_id}</id></jobs></show>&key={self.api_key}"
                status_response = requests.get(status_url, verify=False, timeout=config.STATUS_CHECK_TIMEOUT)
                status_response.raise_for_status()
                
                status_root = ET.fromstring(status_response.text)
                if status_root.get('status') == 'success':
                    job = status_root.find('.//job')
                    if job is not None:
                        status = job.find('status')
                        progress = job.find('progress')
                        status_text = status.text if status is not None else 'Unknown'
                        progress_text = progress.text if progress is not None else '0'
                        
                        print(f"[DEBUG] {job_name}: Job {job_id} - {status_text}, {progress_text}% (waited {wait_time}s)")
                        
                        # COMPLETED - Get results
                        if status_text == 'FIN':
                            print(f"[DEBUG] {job_name}: Job {job_id} COMPLETED!")
                            return self.get_job_results(job_id)
                        
                        # FAILED - Stop immediately
                        elif status_text == 'FAIL':
                            print(f"[DEBUG] {job_name}: Job {job_id} FAILED")
                            return None
                        
                        # Continue waiting for ACT, PEND, etc.
                    else:
                        print(f"[DEBUG] {job_name}: Job {job_id} - no job info found")
                        return None
                else:
                    print(f"[DEBUG] {job_name}: Job {job_id} - API status error")
                    return None
                
                time.sleep(config.JOB_CHECK_INTERVAL)
                wait_time += config.JOB_CHECK_INTERVAL
                
            except Exception as e:
                print(f"[DEBUG] {job_name}: Job status check error - {e}")
                time.sleep(config.JOB_CHECK_INTERVAL)
                wait_time += config.JOB_CHECK_INTERVAL
                continue
        
        print(f"[DEBUG] {job_name}: Job {job_id} timed out after {max_wait} seconds")
        return None
    
    def get_job_results(self, job_id):
        """Get job results"""
        try:
            result_url = f"{self.base_url}/?type=log&action=get&job-id={job_id}&key={self.api_key}"
            result_response = requests.get(result_url, verify=False, timeout=config.API_TIMEOUT)
            result_response.raise_for_status()
            
            result_root = ET.fromstring(result_response.text)
            if result_root.get('status') == 'success':
                logs = result_root.findall('.//entry')
                print(f"[DEBUG] Job {job_id} results: {len(logs)} entries retrieved")
                return result_root
            else:
                error_msg = result_root.find('.//msg')
                error_text = error_msg.text if error_msg is not None else 'Unknown error'
                print(f"[DEBUG] Job {job_id} result retrieval failed: {error_text}")
                return None
                
        except Exception as e:
            print(f"[DEBUG] Exception getting job {job_id} results: {e}")
            return None
    
    def get_custom_url_categories(self):
        """Retrieve all custom URL categories from all vsys and shared"""
        try:
            categories = {}
            
            # Get shared categories
            shared_url = f"{self.base_url}/?type=config&action=get&xpath=/config/shared/profiles/custom-url-category&key={self.api_key}"
            response = requests.get(shared_url, verify=False, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                shared_cats = root.findall('.//entry')
                for cat in shared_cats:
                    name = cat.get('name')
                    if name:
                        categories[f"{name} (shared)"] = {
                            'name': name,
                            'context': 'shared',
                            'xpath': f"/config/shared/profiles/custom-url-category/entry[@name='{name}']"
                        }
            
            # Get vsys categories
            vsys_list_url = f"{self.base_url}/?type=config&action=get&xpath=/config/devices/entry[@name='localhost.localdomain']/vsys&key={self.api_key}"
            response = requests.get(vsys_list_url, verify=False, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                vsys_entries = root.findall('.//vsys/entry')
                for vsys_entry in vsys_entries:
                    vsys_name = vsys_entry.get('name', 'vsys1')
                    
                    vsys_url = f"{self.base_url}/?type=config&action=get&xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='{vsys_name}']/profiles/custom-url-category&key={self.api_key}"
                    response = requests.get(vsys_url, verify=False, timeout=config.API_TIMEOUT)
                    response.raise_for_status()
                    
                    vsys_root = ET.fromstring(response.text)
                    if vsys_root.get('status') == 'success':
                        vsys_cats = vsys_root.findall('.//entry')
                        for cat in vsys_cats:
                            name = cat.get('name')
                            if name:
                                display_name = f"{name} ({vsys_name})"
                                categories[display_name] = {
                                    'name': name,
                                    'context': vsys_name,
                                    'xpath': f"/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='{vsys_name}']/profiles/custom-url-category/entry[@name='{name}']"
                                }
            
            return categories
            
        except Exception as e:
            raise PaloAltoAPIError(f"Error retrieving URL categories: {str(e)}")
    
    def get_category_urls(self, category_info):
        """Get existing URLs in a category"""
        try:
            xpath = category_info['xpath'] + "/list"
            get_url = f"{self.base_url}/?type=config&action=get&xpath={xpath}&key={self.api_key}"
            
            response = requests.get(get_url, verify=False, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                url_members = root.findall('.//member')
                return [member.text for member in url_members if member.text]
            
            return []
            
        except Exception as e:
            raise PaloAltoAPIError(f"Error getting category URLs: {str(e)}")
    
    def update_category_urls(self, category_info, new_urls):
        """Update URL category with new URLs (preserving existing ones)"""
        try:
            # Get existing URLs
            existing_urls = self.get_category_urls(category_info)
            
            # Combine existing and new URLs, removing duplicates
            all_urls = list(set(existing_urls + new_urls))
            
            # Check if any new URLs were actually added
            newly_added = [url for url in new_urls if url not in existing_urls]
            
            if not newly_added:
                return False, "No new URLs to add - all URLs already exist in the category"
            
            # Build XML for the list
            list_xml = "<list>"
            for url in sorted(all_urls):
                list_xml += f"<member>{url}</member>"
            list_xml += "</list>"
            
            # Update the category
            xpath = category_info['xpath'] + "/list"
            update_url = f"{self.base_url}/?type=config&action=edit&xpath={xpath}&element={quote(list_xml)}&key={self.api_key}"
            
            response = requests.post(update_url, verify=False, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                return True, f"Successfully added {len(newly_added)} new URLs to category"
            else:
                error_msg = root.find('.//msg')
                raise PaloAltoAPIError(f"Update failed: {error_msg.text if error_msg is not None else 'Unknown error'}")
                
        except Exception as e:
            raise PaloAltoAPIError(f"Error updating category: {str(e)}")
    
    def commit_changes(self):
        """Commit configuration changes"""
        try:
            commit_url = f"{self.base_url}/?type=commit&cmd=<commit></commit>&key={self.api_key}"
            
            response = requests.post(commit_url, verify=False, timeout=config.COMMIT_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                job_elem = root.find('.//job')
                job_id = job_elem.text if job_elem is not None else 'Unknown'
                return True, job_id
            else:
                error_msg = root.find('.//msg')
                raise PaloAltoAPIError(f"Commit failed: {error_msg.text if error_msg is not None else 'Unknown error'}")
                
        except Exception as e:
            raise PaloAltoAPIError(f"Error committing changes: {str(e)}")
    
    def get_commit_status(self, job_id):
        """Check commit job status"""
        try:
            status_url = f"{self.base_url}/?type=op&cmd=<show><jobs><id>{job_id}</id></jobs></show>&key={self.api_key}"
            
            response = requests.get(status_url, verify=False, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            if root.get('status') == 'success':
                job = root.find('.//job')
                if job is not None:
                    status = job.find('status')
                    progress = job.find('progress')
                    return {
                        'status': status.text if status is not None else 'Unknown',
                        'progress': progress.text if progress is not None else '0'
                    }
            
            return {'status': 'Unknown', 'progress': '0'}
            
        except Exception as e:
            return {'status': 'Error', 'progress': '0', 'error': str(e)}
    
    def get_log_types_available(self):
        """Check what log types are available - Focus on URL logs"""
        available_logs = {}
        
        log_type = 'url'
        try:
            # Test URL log access with multiple approaches
            approaches = [
                f"{self.base_url}/?type=log&log-type={log_type}&key={self.api_key}&nlogs=10",
                f"{self.base_url}/?type=log&log-type={log_type}&key={self.api_key}&nlogs=10&query=(action eq 'block-url')",
                f"{self.base_url}/?type=log&log-type={log_type}&key={self.api_key}",
            ]
            
            for i, test_url in enumerate(approaches):
                try:
                    print(f"[DEBUG] Testing URL logs approach {i+1}")
                    response = requests.get(test_url, verify=False, timeout=config.API_TIMEOUT)
                    response.raise_for_status()
                    
                    root = ET.fromstring(response.text)
                    if root.get('status') == 'success':
                        job_elem = root.find('.//job')
                        if job_elem is not None:
                            job_id = job_elem.text
                            print(f"[DEBUG] URL logs approach {i+1} got job ID: {job_id}")
                            available_logs['url'] = f"Job queued: {job_id}"
                            break
                        else:
                            entries = root.findall('.//entry')
                            print(f"[DEBUG] URL logs approach {i+1} found {len(entries)} entries")
                            if len(entries) > 0:
                                available_logs['url'] = len(entries)
                                break
                            else:
                                available_logs['url'] = f"Approach {i+1}: 0 entries"
                    else:
                        error_msg = root.find('.//msg')
                        error_text = error_msg.text if error_msg is not None else 'Unknown error'
                        print(f"[DEBUG] URL logs approach {i+1} error: {error_text}")
                        available_logs['url'] = f"Approach {i+1}: Error - {error_text}"
                        
                except Exception as e:
                    print(f"[DEBUG] URL logs approach {i+1} exception: {e}")
                    available_logs['url'] = f"Approach {i+1}: Exception - {str(e)}"
                    continue
            
            if 'url' not in available_logs:
                available_logs['url'] = "All approaches failed"
                
        except Exception as e:
            available_logs['url'] = f"Critical error: {str(e)}"
        
        return available_logs