#!/usr/bin/env python3
"""
Example script demonstrating function calling capabilities with DeepSeek Wrapper.
"""Example: Using tools with DeepSeekClient.

Run from repository root after installing deps:
    python -m src.deepseek_wrapper.examples.tool_usage
"""
This script shows how to:
1. Register and use tools with the DeepSeek client
2. Create a conversation that can leverage tools
3. Handle tool calling results
"""

import os
import sys
import logging
import json
from typing import List, Dict, Any
import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from deepseek_wrapper import (
    DeepSeekClient,
    DateTimeTool,
    WeatherTool,
    CalculatorTool,
    WebSearchTool,
    WolframAlphaTool
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tool_usage.log")
    ]
)
logger = logging.getLogger(__name__)

def format_tool_result(result: Any) -> str:
    """Format a tool result for display."""
    if result is None:
        return "None"
    elif isinstance(result, dict) or isinstance(result, list):
        return json.dumps(result, indent=2)
    else:
        return str(result)

def example_single_tool_usage() -> None:
    """Example of using a single tool."""
    logger.info("=== Example: Single Tool Usage ===")
    
    # Create a client and register the DateTime tool
    client = DeepSeekClient()
    client.register_tool(DateTimeTool())
    
    # Create a conversation with a user question
    messages = [
        {"role": "user", "content": "What day of the week is it today? What date would it be in 30 days?"}
    ]
    
    # Get a response with tool usage
    response, tool_usage = client.chat_completion_with_tools(messages)
    
    # Display results
    logger.info(f"Final response: {response}")
    logger.info(f"Tool usage: {json.dumps(tool_usage, indent=2)}")

def example_multiple_tools_usage() -> None:
    """Example of using multiple tools in a conversation."""
    logger.info("\n=== Example: Multiple Tools Usage ===")
    
    # Create a client and register multiple tools
    client = DeepSeekClient()
    client.register_tool(DateTimeTool())
    client.register_tool(CalculatorTool())
    client.register_tool(WeatherTool())
    
    # Create a conversation with a complex user question
    messages = [
        {"role": "user", "content": "I need to know if it's going to rain in London tomorrow. Also, what's 25 squared plus the day of the month?"}
    ]
    
    # Get a response with tool usage
    response, tool_usage = client.chat_completion_with_tools(messages)
    
    # Display results
    logger.info(f"Final response: {response}")
    logger.info(f"Tool usage: {json.dumps(tool_usage, indent=2)}")

def example_conversation_with_tools() -> None:
    """Example of a multi-turn conversation using tools."""
    logger.info("\n=== Example: Multi-turn Conversation With Tools ===")
    
    # Create a client and register tools
    client = DeepSeekClient()
    client.register_tool(DateTimeTool())
    client.register_tool(CalculatorTool())
    client.register_tool(WeatherTool())
    client.register_tool(WebSearchTool())
    
    # Create a conversation history
    conversation = [
        {"role": "system", "content": "You are a helpful assistant who can use tools to answer questions accurately."}
    ]
    
    # First user message
    user_message = "What's today's date and what were the high and low temperatures in New York today?"
    logger.info(f"User: {user_message}")
    conversation.append({"role": "user", "content": user_message})
    
    # Get and display the response
    response, tool_usage = client.chat_completion_with_tools(conversation)
    logger.info(f"Assistant: {response}")
    logger.info(f"Tool usage: {json.dumps(tool_usage, indent=2)}")
    
    # Add the response to the conversation
    conversation.append({"role": "assistant", "content": response})
    
    # Second user message
    user_message = "Can you calculate how many days are left until Christmas?"
    logger.info(f"User: {user_message}")
    conversation.append({"role": "user", "content": user_message})
    
    # Get and display the response
    response, tool_usage = client.chat_completion_with_tools(conversation)
    logger.info(f"Assistant: {response}")
    logger.info(f"Tool usage: {json.dumps(tool_usage, indent=2)}")

def example_advanced_wolfram_alpha() -> None:
    """Example of using the Wolfram Alpha tool for advanced calculations and knowledge."""
    logger.info("\n=== Example: Advanced Wolfram Alpha Tool ===")
    
    # Create a client and register the Wolfram Alpha tool
    client = DeepSeekClient()
    client.register_tool(WolframAlphaTool())
    
    # Create a conversation with complex questions
    messages = [
        {"role": "user", "content": "Can you solve the equation x^3 - 4x^2 + 6x - 24 = 0? And what's the population density of Japan compared to Canada?"}
    ]
    
    # Get a response with tool usage
    response, tool_usage = client.chat_completion_with_tools(messages)
    
    # Display results
    logger.info(f"Final response: {response}")
    logger.info(f"Tool usage: {json.dumps(tool_usage, indent=2)}")

def example_custom_tool() -> None:
    """Example of creating and using a custom tool."""
    logger.info("\n=== Example: Custom Tool ===")
    
    # Import the base Tool class
    from deepseek_wrapper.tools import Tool, ToolResult
    
    # Create a custom tool
    class CountdownTool(Tool[Dict[str, Any]]):
        """Tool for creating countdowns to specific dates."""
        
        name = "countdown"
        description = "Calculate the number of days until a specified date"
        parameters = {
            "target_date": {
                "type": "string",
                "description": "The target date in YYYY-MM-DD format"
            },
            "include_time": {
                "type": "boolean",
                "description": "Whether to include hours, minutes, and seconds in the countdown",
                "default": False
            }
        }
        required_params = ["target_date"]
        
        def _run(self, target_date: str, include_time: bool = False) -> Dict[str, Any]:
            """Calculate the countdown to the target date.
            
            Args:
                target_date: The target date in YYYY-MM-DD format
                include_time: Whether to include time components
                
            Returns:
                Dictionary with countdown information
            """
            try:
                # Parse the target date
                if include_time and len(target_date) > 10:
                    # Assuming ISO format with time
                    target = datetime.datetime.fromisoformat(target_date)
                else:
                    # Assuming YYYY-MM-DD format
                    target = datetime.datetime.strptime(target_date, "%Y-%m-%d")
                
                # Get current date/time
                now = datetime.datetime.now()
                
                # Calculate the difference
                diff = target - now
                
                # Build the result
                result = {
                    "target_date": target_date,
                    "current_date": now.strftime("%Y-%m-%d"),
                    "days_remaining": max(0, diff.days),
                    "total_seconds": max(0, diff.total_seconds()),
                    "is_future": diff.total_seconds() > 0,
                    "is_today": diff.days == 0 and not include_time
                }
                
                # Add time components if requested
                if include_time:
                    seconds = int(diff.total_seconds())
                    hours, remainder = divmod(seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    result["hours"] = hours
                    result["minutes"] = minutes
                    result["seconds"] = seconds
                    result["formatted"] = f"{diff.days} days, {hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    result["formatted"] = f"{diff.days} days"
                
                return result
                
            except ValueError as e:
                raise ValueError(f"Invalid date format: {e}")
    
    # Create a client and register the custom tool
    client = DeepSeekClient()
    client.register_tool(CountdownTool())
    client.register_tool(DateTimeTool())  # Also register DateTime tool for comparison
    
    # Create a conversation with a user question
    messages = [
        {"role": "user", "content": "How many days until Christmas 2025? And what day of the week is it today?"}
    ]
    
    # Get a response with tool usage
    response, tool_usage = client.chat_completion_with_tools(messages)
    
    # Display results
    logger.info(f"Final response: {response}")
    logger.info(f"Tool usage: {json.dumps(tool_usage, indent=2)}")

def main() -> None:
    """Run the tool usage examples."""
    # Check if API key is set
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("Warning: DEEPSEEK_API_KEY environment variable not set.")
        print("Please set it before running this script.")
        print("You can still run the script, but it will likely fail when making API calls.")
        choice = input("Do you want to continue anyway? (y/n): ")
        if choice.lower() != 'y':
            sys.exit(1)
    
    try:
        # Run examples
        example_single_tool_usage()
        example_multiple_tools_usage()
        example_conversation_with_tools()
        example_advanced_wolfram_alpha()
        example_custom_tool()
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 