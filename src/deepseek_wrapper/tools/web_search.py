import time
import json
import logging
import random
import requests
from typing import Dict, Any, List, Optional
import os

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)

class WebSearchTool(Tool[Dict[str, Any]]):
    """Tool for searching the web for information."""
    
    name = "web_search"
    description = "Search the web for real-time information on a given query"
    parameters = {
        "query": {
            "type": "string",
            "description": "The search query to look up information for"
        },
        "num_results": {
            "type": "integer",
            "description": "Number of search results to return (1-10)",
            "minimum": 1,
            "maximum": 10,
            "default": 3
        },
        "safe_search": {
            "type": "boolean", 
            "description": "Whether to enable safe search filtering",
            "default": True
        }
    }
    required_params = ["query"]
    
    # Default search providers in case no API keys are provided
    FALLBACK_PROVIDERS = [
        {
            "name": "Fallback Search",
            "description": "This is a simulated search result since no search API keys are configured."
        }
    ]
    
    def __init__(self, **kwargs):
        """Initialize the web search tool with optional configuration.
        
        Args:
            api_key: Optional API key for search service
            search_engine_id: Optional search engine ID for custom search
            rate_limit: Maximum requests per minute (default: 10)
        """
        super().__init__(**kwargs)
        
        # Get API keys from environment or config
        self.api_key = kwargs.get("api_key") or os.getenv("SEARCH_API_KEY")
        self.search_engine_id = kwargs.get("search_engine_id") or os.getenv("SEARCH_ENGINE_ID")
        
        # Validate API credentials
        self._validate_api_credentials()
        
        # Rate limiting
        self.rate_limit = kwargs.get("rate_limit", 10)  # requests per minute
        self.request_timestamps = []
        
        # Last API validation time
        self.last_api_validation = None
        self.api_validation_ttl = 3600  # Re-validate API key once per hour
        
        # Network status
        self.network_error_count = 0
        self.last_network_error = None
        
        # Retry settings
        self.retry_attempts = kwargs.get("retry_attempts", 3)
        self.retry_delay = kwargs.get("retry_delay", 1)  # seconds
        self.retry_backoff = kwargs.get("retry_backoff", 2)  # exponential backoff multiplier
        
    def _validate_api_credentials(self):
        """Validate API credentials and log appropriate warnings."""
        self.has_valid_credentials = False
        
        if not self.api_key:
            logger.warning("WebSearchTool: No API key configured (SEARCH_API_KEY not set)")
        elif len(self.api_key) < 10:  # Simple length check for likely invalid keys
            logger.warning(f"WebSearchTool: API key looks suspicious (length: {len(self.api_key)})")
        
        if not self.search_engine_id:
            logger.warning("WebSearchTool: No search engine ID configured (SEARCH_ENGINE_ID not set)")
        
        # Check if we have all required credentials
        if self.api_key and self.search_engine_id:
            self.has_valid_credentials = True
            logger.info("WebSearchTool: Valid API credentials detected")
            
            # Basic key format validation for Google API keys
            if not self.api_key.startswith("AIza"):
                logger.warning("WebSearchTool: API key doesn't match expected Google API key format")
        
        # Schedule a validation on first use
        self.last_api_validation = None
    
    def _test_api_key(self) -> bool:
        """Test the API key with a simple API call to validate it works.
        
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        current_time = time.time()
        
        # Skip validation if we've validated recently
        if (self.last_api_validation and 
            current_time - self.last_api_validation < self.api_validation_ttl):
            return self.has_valid_credentials
        
        if not self.api_key or not self.search_engine_id:
            self.has_valid_credentials = False
            return False
        
        try:
            # Use a simple, quick API call to test the key
            test_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": "test",  # Simple query that will always work
                "num": 1  # Just get one result to minimize quota usage
            }
            
            response = requests.get(test_url, params=params, timeout=5)
            
            if response.status_code == 200:
                self.has_valid_credentials = True
                self.logger.info("WebSearchTool: API key validated successfully")
            elif response.status_code == 400:
                error_data = response.json()
                if 'error' in error_data:
                    error_reason = error_data['error'].get('message', 'Unknown error')
                    self.logger.error(f"WebSearchTool: API key validation error (400): {error_reason}")
                    if 'API key' in error_reason:
                        self.has_valid_credentials = False
            elif response.status_code == 403:
                self.has_valid_credentials = False
                self.logger.error("WebSearchTool: API key validation error (403): Forbidden - likely restrictions or quota exceeded")
            else:
                # Other error codes might not indicate an invalid key
                self.logger.warning(f"WebSearchTool: API key validation returned status code {response.status_code}")
            
            # Update last validation time regardless of result
            self.last_api_validation = current_time
            
            return self.has_valid_credentials
        except Exception as e:
            self.logger.error(f"WebSearchTool: Error validating API key: {str(e)}")
            # Network errors don't necessarily mean the key is invalid,
            # so we don't change the existing validation status
            self.last_api_validation = current_time
            return self.has_valid_credentials
    
    def _run(self, query: str, num_results: int = 3, safe_search: bool = True) -> Dict[str, Any]:
        """Search the web for information.
        
        Args:
            query: The search query to look up
            num_results: Number of search results to return (1-10)
            safe_search: Whether to enable safe search filtering
            
        Returns:
            Dictionary containing search results and metadata
        """
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Sanitize inputs
        query = query.strip()
        num_results = max(1, min(10, num_results))  # Clamp between 1 and 10
        
        # Log the search attempt
        self.logger.info(f"Searching for: '{query}' (max results: {num_results})")
        
        try:
            # Validate credentials on first use or if validation has expired
            if (not self.last_api_validation or 
                time.time() - self.last_api_validation > self.api_validation_ttl):
                self._test_api_key()
            
            # If we have valid API keys, perform real search
            if self.has_valid_credentials:
                results = self._perform_real_search(query, num_results, safe_search)
            else:
                # Otherwise use fallback search simulation
                self.logger.warning("No valid search API credentials, using fallback search simulation")
                results = self._simulate_search(query, num_results)
                
            # Reset network error count on success
            self.network_error_count = 0
            self.last_network_error = None
                
            return {
                "query": query,
                "results": results,
                "num_results": len(results),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}", exc_info=True)
            # Return fallback results in case of error
            fallback_results = self._simulate_search(query, num_results, is_error=True)
            return {
                "query": query,
                "results": fallback_results,
                "num_results": len(fallback_results),
                "timestamp": time.time(),
                "error": str(e)
            }
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting to prevent overuse."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [t for t in self.request_timestamps if current_time - t < 60]
        
        # If we've hit the rate limit, sleep until we can make another request
        if len(self.request_timestamps) >= self.rate_limit:
            oldest_timestamp = min(self.request_timestamps)
            sleep_time = 60 - (current_time - oldest_timestamp)
            if sleep_time > 0:
                self.logger.warning(f"Rate limit hit, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Add current request timestamp
        self.request_timestamps.append(time.time())
    
    def _perform_real_search(self, query: str, num_results: int, safe_search: bool) -> List[Dict[str, str]]:
        """Perform a real search using an external API."""
        # Google Custom Search API example
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": num_results,
            "safe": "active" if safe_search else "off"
        }
        
        response = None
        last_error = None
        
        for attempt in range(self.retry_attempts + 1):
            try:
                response = requests.get(url, params=params, timeout=10)
                
                # Log rate limit information if available in headers
                if 'X-RateLimit-Limit' in response.headers:
                    self.logger.info(f"Search API rate limits - "
                                    f"Limit: {response.headers.get('X-RateLimit-Limit')}, "
                                    f"Remaining: {response.headers.get('X-RateLimit-Remaining')}")
                
                if response.status_code == 200:
                    break
                
                elif response.status_code == 400:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_reason = error_data['error'].get('message', 'Unknown error')
                        self.logger.error(f"Search API error (400): {error_reason}")
                        # Check for invalid API key
                        if 'API key' in error_reason:
                            self.has_valid_credentials = False
                            self.logger.error("Invalid API key detected, disabling real search")
                    last_error = f"Search API error: {error_reason if 'error_reason' in locals() else 'Bad Request'}"
                    break  # Don't retry on invalid key or bad request
                
                elif response.status_code == 403:
                    self.logger.error("Search API error (403): Forbidden - likely API key restrictions or quota exceeded")
                    self.has_valid_credentials = False
                    last_error = "Search API access forbidden (quota exceeded or restricted key)"
                    break  # Don't retry on forbidden
                    
                elif response.status_code == 429:
                    # Rate limit hit - always retry with backoff
                    self.logger.warning("Search API rate limit hit (429)")
                    if attempt < self.retry_attempts:
                        sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                        self.logger.info(f"Retrying in {sleep_time}s (attempt {attempt+1}/{self.retry_attempts})")
                        time.sleep(sleep_time)
                        continue
                    last_error = "Search API rate limit exceeded"
                    break
                
                else:
                    # Other error - retry with backoff
                    error_msg = f"Search API returned status code {response.status_code}"
                    try:
                        error_data = response.json()
                        if 'error' in error_data and 'message' in error_data['error']:
                            error_msg += f": {error_data['error']['message']}"
                    except:
                        if response.text:
                            error_msg += f": {response.text}"
                    
                    if attempt < self.retry_attempts:
                        sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                        self.logger.warning(f"{error_msg}. Retrying in {sleep_time}s (attempt {attempt+1}/{self.retry_attempts})")
                        time.sleep(sleep_time)
                        last_error = error_msg
                        continue
                    last_error = error_msg
                    break
                
            except requests.exceptions.Timeout:
                self.network_error_count += 1
                self.last_network_error = time.time()
                
                if attempt < self.retry_attempts:
                    sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                    self.logger.info(f"Request timed out, retrying in {sleep_time} seconds (attempt {attempt+1}/{self.retry_attempts})")
                    time.sleep(sleep_time)
                    last_error = "Search request timed out, please try again"
                    continue
                last_error = "Search request timed out after multiple attempts"
                break
            
            except requests.exceptions.ConnectionError:
                self.network_error_count += 1
                self.last_network_error = time.time()
                
                if attempt < self.retry_attempts:
                    sleep_time = self.retry_delay * (self.retry_backoff ** attempt)
                    self.logger.info(f"Connection error, retrying in {sleep_time} seconds (attempt {attempt+1}/{self.retry_attempts})")
                    time.sleep(sleep_time)
                    last_error = "Connection error when accessing search service"
                    continue
                last_error = "Connection error when accessing search service after multiple attempts"
                break
        
        # Handle errors after all retries
        if not response or response.status_code != 200:
            if last_error:
                raise Exception(last_error)
            raise Exception("Failed to get search results")
        
        try:
            data = response.json()
        except ValueError:
            raise Exception("Invalid JSON response from search service")
        
        results = []
        
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google Custom Search"
                })
        return results
    
    def _simulate_search(self, query: str, num_results: int, is_error: bool = False) -> List[Dict[str, str]]:
        """Simulate search results when no API is available or an error occurs."""
        if is_error:
            return [
                {
                    "title": "Search Error",
                    "snippet": "There was an error processing your search. Please try again later or refine your query.",
                    "link": "",
                    "source": "Error Fallback"
                }
            ]
        
        # Generate a deterministic but varied response based on the query
        random.seed(query)  # Make results deterministic for the same query
        
        results = []
        for i in range(min(num_results, 3)):  # Limit to 3 fallback results
            results.append({
                "title": f"Search result for: {query} (#{i+1})",
                "snippet": (
                    f"This is a simulated search result for '{query}'. "
                    f"In a real implementation, this would contain actual search results from the web. "
                    f"Configure SEARCH_API_KEY and SEARCH_ENGINE_ID environment variables to enable real search."
                ),
                "link": f"https://example.com/search?q={query.replace(' ', '+')}",
                "source": "Simulated Search"
            })
        
        return results
        
    def get_status(self) -> Dict[str, Any]:
        """Get additional status information specific to the web search tool."""
        status = super().get_status()
        
        # Add web search-specific information
        status.update({
            "search_engine_id": bool(self.search_engine_id),
            "api_key_validated": self.last_api_validation is not None,
            "api_validation_age": int(time.time() - self.last_api_validation) if self.last_api_validation else None,
            "network_errors": self.network_error_count
        })
        
        if self.last_network_error:
            status["last_network_error"] = time.strftime("%Y-%m-%d %H:%M:%S", 
                                                        time.localtime(self.last_network_error))
            status["last_error_age"] = int(time.time() - self.last_network_error)
        
        return status 