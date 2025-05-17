# API Reference

This document provides details about the DeepSeek Wrapper API for developers who want to integrate or extend the functionality.

## REST API Endpoints

The DeepSeek Wrapper provides a FastAPI-based REST API with the following endpoints:

### Chat Endpoints

#### `POST /api/chat`

Create a new chat message and get a response from the DeepSeek AI.

**Request Body:**
```json
{
  "message": "Your message here",
  "conversation_id": "optional-conversation-id",
  "system_prompt": "Optional system prompt to guide the AI's behavior"
}
```

**Response:**
```json
{
  "id": "response-id",
  "content": "AI response content",
  "conversation_id": "conversation-id"
}
```

#### `GET /api/chat/stream`

Stream a chat response using Server-Sent Events (SSE).

**Query Parameters:**
- `message` (string): The user's message
- `conversation_id` (string, optional): Conversation identifier
- `system_prompt` (string, optional): System prompt

**Response:**
Server-sent events with the following data format:
```json
{
  "id": "chunk-id",
  "content": "Partial content chunk",
  "is_complete": false
}
```

Final chunk will have `is_complete` set to `true`.

### Conversation Endpoints

#### `GET /api/conversations`

Get a list of all conversations.

**Response:**
```json
[
  {
    "id": "conversation-id",
    "title": "Conversation title",
    "created_at": "2023-06-15T14:30:00Z",
    "updated_at": "2023-06-15T14:35:00Z"
  }
]
```

#### `GET /api/conversations/{conversation_id}`

Get details and messages for a specific conversation.

**Response:**
```json
{
  "id": "conversation-id",
  "title": "Conversation title",
  "created_at": "2023-06-15T14:30:00Z",
  "updated_at": "2023-06-15T14:35:00Z",
  "messages": [
    {
      "id": "message-id",
      "role": "user",
      "content": "User message",
      "created_at": "2023-06-15T14:30:00Z"
    },
    {
      "id": "response-id",
      "role": "assistant",
      "content": "AI response",
      "created_at": "2023-06-15T14:31:00Z"
    }
  ]
}
```

#### `DELETE /api/conversations/{conversation_id}`

Delete a specific conversation.

**Response:** Status 204 No Content

### Document Endpoints

#### `POST /api/documents/upload`

Upload a document for processing.

**Request:** Multipart form data with a `file` field containing the document.

**Response:**
```json
{
  "id": "document-id",
  "filename": "document.pdf",
  "content": "Extracted text from the document",
  "content_type": "application/pdf",
  "size": 1024
}
```

## Python Client API

The DeepSeek Wrapper provides a Python client for programmatic access to the DeepSeek API.

### Basic Usage

```python
from deepseek_wrapper.client import DeepSeekClient

# Initialize the client
client = DeepSeekClient(api_key="your-api-key")

# Simple chat completion
response = client.chat_completion(
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)
print(response.content)

# Streaming response
for chunk in client.chat_completion_stream(
    messages=[
        {"role": "user", "content": "Write a short story about a robot."}
    ]
):
    print(chunk.content, end="", flush=True)
```

### Client Methods

#### `chat_completion(messages, system_prompt=None, **kwargs)`

Get a complete response for the given messages.

**Parameters:**
- `messages` (List[Dict]): List of message objects with `role` and `content`
- `system_prompt` (str, optional): System prompt to guide the AI
- `**kwargs`: Additional parameters to pass to the API

**Returns:** Response object with attributes like `id`, `content`, etc.

#### `chat_completion_stream(messages, system_prompt=None, **kwargs)`

Stream the response for the given messages.

**Parameters:**
- `messages` (List[Dict]): List of message objects with `role` and `content`
- `system_prompt` (str, optional): System prompt to guide the AI
- `**kwargs`: Additional parameters to pass to the API

**Returns:** Generator yielding response chunks

#### `clean_up()`

Clean up resources used by the client, including closing the HTTP session.

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON body with `error` and `message` fields. 