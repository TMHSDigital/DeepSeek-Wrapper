import logging
import os
import time
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)

class WolframAlphaTool(Tool[Dict[str, Any]]):
    """Tool for querying the Wolfram Alpha knowledge base for factual information."""
    
    name = "wolfram_alpha"
    description = "Query Wolfram Alpha for factual information, calculations, or data"
    parameters = {
        "query": {
            "type": "string",
            "description": "The query to send to Wolfram Alpha (e.g., 'mass of earth', 'solve x^2 + 2x - 3 = 0', 'population of France')"
        },
        "units": {
            "type": "string",
            "description": "Preferred unit system ('metric' or 'imperial')",
            "enum": ["metric", "imperial"],
            "default": "metric"
        },
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds for the API call",
            "minimum": 1,
            "maximum": 30,
            "default": 10
        }
    }
    required_params = ["query"]
    
    def __init__(self, **kwargs):
        """Initialize the Wolfram Alpha tool with optional configuration.
        
        Args:
            app_id: Optional Wolfram Alpha App ID
            rate_limit: Maximum requests per minute (default: 5)
        """
        super().__init__(**kwargs)
        
        # Get API credentials from environment or config
        self.app_id = kwargs.get("app_id") or os.getenv("WOLFRAM_ALPHA_APP_ID")
        
        # Rate limiting
        self.rate_limit = kwargs.get("rate_limit", 5)  # requests per minute
        self.request_timestamps = []
    
    def _run(self, query: str, units: str = "metric", timeout: int = 10) -> Dict[str, Any]:
        """Query Wolfram Alpha for information.
        
        Args:
            query: The query to send to Wolfram Alpha
            units: Preferred unit system ('metric' or 'imperial')
            timeout: Timeout in seconds for the API call
            
        Returns:
            Dictionary containing the results and metadata
        """
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Sanitize inputs
        query = query.strip()
        units = units.lower() if units in ["metric", "imperial"] else "metric"
        timeout = max(1, min(30, timeout))  # Clamp between 1 and 30
        
        self.logger.info(f"Querying Wolfram Alpha: '{query}' (units: {units})")
        
        try:
            if not self.app_id:
                self.logger.warning("No Wolfram Alpha App ID configured, using fallback response")
                return self._generate_fallback_response(query)
            
            # Make the actual API call
            result = self._query_wolfram_api(query, units, timeout)
            return result
            
        except Exception as e:
            self.logger.error(f"Wolfram Alpha query error: {str(e)}", exc_info=True)
            return {
                "query": query,
                "success": False,
                "error": str(e),
                "pods": [],
                "texts": ["Error: " + str(e)]
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
    
    def _query_wolfram_api(self, query: str, units: str, timeout: int) -> Dict[str, Any]:
        """Query the Wolfram Alpha API and process the response."""
        # Use the Full Results API for detailed response
        base_url = "https://api.wolframalpha.com/v2/query"
        
        params = {
            "input": query,
            "appid": self.app_id,
            "format": "plaintext",
            "output": "xml",
            "units": units,
            "podtimeout": "2",  # Pod computation timeout
            "formattimeout": "4"  # Formatting timeout
        }
        
        response = requests.get(base_url, params=params, timeout=timeout)
        
        if response.status_code != 200:
            raise Exception(f"Wolfram Alpha API returned status code {response.status_code}")
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        # Check if query was successful
        success = root.get('success') == 'true'
        error = root.get('error') == 'true'
        
        if error:
            error_msg = root.find('.//error/msg')
            error_text = error_msg.text if error_msg is not None else "Unknown error"
            raise Exception(f"Wolfram Alpha error: {error_text}")
        
        # Extract pods and their contents
        pods = []
        texts = []
        
        for pod in root.findall('.//pod'):
            pod_title = pod.get('title', '')
            pod_data = {
                "title": pod_title,
                "subpods": []
            }
            
            for subpod in pod.findall('.//subpod'):
                plaintext_elem = subpod.find('.//plaintext')
                if plaintext_elem is not None and plaintext_elem.text:
                    text = plaintext_elem.text.strip()
                    if text:
                        pod_data["subpods"].append({
                            "text": text,
                            "title": subpod.get('title', '')
                        })
                        texts.append(f"{pod_title}: {text}")
            
            if pod_data["subpods"]:
                pods.append(pod_data)
        
        # Create the result structure
        result = {
            "query": query,
            "success": success,
            "pods": pods,
            "texts": texts,
            "units": units
        }
        
        return result
    
    def _generate_fallback_response(self, query: str) -> Dict[str, Any]:
        """Generate a fallback response when no API key is available."""
        return {
            "query": query,
            "success": False,
            "pods": [],
            "texts": [
                "No Wolfram Alpha App ID configured.",
                "To use this tool, please set the WOLFRAM_ALPHA_APP_ID environment variable.",
                f"Your query was: '{query}'",
                "In a real implementation, this would return data from Wolfram Alpha."
            ],
            "error": "No Wolfram Alpha App ID configured"
        } 