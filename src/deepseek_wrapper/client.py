from typing import AsyncGenerator, Dict, List, Optional, Union, Any
from .config import DeepSeekConfig
from .errors import DeepSeekAPIError, DeepSeekAuthError
from .utils import retry
import httpx
import json
import logging

logger = logging.getLogger(__name__)

class DeepSeekClient:
    """Client for interacting with DeepSeek LLM API."""
    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.config = config or DeepSeekConfig()
        self._client = httpx.Client(timeout=self.config.timeout)
        self._async_client = httpx.AsyncClient(timeout=self.config.timeout)
        self._headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def __del__(self):
        """Cleanup resources when the client is garbage collected."""
        self.close()

    def close(self):
        """Close the synchronous client."""
        if hasattr(self, '_client') and self._client:
            self._client.close()

    async def aclose(self):
        """Close the asynchronous client."""
        if hasattr(self, '_async_client') and self._async_client:
            await self._async_client.aclose()

    def _update_headers(self):
        """Update headers if API key changes."""
        self._headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    @retry()
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Synchronously generate text from DeepSeek."""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 256),
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens")},
        }
        url = f"{self.config.base_url}/completions"
        try:
            resp = self._client.post(url, json=payload, headers=self._headers)
            if resp.status_code == 401:
                raise DeepSeekAuthError("Invalid or missing API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["text"] if "choices" in data else data
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e

    @retry()
    async def async_generate_text(self, prompt: str, **kwargs) -> str:
        """Asynchronously generate text from DeepSeek."""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 256),
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens")},
        }
        url = f"{self.config.base_url}/completions"
        try:
            resp = await self._async_client.post(url, json=payload, headers=self._headers)
            if resp.status_code == 401:
                raise DeepSeekAuthError("Invalid or missing API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["text"] if "choices" in data else data
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e

    @retry()
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Synchronously get chat completion from DeepSeek."""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 256),
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens")},
        }
        url = f"{self.config.base_url}/chat/completions"
        try:
            resp = self._client.post(url, json=payload, headers=self._headers)
            if resp.status_code == 401:
                raise DeepSeekAuthError("Invalid or missing API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"] if "choices" in data else data
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e

    @retry()
    async def async_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Asynchronously get chat completion from DeepSeek."""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 256),
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens")},
        }
        url = f"{self.config.base_url}/chat/completions"
        try:
            resp = await self._async_client.post(url, json=payload, headers=self._headers)
            if resp.status_code == 401:
                raise DeepSeekAuthError("Invalid or missing API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"] if "choices" in data else data
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e

    @retry()
    async def async_chat_completion_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion from DeepSeek.
        
        Returns:
            AsyncGenerator that yields content chunks as they arrive.
        """
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 256),
            "stream": True,  # Enable streaming
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens", "stream")},
        }
        url = f"{self.config.base_url}/chat/completions"
        logger.debug(f"Streaming request to DeepSeek API: URL={url}, payload={json.dumps(payload, indent=2)}")
        try:
            async with self._async_client.stream('POST', url, json=payload, headers=self._headers) as resp:
                if resp.status_code == 401:
                    raise DeepSeekAuthError("Invalid or missing API key.")
                logger.debug(f"DeepSeek API response status: {resp.status_code}")
                logger.debug(f"DeepSeek API response headers: {resp.headers}")
                resp.raise_for_status()
                buffer = ""
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            return
                        try:
                            chunk_data = json.loads(data)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content')
                                if content:
                                    yield content
                        except Exception as e:
                            logger.error(f"Error processing chunk: {e}")
                            continue
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e 