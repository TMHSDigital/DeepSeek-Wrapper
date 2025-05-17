import json
import logging
import time
import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic

logger = logging.getLogger(__name__)

class ToolResult:
    """Represents the result of running a tool."""
    
    def __init__(
        self, 
        success: bool, 
        content: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.content = content
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        result = {
            "success": self.success,
            "content": self.content
        }
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    def to_json(self) -> str:
        """Convert the result to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def success_result(cls, content: Any, metadata: Optional[Dict[str, Any]] = None) -> 'ToolResult':
        """Create a successful result."""
        return cls(True, content=content, metadata=metadata)
    
    @classmethod
    def error_result(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> 'ToolResult':
        """Create an error result."""
        return cls(False, error=error, metadata=metadata)
    
    def __repr__(self) -> str:
        if self.success:
            return f"ToolResult(success=True, content={repr(self.content)})"
        else:
            return f"ToolResult(success=False, error={repr(self.error)})"

T = TypeVar('T')

class Tool(ABC, Generic[T]):
    """Base class for all tools that can be called by the AI."""
    
    name: str = None
    description: str = None
    parameters: Dict[str, Dict[str, Any]] = None
    required_params: List[str] = None
    
    def __init__(self, **kwargs):
        """Initialize the tool with optional configuration."""
        self.config = kwargs
        if not self.name:
            self.name = self.__class__.__name__
        
        if not self.description:
            self.description = self.__doc__ or "No description provided"
        
        if not self.parameters:
            self.parameters = {}
        
        if not self.required_params:
            self.required_params = []
            
        # Configure logging
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
        # Cache configuration
        self.use_cache = kwargs.get("use_cache", True)
        self.cache_ttl = kwargs.get("cache_ttl", 300)  # Default 5 minutes
        self.cache = {}
        
        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_used_time = None
        self.creation_time = time.time()
    
    def validate_params(self, **kwargs) -> bool:
        """Validate if all required parameters are present."""
        for param in self.required_params:
            if param not in kwargs:
                return False
        return True
    
    @abstractmethod
    def _run(self, **kwargs) -> T:
        """Internal method that implements the tool's functionality."""
        pass
    
    def _get_cache_key(self, **kwargs) -> str:
        """Generate a cache key from the tool parameters."""
        # Sort to ensure consistent ordering
        sorted_items = sorted(kwargs.items())
        param_str = json.dumps(sorted_items)
        return f"{self.name}:{param_str}"
    
    def _is_cache_valid(self, cache_entry):
        """Check if a cache entry is still valid based on TTL."""
        if not cache_entry or "timestamp" not in cache_entry:
            return False
        return (time.time() - cache_entry["timestamp"]) < self.cache_ttl
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool's cache usage."""
        expired_count = 0
        valid_count = 0
        
        # Count expired vs valid entries
        for entry in self.cache.values():
            if self._is_cache_valid(entry):
                valid_count += 1
            else:
                expired_count += 1
        
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "size": len(self.cache),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
            "ttl": self.cache_ttl,
            "last_used": self.last_used_time,
            "creation_time": self.creation_time
        }
    
    def cleanup_expired_cache(self):
        """Remove expired entries from the cache."""
        expired_keys = []
        current_time = time.time()
        
        # Find expired keys
        for key, entry in self.cache.items():
            if "timestamp" in entry and (current_time - entry["timestamp"]) >= self.cache_ttl:
                expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            del self.cache[key]
            
        return len(expired_keys)
    
    def run(self, **kwargs) -> ToolResult:
        """Execute the tool with the given parameters."""
        try:
            # Update last used time
            self.last_used_time = time.time()
            
            # Validate parameters
            if not self.validate_params(**kwargs):
                missing = [p for p in self.required_params if p not in kwargs]
                return ToolResult.error_result(
                    f"Missing required parameters: {', '.join(missing)}"
                )
            
            # Check cache if enabled
            if self.use_cache:
                cache_key = self._get_cache_key(**kwargs)
                cache_entry = self.cache.get(cache_key)
                
                if cache_entry and self._is_cache_valid(cache_entry):
                    self.logger.info(f"Using cached result for tool '{self.name}'")
                    self.cache_hits += 1
                    # Update accessed timestamp to extend life of frequently used entries
                    cache_entry["last_accessed"] = time.time()
                    return cache_entry["result"]
                
                self.cache_misses += 1
                
                # Periodically clean up expired cache entries (every 20 misses)
                if self.cache_misses % 20 == 0 and len(self.cache) > 10:
                    removed = self.cleanup_expired_cache()
                    if removed > 0:
                        self.logger.info(f"Cleaned up {removed} expired cache entries for tool '{self.name}'")
            
            # Run the actual tool implementation
            self.logger.info(f"Running tool '{self.name}' with params: {kwargs}")
            result = self._run(**kwargs)
            self.logger.info(f"Tool '{self.name}' completed successfully")
            
            # Create success result
            tool_result = ToolResult.success_result(result)
            
            # Cache the result if caching is enabled
            if self.use_cache:
                cache_key = self._get_cache_key(**kwargs)
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "last_accessed": time.time(),
                    "result": tool_result
                }
            
            return tool_result
        except Exception as e:
            self.logger.error(f"Error running tool '{self.name}': {str(e)}", exc_info=True)
            return ToolResult.error_result(str(e))
    
    def clear_cache(self):
        """Clear the tool's cache."""
        cache_size = len(self.cache)
        self.cache = {}
        self.logger.info(f"Cleared cache for tool '{self.name}' ({cache_size} entries)")
        
        # Reset cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required_params
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status and metadata for this tool."""
        status = {
            "name": self.name,
            "description": self.description,
            "cache_enabled": self.use_cache,
            "cache_ttl": self.cache_ttl,
            "cache_size": len(self.cache),
            "required_params": self.required_params,
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_ratio": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
            }
        }
        
        # Format timestamps if they exist
        if self.last_used_time:
            last_used_dt = datetime.datetime.fromtimestamp(self.last_used_time)
            status["last_used"] = last_used_dt.strftime("%Y-%m-%d %H:%M:%S")
            status["last_used_seconds_ago"] = int(time.time() - self.last_used_time)
        
        # Add API key information if present in any attribute
        if hasattr(self, "api_key"):
            status["has_api_key"] = bool(self.api_key)
        if hasattr(self, "has_valid_api_key"):
            status["api_key_valid"] = self.has_valid_api_key
        elif hasattr(self, "has_valid_credentials"):
            status["has_valid_credentials"] = self.has_valid_credentials
            
        return status
    
    def __repr__(self) -> str:
        return f"{self.name}(description='{self.description}')"


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        """Initialize an empty tools registry."""
        self.tools: Dict[str, Tool] = {}
        self.logger = logging.getLogger(f"{__name__}.ToolRegistry")
    
    def register(self, tool: Tool) -> None:
        """Register a tool with the registry."""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, tool_name: str) -> None:
        """Remove a tool from the registry."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.logger.info(f"Unregistered tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """Get a list of all registered tool names."""
        return list(self.tools.keys())
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get JSON schemas for all registered tools."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def get_tools_status(self) -> List[Dict[str, Any]]:
        """Get status information for all registered tools."""
        return [tool.get_status() for tool in self.tools.values()]
    
    def run_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Run a tool by name with the given parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult.error_result(f"Tool '{tool_name}' not found")
        
        return tool.run(**kwargs)
    
    def clear_all_caches(self) -> None:
        """Clear caches for all registered tools."""
        for tool in self.tools.values():
            tool.clear_cache()
        self.logger.info("Cleared caches for all tools")
    
    def __repr__(self) -> str:
        tool_list = ", ".join(self.list_tools())
        return f"ToolRegistry(tools=[{tool_list}])" 