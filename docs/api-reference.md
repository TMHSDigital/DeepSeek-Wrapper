# API Reference

This document provides detailed information about the DeepSeek Wrapper API.

<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
<h2 style="margin-top: 0;">Table of Contents</h2>

- [Client](#client)
  - [DeepSeekClient](#deepseek-client)
  - [DeepSeekConfig](#deepseek-config)
- [Realtime Information](#realtime-information)
  - [get_realtime_info()](#get_realtime_info)
- [Tools](#tools)
  - [Tool Registry](#tool-registry)
  - [Built-in Tools](#built-in-tools)
  - [Using Tools](#using-tools)
  - [Creating Custom Tools](#creating-custom-tools)
- [Error Handling](#error-handling)
  - [DeepSeekAPIError](#deepseekapierror)
  - [DeepSeekAuthError](#deepseekautherror)
</div>

## Client

### DeepSeek Client

The main client for interacting with the DeepSeek API.

```python
from deepseek_wrapper import DeepSeekClient

# Create a client with default config (from environment variables)
client = DeepSeekClient()

# Or with custom configuration
from deepseek_wrapper import DeepSeekConfig
config = DeepSeekConfig(
    api_key="your-api-key",
    base_url="https://api.deepseek.com/v1",
    timeout=30
)
client = DeepSeekClient(config)
```

#### Methods

- **generate_text**(prompt: str, **kwargs) -> str
  
  Generate text completion for a prompt.
  
  ```python
  result = client.generate_text("Hello, world!", max_tokens=100)
  ```

- **async_generate_text**(prompt: str, **kwargs) -> str
  
  Asynchronously generate text completion.
  
  ```python
  result = await client.async_generate_text("Hello, world!", max_tokens=100)
  ```

- **chat_completion**(messages: List[Dict[str, str]], **kwargs) -> str
  
  Get a response for a chat conversation.
  
  ```python
  messages = [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, who are you?"}
  ]
  response = client.chat_completion(messages)
  ```

- **async_chat_completion**(messages: List[Dict[str, str]], **kwargs) -> str
  
  Asynchronously get a response for a chat conversation.
  
  ```python
  response = await client.async_chat_completion(messages)
  ```

- **async_chat_completion_stream**(messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]
  
  Stream a chat response.
  
  ```python
  async for chunk in client.async_chat_completion_stream(messages):
      print(chunk, end="", flush=True)
  ```

- **chat_completion_with_tools**(messages, tools=None, tool_choice="auto", max_tools_to_use=3, **kwargs)
  
  Get a chat completion with tool use capability.
  
  ```python
  # Register tools with the client
  client.register_tool(DateTimeTool())
  client.register_tool(WeatherTool())
  
  # Or pass them directly to the function
  from deepseek_wrapper import DateTimeTool, CalculatorTool
  response, tool_usage = client.chat_completion_with_tools(
      messages,
      tools=[DateTimeTool(), CalculatorTool()],
      tool_choice="auto"
  )
  ```

- **async_chat_completion_with_tools**(messages, tools=None, tool_choice="auto", max_tools_to_use=3, **kwargs)
  
  Asynchronously get a chat completion with tool use capability.
  
  ```python
  response, tool_usage = await client.async_chat_completion_with_tools(messages, tools=[WeatherTool()])
  ```

- **register_tool**(tool)
  
  Register a tool with the client.
  
  ```python
  from deepseek_wrapper import DateTimeTool
  client.register_tool(DateTimeTool())
  ```

- **unregister_tool**(tool_name)
  
  Unregister a tool by name.
  
  ```python
  client.unregister_tool("date_time")
  ```

- **list_tools**()
  
  List all registered tool names.
  
  ```python
  tool_names = client.list_tools()
  ```

### DeepSeek Config

Configuration for the DeepSeek client.

```python
from deepseek_wrapper import DeepSeekConfig

config = DeepSeekConfig(
    api_key="your-api-key",  # Defaults to os.environ.get("DEEPSEEK_API_KEY")
    base_url="https://api.deepseek.com/v1",  # API base URL
    timeout=30.0  # Request timeout in seconds
)
```

## Realtime Information

### get_realtime_info()

Get real-time date and time information in various formats.

```python
from deepseek_wrapper.utils import get_realtime_info

# Get real-time information as JSON string
realtime_info = get_realtime_info()
print(realtime_info)
```

Output example:

```json
{
  "current_datetime": {
    "iso": "2025-05-17T14:30:45.123456",
    "date": "2025-05-17",
    "time": "14:30:45",
    "day_of_week": "Saturday",
    "month": "May",
    "year": "2025",
    "unix_timestamp": 1747752245,
    "utc": "2025-05-17 18:30:45 UTC"
  },
  "formatted": {
    "us_date": "05/17/2025",
    "eu_date": "17/05/2025",
    "short_date": "May 17, 2025",
    "long_date": "May 17, 2025",
    "time_12h": "2:30 PM",
    "time_24h": "14:30",
    "day_and_date": "Saturday, May 17, 2025"
  }
}
```

## Tools

The DeepSeek Wrapper includes a powerful tools system that allows the AI to perform actions and access external data.

### Tool Registry

The `ToolRegistry` class manages a collection of tools that can be used by the AI.

```python
from deepseek_wrapper import ToolRegistry

# Create a registry
registry = ToolRegistry()

# Register tools
from deepseek_wrapper import DateTimeTool, WeatherTool
registry.register(DateTimeTool())
registry.register(WeatherTool())

# Run a tool
result = registry.run_tool("date_time")
print(result.content)  # Tool output
```

### Built-in Tools

The DeepSeek Wrapper comes with several built-in tools:

- **DateTimeTool** - Get current date and time information in various formats
  ```python
  from deepseek_wrapper import DateTimeTool
  tool = DateTimeTool()
  result = tool.run(timezone="America/New_York", format="full")
  ```

- **CalculatorTool** - Perform mathematical calculations
  ```python
  from deepseek_wrapper import CalculatorTool
  tool = CalculatorTool()
  result = tool.run(expression="25 * 4 + sin(0.5)")
  ```

- **WeatherTool** - Get current weather conditions or forecasts
  ```python
  from deepseek_wrapper import WeatherTool
  tool = WeatherTool()
  result = tool.run(location="New York", forecast_days=3, units="metric")
  ```

- **WebSearchTool** - Search the web for information
  ```python
  from deepseek_wrapper import WebSearchTool
  tool = WebSearchTool()
  result = tool.run(query="latest news about AI", num_results=5)
  ```

- **WolframAlphaTool** - Query Wolfram Alpha for computational knowledge
  ```python
  from deepseek_wrapper import WolframAlphaTool
  tool = WolframAlphaTool()
  result = tool.run(query="population of Germany")
  ```

### Using Tools

Tools can be used in two ways:

1. **Directly** - You call the tool methods yourself
   ```python
   from deepseek_wrapper import DateTimeTool
   tool = DateTimeTool()
   result = tool.run(timezone="Europe/London")
   print(result.content)
   ```

2. **Through the DeepSeek client** - Let the AI decide when to use tools
   ```python
   from deepseek_wrapper import DeepSeekClient, DateTimeTool, WeatherTool
   
   client = DeepSeekClient()
   client.register_tool(DateTimeTool())
   client.register_tool(WeatherTool())
   
   messages = [
       {"role": "user", "content": "What's the weather like in London today and what date is it?"}
   ]
   
   response, tool_usage = client.chat_completion_with_tools(messages)
   print(response)
   print(tool_usage)  # List of tools used and their arguments
   ```

### Creating Custom Tools

You can create custom tools by subclassing the `Tool` class:

```python
from deepseek_wrapper.tools import Tool, ToolResult
from typing import Dict

class MyCustomTool(Tool[Dict[str, str]]):
    """Example custom tool."""
    
    name = "my_custom_tool"
    description = "A custom tool that does something useful"
    parameters = {
        "param1": {
            "type": "string",
            "description": "First parameter description"
        },
        "param2": {
            "type": "integer",
            "description": "Second parameter description",
            "default": 42
        }
    }
    required_params = ["param1"]
    
    def _run(self, param1: str, param2: int = 42) -> Dict[str, str]:
        """Implement the tool's functionality."""
        # Your custom logic here
        return {
            "result": f"Processed {param1} with value {param2}",
            "status": "success"
        }

# Use your custom tool
tool = MyCustomTool()
result = tool.run(param1="test", param2=100)
print(result.content)  # Access the returned data

# Or register it with a client
client = DeepSeekClient()
client.register_tool(MyCustomTool())
```

## Error Handling

### DeepSeekAPIError

Base exception for API-related errors.

```python
from deepseek_wrapper import DeepSeekAPIError

try:
    response = client.generate_text("Hello", max_tokens=1000000)  # Too many tokens
except DeepSeekAPIError as e:
    print(f"API error: {e}")
```

### DeepSeekAuthError

Authentication-related errors (invalid or missing API key).

```python
from deepseek_wrapper import DeepSeekAuthError

try:
    client = DeepSeekClient(DeepSeekConfig(api_key="invalid-key"))
    response = client.generate_text("Hello")
except DeepSeekAuthError as e:
    print(f"Authentication error: {e}")
```

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