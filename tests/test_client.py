import pytest
from deepseek_wrapper import DeepSeekClient, DeepSeekConfig
from deepseek_wrapper.errors import DeepSeekAPIError, DeepSeekAuthError
import httpx
import os
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

@pytest.fixture
def client():
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    return DeepSeekClient()

def test_generate_text_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"text": "Hello DeepSeek!"}]}
    with patch.object(client._client, "post", return_value=mock_response):
        result = client.generate_text("hi")
        assert result == "Hello DeepSeek!"

def test_generate_text_auth_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Unauthorized"}
    with patch.object(client._client, "post", return_value=mock_response):
        with pytest.raises(DeepSeekAuthError):
            client.generate_text("hi")

def test_generate_text_api_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=None, response=mock_response)
    with patch.object(client._client, "post", return_value=mock_response):
        with pytest.raises(DeepSeekAPIError):
            client.generate_text("hi")

@pytest.mark.asyncio
async def test_async_generate_text_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"text": "Async DeepSeek!"}]}
    with patch.object(client._async_client, "post", new=AsyncMock(return_value=mock_response)):
        result = await client.async_generate_text("hi")
        assert result == "Async DeepSeek!"

@pytest.mark.asyncio
async def test_async_generate_text_auth_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Unauthorized"}
    with patch.object(client._async_client, "post", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(DeepSeekAuthError):
            await client.async_generate_text("hi")

@pytest.mark.asyncio
async def test_async_generate_text_api_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=None, response=mock_response)
    with patch.object(client._async_client, "post", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(DeepSeekAPIError):
            await client.async_generate_text("hi")

def test_chat_completion_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"message": {"content": "Chat reply!"}}]}
    with patch.object(client._client, "post", return_value=mock_response):
        result = client.chat_completion([{"role": "user", "content": "hi"}])
        assert result == "Chat reply!"

def test_chat_completion_auth_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Unauthorized"}
    with patch.object(client._client, "post", return_value=mock_response):
        with pytest.raises(DeepSeekAuthError):
            client.chat_completion([{"role": "user", "content": "hi"}])

def test_chat_completion_api_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=None, response=mock_response)
    with patch.object(client._client, "post", return_value=mock_response):
        with pytest.raises(DeepSeekAPIError):
            client.chat_completion([{"role": "user", "content": "hi"}])

@pytest.mark.asyncio
async def test_async_chat_completion_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"message": {"content": "Async chat!"}}]}
    with patch.object(client._async_client, "post", new=AsyncMock(return_value=mock_response)):
        result = await client.async_chat_completion([{"role": "user", "content": "hi"}])
        assert result == "Async chat!"

@pytest.mark.asyncio
async def test_async_chat_completion_auth_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Unauthorized"}
    with patch.object(client._async_client, "post", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(DeepSeekAuthError):
            await client.async_chat_completion([{"role": "user", "content": "hi"}])

@pytest.mark.asyncio
async def test_async_chat_completion_api_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=None, response=mock_response)
    with patch.object(client._async_client, "post", new=AsyncMock(return_value=mock_response)):
        with pytest.raises(DeepSeekAPIError):
            await client.async_chat_completion([{"role": "user", "content": "hi"}])

def test_generate_text_retries_on_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=None, response=mock_response)
    with patch.object(client._client, "post", side_effect=[mock_response, mock_response, mock_response]):
        with pytest.raises(DeepSeekAPIError):
            client.generate_text("hi") 