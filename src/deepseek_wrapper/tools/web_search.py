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
        
        # Rate limiting
        self.rate_limit = kwargs.get("rate_limit", 10)  # requests per minute
        self.request_timestamps = []
        
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
            # If we have API keys, perform real search
            if self.api_key and self.search_engine_id:
                results = self._perform_real_search(query, num_results, safe_search)
            else:
                # Otherwise use fallback search simulation
                self.logger.warning("No search API keys configured, using fallback search simulation")
                results = self._simulate_search(query, num_results)
                
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
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            raise Exception(f"Search API returned status code {response.status_code}: {response.text}")
        
        data = response.json()
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