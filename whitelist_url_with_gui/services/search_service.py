"""
URL Search Service
Handles targeted URL searching with multiple search terms and manual URL addition
Improved error handling and timeout management
"""
from datetime import datetime, timedelta
from typing import List, Set
import time
import re

from config import config
from models.ticket import SearchResult, SearchAttempt
from utils.validators import validate_search_term, validate_action_type

class SearchService:
    """Service for searching blocked URLs in Palo Alto logs"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def search_blocked_urls(self, search_terms: str, action_type: str = 'block-url') -> SearchResult:
        """
        Execute targeted search with multiple search terms using OR logic
        
        Args:
            search_terms: Comma-separated search terms to look for
            action_type: Action type to filter on ('block-url' or 'block-continue')
            
        Returns:
            SearchResult object with found URLs and metadata
        """
        try:
            # Parse and validate search terms
            parsed_terms = self._parse_search_terms(search_terms)
            if not parsed_terms:
                return SearchResult(
                    urls=[],
                    search_term=search_terms,
                    action_type=action_type,
                    strategy_info={},
                    success=False,
                    error="No valid search terms provided"
                )
            
            # Validate action type
            if not validate_action_type(action_type):
                return SearchResult(
                    urls=[],
                    search_term=search_terms,
                    action_type=action_type,
                    strategy_info={},
                    success=False,
                    error="Invalid action type"
                )
            
            print(f"[DEBUG] Starting MULTI-TERM search for: {parsed_terms}")
            print(f"[DEBUG] Strategy: Multiple terms with OR logic, action '{action_type}', multiple timeout attempts")
            
            blocked_urls = set()
            attempts = []
            
            # Calculate 3-month lookback date
            three_months_ago = datetime.now() - timedelta(days=config.LOOKBACK_MONTHS * 30)
            time_filter = three_months_ago.strftime("'%Y/%m/%d %H:%M:%S'")
            
            print(f"[DEBUG] Time filter: >= {time_filter}")
            
            # Build the multi-term OR query
            base_query = self._build_multi_term_query(parsed_terms, action_type, time_filter)
            
            # Execute multiple timeout attempts with better error handling
            attempts = self._execute_timeout_attempts_improved(base_query, search_terms, blocked_urls)
            
            # Prepare results
            final_urls = sorted(list(blocked_urls))
            successful_attempts = sum(1 for attempt in attempts if attempt.success)
            
            strategy_info = {
                'search_terms': parsed_terms,
                'search_terms_count': len(parsed_terms),
                'original_input': search_terms,
                'action_type': action_type,
                'results_found': len(final_urls),
                'search_strategy': 'multi_term_or_logic_multiple_timeouts_improved',
                'lookback_period': f'{config.LOOKBACK_MONTHS}_months',
                'max_entries': config.DEFAULT_MAX_RESULTS,
                'successful_attempts': f'{successful_attempts}/{len(attempts)}',
                'timeout_attempts': [attempt.to_dict() for attempt in attempts],
                'query_used': base_query
            }
            
            print(f"[DEBUG] MULTI-TERM Final results: {len(final_urls)} unique URLs")
            print(f"[DEBUG] Search terms used: {parsed_terms}")
            print(f"[DEBUG] Found URLs: {final_urls}")
            
            # Consider partial success if we found some URLs even if not all attempts succeeded
            is_success = len(final_urls) > 0 or successful_attempts > 0
            
            return SearchResult(
                urls=final_urls,
                search_term=search_terms,
                action_type=action_type,
                strategy_info=strategy_info,
                success=is_success
            )
            
        except Exception as e:
            print(f"[DEBUG] Exception in search_blocked_urls: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            
            return SearchResult(
                urls=[],
                search_term=search_terms,
                action_type=action_type,
                strategy_info={},
                success=False,
                error=str(e)
            )
    
    def _parse_search_terms(self, search_terms: str) -> List[str]:
        """Parse and validate multiple search terms"""
        if not search_terms:
            return []
        
        # Split by comma and clean up
        terms = []
        raw_terms = search_terms.split(',')
        
        for term in raw_terms:
            cleaned_term = term.strip()
            if cleaned_term and validate_search_term(cleaned_term):
                terms.append(cleaned_term)
            elif cleaned_term:
                print(f"[DEBUG] Skipping invalid search term: '{cleaned_term}'")
        
        return terms
    
    def _build_multi_term_query(self, search_terms: List[str], action_type: str, time_filter: str) -> str:
        """Build query with OR logic for multiple search terms"""
        if len(search_terms) == 1:
            # Single term - use simple query
            url_condition = f"url contains '{search_terms[0]}'"
        else:
            # Multiple terms - use OR logic
            url_conditions = [f"url contains '{term}'" for term in search_terms]
            url_condition = f"( {' ) or ( '.join(url_conditions)} )"
        
        query = f"( {url_condition} ) and ( action eq '{action_type}' ) and ( receive_time geq {time_filter} )"
        
        print(f"[DEBUG] Built query: {query}")
        return query
    
    def _execute_timeout_attempts_improved(self, base_query: str, search_terms: str, blocked_urls: Set[str]) -> List[SearchAttempt]:
        """Execute multiple timeout attempts with improved error handling"""
        attempts = []
        
        print(f"[DEBUG] Starting {len(config.SEARCH_TIMEOUT_ATTEMPTS)} timeout attempts (improved)")
        print(f"[DEBUG] Query: {base_query}")
        print(f"[DEBUG] ⏱️ Total estimated time: ~3-4 minutes")
        
        for attempt_num, timeout in enumerate(config.SEARCH_TIMEOUT_ATTEMPTS, 1):
            print(f"[DEBUG] === ATTEMPT {attempt_num}/{len(config.SEARCH_TIMEOUT_ATTEMPTS)}: Timeout {timeout}s ===")
            
            # Wait between attempts to avoid conflicts (except first attempt)
            if attempt_num > 1:
                print(f"[DEBUG] Waiting {config.ATTEMPT_WAIT_TIME} seconds before attempt {attempt_num}...")
                time.sleep(config.ATTEMPT_WAIT_TIME)
            
            urls_before = len(blocked_urls)
            attempt = self._execute_single_attempt_improved(
                base_query, 
                search_terms, 
                blocked_urls, 
                timeout, 
                config.DEFAULT_MAX_RESULTS, 
                f"Attempt{attempt_num}"
            )
            
            urls_after = len(blocked_urls)
            urls_added = urls_after - urls_before
            attempt.urls_found = urls_added
            
            attempts.append(attempt)
            
            if attempt.success:
                print(f"[DEBUG] ✅ Attempt {attempt_num} SUCCESS: Added {urls_added} URLs (Total: {len(blocked_urls)})")
                # If we got good results and have multiple attempts left, we might stop early
                if len(blocked_urls) >= 10 and attempt_num < len(config.SEARCH_TIMEOUT_ATTEMPTS):
                    print(f"[DEBUG] Got {len(blocked_urls)} URLs, considering early success...")
            else:
                print(f"[DEBUG] ❌ Attempt {attempt_num} FAILED: Added {urls_added} URLs (Total: {len(blocked_urls)})")
                print(f"[DEBUG] Error: {attempt.error}")
            
            # Show current progress
            if len(blocked_urls) > 0:
                print(f"[DEBUG] Current URLs after attempt {attempt_num}: {sorted(list(blocked_urls))}")
        
        return attempts
    
    def _execute_single_attempt_improved(self, query: str, search_terms: str, blocked_urls: Set[str], 
                                       timeout: int, nlogs: int, attempt_name: str) -> SearchAttempt:
        """Execute a single search attempt with improved error handling"""
        print(f"[DEBUG] {attempt_name}: Executing query with {timeout}s timeout, {nlogs} max logs")
        
        attempt = SearchAttempt(
            attempt_number=int(attempt_name.replace('Attempt', '')),
            timeout=timeout,
            nlogs=nlogs,
            success=False
        )
        
        try:
            # Execute the log query with extended timeout for API calls
            extended_timeout = timeout + 10  # Give API client more time
            print(f"[DEBUG] {attempt_name}: Using extended timeout of {extended_timeout}s for API call")
            
            result = self.api_client.execute_log_query(query, nlogs, extended_timeout)
            
            if result['type'] == 'direct':
                print(f"[DEBUG] {attempt_name}: DIRECT results - {len(result['entries'])} entries")
                matches_found = self._process_log_entries(result['entries'], search_terms, blocked_urls, attempt_name)
                if matches_found > 0:
                    attempt.success = True
                    print(f"[DEBUG] {attempt_name}: Direct query successful - {matches_found} matches")
                else:
                    attempt.error = "No matching URLs found in direct results"
            
            elif result['type'] == 'job':
                job_id = result['job_id']
                print(f"[DEBUG] {attempt_name}: Job {job_id} queued (will wait {timeout}s)")
                
                # Use extended timeout for job waiting as well
                job_results = self.api_client.wait_for_job(job_id, extended_timeout, attempt_name)
                if job_results:
                    logs = job_results.findall('.//entry')
                    print(f"[DEBUG] {attempt_name}: Job successful - {len(logs)} entries")
                    
                    if len(logs) > 0:
                        matches_found = self._process_log_entries(logs, search_terms, blocked_urls, f"{attempt_name} Job")
                        if matches_found > 0:
                            attempt.success = True
                            print(f"[DEBUG] {attempt_name}: Job successful - {matches_found} matches")
                        else:
                            attempt.error = "No matching URLs found in job results"
                    else:
                        attempt.error = "Job completed but returned no log entries"
                else:
                    print(f"[DEBUG] {attempt_name}: Job failed or timed out after {extended_timeout}s")
                    attempt.error = "Job timeout or failure"
            
            elif result['type'] == 'empty':
                print(f"[DEBUG] {attempt_name}: Empty result")
                attempt.error = "Empty result from firewall"
            else:
                attempt.error = f"Unknown result type: {result.get('type', 'unknown')}"
        
        except Exception as e:
            print(f"[DEBUG] {attempt_name}: Exception - {e}")
            # Try to provide more specific error messages
            error_str = str(e).lower()
            if "timeout" in error_str:
                attempt.error = f"Request timeout after {timeout}s"
            elif "connection" in error_str:
                attempt.error = f"Connection error: {str(e)}"
            elif "authentication" in error_str or "unauthorized" in error_str:
                attempt.error = f"Authentication error: {str(e)}"
            else:
                attempt.error = str(e)
        
        return attempt
    
    def _process_log_entries(self, logs, search_terms: str, blocked_urls: Set[str], test_name: str) -> int:
        """Process log entries and extract matching URLs"""
        matches_found = 0
        
        print(f"[DEBUG] {test_name}: Processing {len(logs)} entries for search terms")
        
        # Parse search terms for matching
        parsed_terms = self._parse_search_terms(search_terms)
        
        # Track what we find for debugging
        action_counts = {}
        
        # Process logs
        for j, log_entry in enumerate(logs):
            try:
                # Check ALL possible URL fields
                url_text = None
                for field_name in config.URL_SOURCES:
                    url_elem = log_entry.find(field_name)
                    if url_elem is not None and url_elem.text:
                        url_text = url_elem.text
                        break
                
                # Get action for tracking
                action_elem = log_entry.find('action')
                action_text = action_elem.text if action_elem is not None else 'unknown'
                
                # Count actions for debugging
                action_counts[action_text] = action_counts.get(action_text, 0) + 1
                
                # Debug first entry of each attempt
                if j == 0:
                    print(f"[DEBUG] {test_name} sample entry: url={url_text[:50] if url_text else 'None'}..., action={action_text}")
                
                # MULTI-TERM MATCHING: Check if URL contains any of the search terms
                if url_text and self._url_contains_any_term(url_text, parsed_terms):
                    found_domain = self._extract_exact_domain(url_text, parsed_terms)
                    
                    if found_domain and len(found_domain) > config.MIN_DOMAIN_LENGTH:
                        if matches_found < 10:  # Limit debug output
                            matching_term = self._get_matching_term(url_text, parsed_terms)
                            print(f"[DEBUG] {test_name} MATCH: {found_domain} (from: {url_text[:40]}..., matched: '{matching_term}', action: {action_text})")
                        blocked_urls.add(found_domain)
                        matches_found += 1
                        
            except Exception as e:
                if j < 3:  # Only debug first few errors
                    print(f"[DEBUG] {test_name} error processing entry {j}: {e}")
                continue
        
        # Show action distribution for debugging
        if action_counts and matches_found > 0:
            action_summary = ", ".join([f"{action}:{count}" for action, count in sorted(action_counts.items())])
            print(f"[DEBUG] {test_name} action distribution: {action_summary}")
        
        print(f"[DEBUG] {test_name} RESULT: {matches_found} matches found from {len(logs)} entries")
        return matches_found
    
    def _url_contains_any_term(self, url_text: str, search_terms: List[str]) -> bool:
        """Check if URL contains any of the search terms"""
        url_lower = url_text.lower()
        return any(term.lower() in url_lower for term in search_terms)
    
    def _get_matching_term(self, url_text: str, search_terms: List[str]) -> str:
        """Get the first matching search term for debugging"""
        url_lower = url_text.lower()
        for term in search_terms:
            if term.lower() in url_lower:
                return term
        return "unknown"
    
    def _extract_exact_domain(self, url_text: str, search_terms: List[str]) -> str:
        """Extract exact domain from URL text - no artificial variations"""
        try:
            # Method 1: Direct URL processing - extract EXACT domain from URL
            if '://' in url_text:
                clean_url = url_text.split('://', 1)[1]
            else:
                clean_url = url_text
            
            # Extract the EXACT domain part (before first slash, colon, or question mark)
            exact_domain = clean_url.split('/')[0].split(':')[0].split('?')[0].split('&')[0].strip().lower()
            if exact_domain and '.' in exact_domain and self._url_contains_any_term(exact_domain, search_terms):
                return exact_domain
            
            # Method 2: Handle multiple URLs in one field
            for separator in config.URL_SEPARATORS:
                if separator in url_text:
                    parts = url_text.split(separator)
                    for part in parts:
                        part = part.strip()
                        if part and self._url_contains_any_term(part, search_terms):
                            # Process this part
                            if '://' in part:
                                part = part.split('://', 1)[1]
                            domain = part.split('/')[0].split(':')[0].split('?')[0].split('&')[0].strip().lower()
                            if domain and '.' in domain and len(domain) > config.MIN_DOMAIN_LENGTH:
                                return domain
                    break
            
            return None
            
        except Exception as e:
            print(f"[DEBUG] Error extracting domain from {url_text[:50]}...: {e}")
            return None
    
    def validate_manual_urls(self, manual_urls: str) -> tuple[List[str], List[str]]:
        """
        Validate manually entered URLs
        
        Args:
            manual_urls: Comma-separated or newline-separated URLs
            
        Returns:
            Tuple of (valid_urls, invalid_urls)
        """
        if not manual_urls:
            return [], []
        
        # Split by comma or newline
        raw_urls = re.split(r'[,\n]', manual_urls)
        
        valid_urls = []
        invalid_urls = []
        
        for url in raw_urls:
            cleaned_url = url.strip()
            if not cleaned_url:
                continue
                
            # Basic validation
            if self._is_valid_manual_url(cleaned_url):
                # Normalize the URL (remove protocol, ensure it ends with /)
                normalized_url = self._normalize_manual_url(cleaned_url)
                valid_urls.append(normalized_url)
            else:
                invalid_urls.append(cleaned_url)
        
        return valid_urls, invalid_urls
    
    def _is_valid_manual_url(self, url: str) -> bool:
        """Check if manually entered URL is valid"""
        if len(url) < config.MIN_DOMAIN_LENGTH or len(url) > config.MAX_URL_LENGTH:
            return False
        
        # Remove protocol for validation
        clean_url = url
        if clean_url.startswith(('http://', 'https://')):
            clean_url = clean_url.split('://', 1)[1]
        
        # Allow wildcards at the beginning
        if clean_url.startswith('*.'):
            clean_url = clean_url[2:]
        
        # Basic domain pattern
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*(/.*)?$'
        
        return re.match(domain_pattern, clean_url) is not None
    
    def _normalize_manual_url(self, url: str) -> str:
        """Normalize manually entered URL"""
        # Remove protocol
        if url.startswith(('http://', 'https://')):
            url = url.split('://', 1)[1]
        
        # Handle wildcards
        if url.startswith('*.'):
            return url.lower()
        
        # Ensure non-wildcard domains end with /
        if not url.endswith('/') and '/' not in url:
            url += '/'
        
        return url.lower()