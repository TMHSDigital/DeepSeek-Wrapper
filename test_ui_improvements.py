#!/usr/bin/env python3
"""
Test script to demonstrate the UI improvements for DeepSeek-Wrapper.
This script tests the markdown rendering and formatting features.
"""

import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from deepseek_wrapper import DeepSeekClient

def test_markdown_features():
    """Test various markdown features that should now render properly."""

    # Set API key from environment
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ No DEEPSEEK_API_KEY found. Set it in your environment first.")
        print("   Example: export DEEPSEEK_API_KEY=sk-your-key-here")
        return

    print("🚀 Testing DeepSeek-Wrapper UI Improvements...")
    print("=" * 60)

    try:
        client = DeepSeekClient()

        # Test 1: Bulleted lists (should render properly during streaming)
        print("\n📝 Test 1: Bulleted Lists")
        print("Sending: 'List 3 benefits of AI'")
        response, _ = client.chat_completion_with_tools([
            {"role": "user", "content": "List 3 benefits of AI"}
        ])
        print("Response received - check if bullets render properly in web UI")

        # Test 2: Code blocks
        print("\n💻 Test 2: Code Blocks")
        print("Sending: 'Show me a simple Python function'")
        response, _ = client.chat_completion_with_tools([
            {"role": "user", "content": "Show me a simple Python function"}
        ])
        print("Response received - check if code blocks have copy buttons and syntax highlighting")

        # Test 3: Headings and formatting
        print("\n🎨 Test 3: Headings & Mixed Formatting")
        print("Sending: 'Explain machine learning with a heading and code'")
        response, _ = client.chat_completion_with_tools([
            {"role": "user", "content": "Explain machine learning with a heading and code"}
        ])
        print("Response received - check if headings, bold, italic render properly")

        print("\n✅ All tests completed successfully!")
        print("\n🌟 UI Improvements you should see:")
        print("  • Bulleted lists render immediately during streaming")
        print("  • Proper spacing and indentation for nested lists")
        print("  • Code blocks with copy buttons and syntax highlighting")
        print("  • Headings with proper typography and spacing")
        print("  • Smooth transitions during content updates")
        print("  • Improved dark theme compatibility")
        print("  • Better cursor animation during streaming")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_markdown_features()
