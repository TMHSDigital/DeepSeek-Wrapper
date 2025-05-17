import json
import logging
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
    
    def run(self, **kwargs) -> ToolResult:
        """Execute the tool with the given parameters."""
        try:
            # Validate parameters
            if not self.validate_params(**kwargs):
                missing = [p for p in self.required_params if p not in kwargs]
                return ToolResult.error_result(
                    f"Missing required parameters: {', '.join(missing)}"
                )
            
            # Run the actual tool implementation
            self.logger.info(f"Running tool '{self.name}' with params: {kwargs}")
            result = self._run(**kwargs)
            self.logger.info(f"Tool '{self.name}' completed successfully")
            
            return ToolResult.success_result(result)
        except Exception as e:
            self.logger.error(f"Error running tool '{self.name}': {str(e)}", exc_info=True)
            return ToolResult.error_result(str(e))
    
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
    
    def run_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Run a tool by name with the given parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult.error_result(f"Tool '{tool_name}' not found")
        
        return tool.run(**kwargs)
    
    def __repr__(self) -> str:
        tool_list = ", ".join(self.list_tools())
        return f"ToolRegistry(tools=[{tool_list}])" 