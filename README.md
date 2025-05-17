# DeepSeek Wrapper

[![CI](https://github.com/TMHSDigital/DeepSeek-Wrapper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/TMHSDigital/DeepSeek-Wrapper/actions)
[![Coverage Status](https://img.shields.io/badge/coverage-94%25-brightgreen)](https://github.com/TMHSDigital/DeepSeek-Wrapper)
[![License](https://img.shields.io/github/license/TMHSDigital/DeepSeek-Wrapper)](docs/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/requests.svg)](https://www.python.org/downloads/)

[![Issues](https://img.shields.io/github/issues/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/pulls)
[![GitHub stars](https://img.shields.io/github/stars/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/network)
[![Last Commit](https://img.shields.io/github/last-commit/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/commits/main)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)

---

<div align="center">
  <h3>A modern, async/sync Python client for the DeepSeek LLM API.</h3>
  <p>Supports completions, chat, retries, and robust error handling. Built for local dev, CI, and production.</p>
</div>

<p align="center">
  <img src="docs/images/ui-overview.png" alt="DeepSeek Wrapper UI" style="max-width: 800px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
</p>

## Documentation

<table>
  <tr>
    <td width="33%" align="center">
      <a href="docs/getting-started.md">
        <b>Getting Started</b><br>
        Quick setup guide
      </a>
    </td>
    <td width="33%" align="center">
      <a href="docs/web-ui-guide.md">
        <b>Web UI Guide</b><br>
        Guide to using the web interface
      </a>
    </td>
    <td width="33%" align="center">
      <a href="docs/features.md">
        <b>Features</b><br>
        Detailed feature list
      </a>
    </td>
  </tr>
  <tr>
    <td width="33%" align="center">
      <a href="docs/api-reference.md">
        <b>API Reference</b><br>
        API documentation for developers
      </a>
    </td>
    <td width="33%" align="center">
      <a href="docs/deployment.md">
        <b>Deployment Guide</b><br>
        Deployment options and configurations
      </a>
    </td>
    <td width="33%" align="center">
      <a href="docs/faq.md">
        <b>FAQ</b><br>
        Frequently asked questions
      </a>
    </td>
  </tr>
</table>

For DeepSeek AI model capabilities, see [DeepSeek documentation](docs/deepseek-docs.md).

## Version Progress

Below are screenshots showing the evolution of the DeepSeek Wrapper web UI and features over time:

<p align="center">
  <strong style="font-size:1.2em;">Pre-release</strong>
</p>
<p align="center">
  <img src="versions/pre-release.png" alt="Pre-release UI" style="max-width: 600px; border-radius: 8px; box-shadow: 0 2px 8px #0002;">
</p>
<p align="center" style="font-size: 0.95em; color: #666;">
  <em>Initial UI and feature set before public release.</em>
</p>

<!-- Add more screenshots here as you add new versions, e.g.:
<p align="center">
  <strong style="font-size:1.2em;">v0.2.0</strong>
</p>
<p align="center">
  <img src="versions/v0.2.0.png" alt="v0.2.0 UI" style="max-width: 600px; border-radius: 8px; box-shadow: 0 2px 8px #0002;">
</p>
<p align="center" style="font-size: 0.95em; color: #666;">
  <em>Added async endpoints and improved chat history.</em>
</p>
-->

<p align="center">
  <strong style="font-size:1.2em;">Tool Status & Caching Panel</strong>
</p>
<p align="center">
  <img src="docs/images/tool-status-panel.png" alt="Tool status and caching panel" style="max-width: 600px; border-radius: 8px; box-shadow: 0 2px 8px #0002;">
</p>
<p align="center" style="font-size: 0.95em; color: #666;">
  <em>Enhanced tool status and caching panel: see per-tool status, cache stats, and manage tool caches directly from the UI.</em>
</p>

## Features

<div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0;">
    <div style="flex: 1; min-width: 250px; border-left: 4px solid #4A90E2; padding: 10px; background: #F5F9FF; margin: 5px 0;">    <h3 style="color: #4A90E2; margin-top: 0;">Modern API</h3>    <ul>      <li><b>Sync & async support</b></li>      <li><b>Type hints throughout</b></li>      <li><b>Clean error handling</b></li>    </ul>  </div>    <div style="flex: 1; min-width: 250px; border-left: 4px solid #50C878; padding: 10px; background: #F5FFF7; margin: 5px 0;">    <h3 style="color: #50C878; margin-top: 0;">Advanced Web UI</h3>    <ul>      <li><b>Session-based chat history</b></li>      <li><b>Markdown rendering</b></li>      <li><b>File uploads & processing</b></li>    </ul>  </div>    <div style="flex: 1; min-width: 250px; border-left: 4px solid #FF9E42; padding: 10px; background: #FFF8F0; margin: 5px 0;">    <h3 style="color: #FF9E42; margin-top: 0;">Real-Time Awareness</h3>    <ul>      <li><b>Current date & time information</b></li>      <li><b>Multiple formats (ISO, US, EU)</b></li>      <li><b>No external API required</b></li>    </ul>  </div>    <div style="flex: 1; min-width: 250px; border-left: 4px solid #FF6B6B; padding: 10px; background: #FFF5F5; margin: 5px 0;">    <h3 style="color: #FF6B6B; margin-top: 0;">Production Ready</h3>    <ul>      <li><b>Automatic retries with backoff</b></li>      <li><b>100% test coverage</b></li>      <li><b>Environment variable config</b></li>    </ul>  </div>
    <div style="flex: 1; min-width: 250px; border-left: 4px solid #9D56F7; padding: 10px; background: #F9F0FF; margin: 5px 0;">
      <h3 style="color: #9D56F7; margin-top: 0;">Function Calling</h3>
      <ul>
        <li><b>Tool integration framework</b></li>
        <li><b>Built-in tools (Weather, Calculator)</b></li>
        <li><b>Custom tool creation system</b></li>
        <li><b>Tool status dashboard: visualize tool health, API key status, and cache performance in real time</b></li>
      </ul>
    </div>
    <div style="flex: 1; min-width: 250px; border-left: 4px solid #2EC4B6; padding: 10px; background: #F0FFFC; margin: 5px 0;">
      <h3 style="color: #2EC4B6; margin-top: 0;">API Key Management</h3>
      <ul>
        <li><b>Integrated settings panel</b></li>
        <li><b>Secure API key storage in .env</b></li>
        <li><b>Tool configuration UI</b></li>
      </ul>
    </div>
</div>

## Web UI (FastAPI)

A modern, session-based chat interface for DeepSeek, built with FastAPI and Jinja2.

**To run locally:**
```bash
uvicorn src.deepseek_wrapper.web:app --reload
```
Then open [http://localhost:8000](http://localhost:8000) in your browser.

**Web UI Features:**
- Chat with DeepSeek LLM (session-based history)
- Async backend for fast, non-blocking responses
- Reset conversation button
- Timestamps, avatars, and chat bubbles
- **Markdown rendering in assistant responses**
- Loading indicator while waiting for LLM
- Error banner for API issues
- **Tool configuration in settings panel with API key management**

For a comprehensive guide to using the web interface, see the [Web UI Guide](docs/web-ui-guide.md).

## Installation

```bash
pip install -r requirements.txt
pip install -e .  # for local development
```

For detailed installation instructions, see the [Getting Started Guide](docs/getting-started.md).

## Usage (Python)

```python
from deepseek_wrapper import DeepSeekClient
client = DeepSeekClient()
result = client.generate_text("Hello world!", max_tokens=32)
print(result)

# Async usage
import asyncio
async def main():
    result = await client.async_generate_text("Hello async world!", max_tokens=32)
    print(result)
# asyncio.run(main())
```

### Real-Time Date Awareness

```python
from deepseek_wrapper import DeepSeekClient
from deepseek_wrapper.utils import get_realtime_info

# Get real-time date information as JSON
realtime_data = get_realtime_info()
print(realtime_data)  # Prints current date in multiple formats

# Create a client with real-time awareness
client = DeepSeekClient()

# Use in a system prompt
system_prompt = f"""You are a helpful assistant with real-time awareness.
Current date and time information:
{realtime_data}
"""

# Send a message with the real-time-aware system prompt
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "What's today's date?"}
]

response = client.chat_completion(messages)
print(response)  # Will include the current date
```

### Function Calling with Tools

```python
from deepseek_wrapper import DeepSeekClient, DateTimeTool, WeatherTool, CalculatorTool

# Create a client and register tools
client = DeepSeekClient()
client.register_tool(DateTimeTool())
client.register_tool(WeatherTool())
client.register_tool(CalculatorTool())

# Create a conversation
messages = [
    {"role": "user", "content": "What's the weather in London today? Also, what's the square root of 144?"}
]

# Get a response with tool usage
response, tool_usage = client.chat_completion_with_tools(messages)

# Print the final response
print(response)

# See which tools were used
for tool in tool_usage:
    print(f"Used {tool['tool']} with args: {tool['arguments']}")
```

For a complete API reference and advanced usage, see the [API Reference](docs/api-reference.md).

## Configuration
- Set `DEEPSEEK_API_KEY` in your `.env` or environment
- Optionally set `DEEPSEEK_BASE_URL`, `timeout`, `max_retries`
- See `.env.example`

**Default model:** `deepseek-chat` (per DeepSeek docs)

For deployment options and environment configurations, see the [Deployment Guide](docs/deployment.md).

## API Reference
All methods accept extra keyword args for model parameters (e.g., `temperature`, `top_p`, etc).

## Testing

```bash
pytest --cov=src/deepseek_wrapper
```

## Contributing

- Run `pre-commit install` to enable hooks

## Links
- [DeepSeek API Docs](https://platform.deepseek.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [GitHub Repo](https://github.com/TMHSDigital/DeepSeek-Wrapper)

## License
## Contributing
