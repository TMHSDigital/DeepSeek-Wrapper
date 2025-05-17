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

## Features

<div style="display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0;">
  <div style="flex: 1; min-width: 250px; border-left: 4px solid #4A90E2; padding: 10px; background: #F5F9FF; margin: 5px 0;">
    <h3 style="color: #4A90E2; margin-top: 0;">Modern API</h3>
    <ul>
      <li><b>Sync & async support</b></li>
      <li><b>Type hints throughout</b></li>
      <li><b>Clean error handling</b></li>
    </ul>
  </div>
  
  <div style="flex: 1; min-width: 250px; border-left: 4px solid #50C878; padding: 10px; background: #F5FFF7; margin: 5px 0;">
    <h3 style="color: #50C878; margin-top: 0;">Advanced Web UI</h3>
    <ul>
      <li><b>Session-based chat history</b></li>
      <li><b>Markdown rendering</b></li>
      <li><b>File uploads & processing</b></li>
    </ul>
  </div>
  
  <div style="flex: 1; min-width: 250px; border-left: 4px solid #FF6B6B; padding: 10px; background: #FFF5F5; margin: 5px 0;">
    <h3 style="color: #FF6B6B; margin-top: 0;">Production Ready</h3>
    <ul>
      <li><b>Automatic retries with backoff</b></li>
      <li><b>100% test coverage</b></li>
      <li><b>Environment variable config</b></li>
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

For a complete API reference and advanced usage, see the [API Reference](docs/api-reference.md).

## Configuration
- Set `DEEPSEEK_API_KEY` in your `.env` or environment
- Optionally set `DEEPSEEK_BASE_URL`, `timeout`, `max_retries`
- See `.env.example`

**Default model:** `deepseek-chat` (per DeepSeek docs)

For deployment options and environment configurations, see the [Deployment Guide](docs/deployment.md).

## API Reference
- `DeepSeekClient.generate_text(prompt, **kwargs)` → str
- `DeepSeekClient.async_generate_text(prompt, **kwargs)` → str
- `DeepSeekClient.chat_completion(messages, **kwargs)` → str
- `DeepSeekClient.async_chat_completion(messages, **kwargs)` → str

All methods accept extra keyword args for model parameters (e.g., `temperature`, `top_p`, etc).

## Testing

```bash
pytest --cov=src/deepseek_wrapper
```

## Contributing
- See [CONTRIBUTING.md](docs/CONTRIBUTING.md)
- Run `pre-commit install` to enable hooks

## Links
- [DeepSeek API Docs](https://platform.deepseek.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [GitHub Repo](https://github.com/TMHSDigital/DeepSeek-Wrapper)

## License
This project is licensed under the [Apache 2.0 License](docs/LICENSE).
