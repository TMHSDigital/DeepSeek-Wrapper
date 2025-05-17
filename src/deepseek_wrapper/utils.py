import time
from functools import wraps
from typing import Callable
import datetime
import pytz
import json

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

def get_realtime_info():
    """Get real-time information as a JSON string that can be included in system prompts.
    
    Returns:
        str: JSON string with current date, time, and other real-time information
    """
    now = datetime.datetime.now()
    utc_now = datetime.datetime.now(pytz.UTC)
    
    # Get various time formats
    date_formats = {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": now.strftime("%Y"),
        "unix_timestamp": int(time.time()),
        "utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    
    # Format some common date notations
    common_formats = {
        "us_date": now.strftime("%m/%d/%Y"),
        "eu_date": now.strftime("%d/%m/%Y"),
        "short_date": now.strftime("%b %d, %Y"),
        "long_date": now.strftime("%B %d, %Y"),
        "time_12h": now.strftime("%I:%M %p"),
        "time_24h": now.strftime("%H:%M"),
        "day_and_date": now.strftime("%A, %B %d, %Y"),
    }
    
    # Combine all information
    realtime_info = {
        "current_datetime": date_formats,
        "formatted": common_formats,
    }
    
    return json.dumps(realtime_info, indent=2)

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

class DateTimeTool(Tool):
    def run(self):
        """Get current date and time information."""
        return get_realtime_info() 