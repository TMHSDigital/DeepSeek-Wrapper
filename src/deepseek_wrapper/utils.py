import time
from functools import wraps
from typing import Callable

def retry(max_retries: int = 3, backoff: float = 1.0):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    from .errors import DeepSeekAuthError
                    if isinstance(e, DeepSeekAuthError):
                        raise
                    retries += 1
                    if retries > max_retries:
                        raise
                    time.sleep(backoff * (2 ** (retries - 1)))
        return wrapper
    return decorator

# Tool base class
class Tool:
    def run(self, *args, **kwargs):
        raise NotImplementedError("Each tool must implement the run method.")

# Tool registry
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def add_tool(self, name, tool):
        self.tools[name] = tool

    def get_tool(self, name):
        return self.tools.get(name)

    def run_tool(self, name, *args, **kwargs):
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return tool.run(*args, **kwargs)

class WebSearchTool(Tool):
    def run(self, query):
        # Placeholder: Replace with real web search logic
        return f"Web search results for: {query}" 