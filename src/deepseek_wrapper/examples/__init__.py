"""Examples demonstrating how to use deepseek_wrapper."""
"""Examples package for DeepSeek Wrapper.

This package contains example scripts demonstrating client and tool usage.
"""
# Package exports
from .tool_usage import (
    example_single_tool_usage,
    example_multiple_tools_usage,
    example_conversation_with_tools,
    example_advanced_wolfram_alpha,
    example_custom_tool
)

__all__ = [
    "example_single_tool_usage",
    "example_multiple_tools_usage",
    "example_conversation_with_tools",
    "example_advanced_wolfram_alpha",
    "example_custom_tool"
] 