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

### Text Generation Endpoints

#### `POST /api/generate`

Generate text based on a prompt without conversation context.

**Request Body:**
```json
{
  "prompt": "Your prompt here",
  "max_tokens": 100,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "id": "generation-id",
  "text": "Generated text content"
}
```

#### `GET /api/generate/stream`

Stream a text generation response using Server-Sent Events (SSE).

**Query Parameters:**
- `prompt` (string): The generation prompt
- `max_tokens` (integer, optional): Maximum tokens to generate
- `temperature` (float, optional): Temperature for generation

**Response:**
Server-sent events with the same format as the chat stream endpoint.

### Embedding Endpoints

#### `POST /api/embeddings`

Generate embeddings for input text.

**Request Body:**
```json
{
  "input": "Text to generate embeddings for"
}
```

**Response:**
```json
{
  "embedding": [0.123, 0.456, ...], // Vector of floating-point values
  "dimensions": 1536 // Number of dimensions in the embedding vector
}
```

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

### Webhook Endpoints

#### `POST /api/webhooks/register`

Register a webhook to receive notifications.

**Request Body:**
```json
{
  "url": "https://your-webhook-endpoint.com",
  "events": ["completion.finished", "error"],
  "description": "Optional description of this webhook"
}
```

**Response:**
```json
{
  "id": "webhook-id",
  "url": "https://your-webhook-endpoint.com",
  "events": ["completion.finished", "error"],
  "created_at": "2023-06-15T14:30:00Z"
}
```

#### `GET /api/webhooks`

List all registered webhooks.

**Response:** Array of webhook objects.

#### `DELETE /api/webhooks/{webhook_id}`

Delete a registered webhook.

**Response:** Status 204 No Content

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

# Text generation
text = client.generate_text(
    prompt="Write a poem about artificial intelligence.",
    max_tokens=100
)
print(text)

# Generate embeddings
embedding = client.get_embedding("This is a sample text for embedding")
print(f"Embedding dimensions: {len(embedding)}")

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

#### `generate_text(prompt, **kwargs)`

Generate text based on a prompt.

**Parameters:**
- `prompt` (str): The text prompt
- `max_tokens` (int, optional): Maximum number of tokens to generate
- `temperature` (float, optional): Controls randomness (0-1.0)
- `top_p` (float, optional): Nucleus sampling parameter
- `**kwargs`: Additional parameters to pass to the API

**Returns:** String containing the generated text

#### `async_generate_text(prompt, **kwargs)`

Asynchronous version of `generate_text`.

**Parameters:** Same as `generate_text`
**Returns:** Coroutine that resolves to a string containing the generated text

#### `generate_text_stream(prompt, **kwargs)`

Stream text generation.

**Parameters:** Same as `generate_text`
**Returns:** Generator yielding text chunks

#### `async_generate_text_stream(prompt, **kwargs)`

Asynchronous version of `generate_text_stream`.

**Parameters:** Same as `generate_text`
**Returns:** Async generator yielding text chunks

#### `get_embedding(text, **kwargs)`

Generate embeddings for the input text.

**Parameters:**
- `text` (str): Input text to embed
- `model` (str, optional): Embedding model to use
- `**kwargs`: Additional parameters to pass to the API

**Returns:** List of floats representing the embedding vector

#### `clean_up()`

Clean up resources used by the client, including closing the HTTP session.

## Model Configuration

The DeepSeek Wrapper supports the following model configuration parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | "deepseek-chat" | The DeepSeek model to use |
| `temperature` | float | 0.7 | Controls randomness in generation (0-1.0) |
| `max_tokens` | integer | 1024 | Maximum number of tokens to generate |
| `top_p` | float | 0.95 | Nucleus sampling parameter (0-1.0) |
| `top_k` | integer | 50 | Limits vocabulary to top K options |
| `presence_penalty` | float | 0.0 | Penalizes repeated tokens (-2.0 to 2.0) |
| `frequency_penalty` | float | 0.0 | Penalizes frequent tokens (-2.0 to 2.0) |
| `stop` | array | [] | Sequences where the API will stop generating |
| `stream` | boolean | false | Whether to stream the response |
| `timeout` | integer | 30 | Client timeout in seconds |
| `max_retries` | integer | 3 | Maximum number of retries on failure |

## Utility Functions

The DeepSeek Wrapper includes several utility functions to enhance functionality:

### Real-Time Information

#### `get_realtime_info()`

Get current date and time information in JSON format for use in prompts.

**Returns:** JSON string with current date, time, and other real-time information.

**Example:**
```python
from deepseek_wrapper.utils import get_realtime_info

# Get real-time information as JSON
realtime_data = get_realtime_info()
print(realtime_data)

# Include in a system prompt
system_prompt = f"""You are a helpful assistant with access to real-time information.
Current date and time data:
{realtime_data}
"""
```

**Output Format:**
```json
{
  "current_datetime": {
    "iso": "2025-05-17T12:30:45.123456",
    "date": "2025-05-17",
    "time": "12:30:45",
    "day_of_week": "Saturday",
    "month": "May",
    "year": "2025",
    "unix_timestamp": 1747363845,
    "utc": "2025-05-17 17:30:45 UTC"
  },
  "formatted": {
    "us_date": "05/17/2025",
    "eu_date": "17/05/2025",
    "short_date": "May 17, 2025",
    "long_date": "May 17, 2025",
    "time_12h": "12:30 PM",
    "time_24h": "12:30",
    "day_and_date": "Saturday, May 17, 2025"
  }
}
```

### Tool Classes

#### `DateTimeTool`

A tool class that returns current date and time information.

**Example:**
```python
from deepseek_wrapper.utils import DateTimeTool

# Create and use the tool
datetime_tool = DateTimeTool()
realtime_info = datetime_tool.run()
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON body with `error` and `message` fields.

## Webhook Events

When using webhooks, you can subscribe to the following events:

| Event | Description |
|-------|-------------|
| `completion.started` | Triggered when a completion request begins processing |
| `completion.finished` | Triggered when a completion request is successfully completed |
| `embedding.created` | Triggered when embeddings are successfully generated |
| `error` | Triggered when an error occurs during processing |

Webhook payloads include an `event` field identifying the event type, and a `data` field containing event-specific information. 