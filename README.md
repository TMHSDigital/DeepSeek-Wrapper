# DeepSeek Wrapper

[![Tests](https://github.com/TMHSDigital/DeepSeek-Wrapper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/TMHSDigital/DeepSeek-Wrapper/actions)
[![Coverage Status](https://img.shields.io/badge/coverage-94%25-brightgreen)](https://github.com/TMHSDigital/DeepSeek-Wrapper)
[![License](https://img.shields.io/github/license/TMHSDigital/DeepSeek-Wrapper)](LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/requests.svg)](https://www.python.org/downloads/)
[![Last Commit](https://img.shields.io/github/last-commit/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/commits/main)
[![Issues](https://img.shields.io/github/issues/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/pulls)
[![GitHub stars](https://img.shields.io/github/stars/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/TMHSDigital/DeepSeek-Wrapper)](https://github.com/TMHSDigital/DeepSeek-Wrapper/network)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)

A modern, async/sync Python client for the DeepSeek LLM API. Supports completions, chat, retries, and robust error handling. Built for local dev, CI, and production.

## Features
- Sync & async API
- Text generation & chat completion
- Automatic retries with exponential backoff
- Type hints throughout
- .env and environment variable config
- 100% test coverage with pytest & mocks
- Pre-commit hooks and CI ready

## Installation

```bash
pip install -r requirements.txt
pip install -e .  # for local development
```

## Usage

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

## Configuration
- Set `DEEPSEEK_API_KEY` in your `.env` or environment
- Optionally set `DEEPSEEK_BASE_URL`, `timeout`, `max_retries`
- See `.env.example`

**Default model:** `deepseek-chat` (per DeepSeek docs)

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
- See `CONTRIBUTING.md`
- Run `pre-commit install` to enable hooks

## Links
- [DeepSeek API Docs](https://platform.deepseek.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [GitHub Repo](https://github.com/TMHSDigital/DeepSeek-Wrapper)

## License
Apache 2.0
