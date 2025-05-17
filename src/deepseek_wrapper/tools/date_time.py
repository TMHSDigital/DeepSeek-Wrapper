import datetime
import time
import json
import pytz
from typing import Dict, Any, Optional, List

from .base import Tool, ToolResult

class DateTimeTool(Tool[str]):
    """Tool for retrieving current date and time information."""
    
    name = "date_time"
    description = "Get current date and time information in various formats"
    parameters = {
        "timezone": {
            "type": "string",
            "description": "Optional timezone name (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo'). Defaults to local timezone if not specified.",
            "default": "local"
        },
        "format": {
            "type": "string",
            "description": "Optional format specifier ('iso', 'full', 'date_only', 'time_only', etc.). Defaults to 'full' which returns all formats.",
            "enum": ["iso", "full", "date_only", "time_only", "unix"],
            "default": "full"
        }
    }
    
    def _run(self, timezone: str = "local", format: str = "full") -> str:
        """Get current date and time information.
        
        Args:
            timezone: Timezone name (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')
                     or 'local' for the system's local timezone
            format: Format specifier ('iso', 'full', 'date_only', 'time_only', 'unix')
        
        Returns:
            JSON string containing date and time information
        """
        # Get the datetime in the requested timezone
        if timezone == "local":
            now = datetime.datetime.now()
            tz_now = now
        else:
            try:
                tz = pytz.timezone(timezone)
                utc_now = datetime.datetime.now(pytz.UTC)
                tz_now = utc_now.astimezone(tz)
            except pytz.exceptions.UnknownTimeZoneError:
                return ToolResult.error_result(f"Unknown timezone: {timezone}").to_json()
        
        # Get UTC time for reference
        utc_now = datetime.datetime.now(pytz.UTC)
        
        # Format the response based on the requested format
        if format == "iso":
            return json.dumps({
                "iso": tz_now.isoformat(),
                "timezone": timezone if timezone != "local" else str(datetime.datetime.now().astimezone().tzinfo)
            })
        
        elif format == "date_only":
            return json.dumps({
                "date": tz_now.strftime("%Y-%m-%d"),
                "day_of_week": tz_now.strftime("%A"),
                "month": tz_now.strftime("%B"),
                "year": tz_now.strftime("%Y"),
                "us_date": tz_now.strftime("%m/%d/%Y"),
                "eu_date": tz_now.strftime("%d/%m/%Y")
            })
        
        elif format == "time_only":
            return json.dumps({
                "time": tz_now.strftime("%H:%M:%S"),
                "time_12h": tz_now.strftime("%I:%M:%S %p"),
                "time_24h": tz_now.strftime("%H:%M:%S")
            })
        
        elif format == "unix":
            return json.dumps({
                "unix_timestamp": int(time.time())
            })
        
        else:  # "full" or default
            # Get various time formats
            date_formats = {
                "iso": tz_now.isoformat(),
                "date": tz_now.strftime("%Y-%m-%d"),
                "time": tz_now.strftime("%H:%M:%S"),
                "day_of_week": tz_now.strftime("%A"),
                "month": tz_now.strftime("%B"),
                "year": tz_now.strftime("%Y"),
                "unix_timestamp": int(time.time()),
                "timezone": timezone if timezone != "local" else str(datetime.datetime.now().astimezone().tzinfo),
                "utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            
            # Format some common date notations
            common_formats = {
                "us_date": tz_now.strftime("%m/%d/%Y"),
                "eu_date": tz_now.strftime("%d/%m/%Y"),
                "short_date": tz_now.strftime("%b %d, %Y"),
                "long_date": tz_now.strftime("%B %d, %Y"),
                "time_12h": tz_now.strftime("%I:%M %p"),
                "time_24h": tz_now.strftime("%H:%M"),
                "day_and_date": tz_now.strftime("%A, %B %d, %Y"),
            }
            
            # Combine all information
            realtime_info = {
                "current_datetime": date_formats,
                "formatted": common_formats,
            }
            
            return json.dumps(realtime_info, indent=2) 