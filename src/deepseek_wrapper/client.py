from typing import Any, Dict, Optional, Union
from .config import DeepSeekConfig
from .errors import DeepSeekAPIError, DeepSeekAuthError
from .utils import retry
import httpx

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
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}")
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e))

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
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}")
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e))

    @retry()
    def chat_completion(self, messages: list, **kwargs) -> str:
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
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}")
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e))

    @retry()
    async def async_chat_completion(self, messages: list, **kwargs) -> str:
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
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}")
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) 