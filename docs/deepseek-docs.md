# DeepSeek LLM API Documentation

DeepSeek provides an API that is compatible with the OpenAI format, making it relatively easy to integrate for developers already familiar with OpenAI's services. This documentation provides a comprehensive overview of the DeepSeek API, including its endpoints, authentication methods, request formats, supported models, error codes, and example implementations.

## Authentication

DeepSeek API uses API key authentication, similar to many other API services.

### Obtaining an API Key

To use the DeepSeek API, you need to:

1. Create or log in to your DeepSeek account
2. Navigate to the API keys page
3. Select "Create new secret key" (you can optionally name your key)
4. Copy the generated API key for use in your applications[4]

### Authentication Method

Authentication is performed by including your API key in the request header:

```
Authorization: Bearer 
```

This header must be included with every API request[1].

## API Endpoints

### Base URL

The DeepSeek API can be accessed through the following base URL:

```
https://api.deepseek.com
```

For OpenAI compatibility, you can also use:

```
https://api.deepseek.com/v1
```

Note that the "v1" in this URL has no relationship with the model's version[1].

### Chat Completions

**Endpoint:** `/chat/completions`
**Method:** POST
**URL:** `https://api.deepseek.com/chat/completions`

This endpoint creates a model response for the given chat conversation[2].

## Supported Models

DeepSeek currently offers the following models through their API:

1. **deepseek-chat**: The general-purpose chat model, which has been upgraded to DeepSeek-V3. To invoke this model, specify `model='deepseek-chat'`[1].

2. **deepseek-reasoner**: The latest reasoning model, DeepSeek-R1, which is specialized for complex reasoning tasks. To invoke this model, specify `model='deepseek-reasoner'`[1][6].

## Request Format

### Chat Completion Request

```json
{
  "model": "deepseek-chat",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}
```

### Required Fields

- **model** (string): Specifies which model to use (e.g., "deepseek-chat", "deepseek-reasoner")[1]
- **messages** (array): A list of messages comprising the conversation, with at least one message required[2]

### Message Object

Each message in the "messages" array must include:

- **role** (string): The role of the message author. Possible values:
  - "system": For system instructions
  - "user": For user messages
  - "assistant": For assistant responses
  - "tool": For tool messages/responses
- **content** (string): The content of the message[2]

### Optional Fields

- **name** (string): An optional name for the participant to differentiate between participants of the same role[2]
- **stream** (boolean): When set to true, provides a stream of responses; when false, returns the complete response[1]
- **prefix** (boolean, Beta): When set to true for assistant messages, forces the model to start its answer with the supplied prefix content. Requires setting `base_url="https://api.deepseek.com/beta"`[2]
- **reasoning_content** (string, Beta): Used for the `deepseek-reasoner` model in the Chat Prefix Completion feature. When using this feature, the `prefix` parameter must be set to `true`[2]
- **stop** (array): Specifies sequences where the API will stop generating further tokens[3]

## Response Format

The response format follows a structure similar to OpenAI's API responses. When using the OpenAI SDK to interact with DeepSeek API, the response can be processed in the same way as OpenAI responses.

For non-streaming responses, the response includes the generated content accessible through the response object[1].

## Error Codes

When calling the DeepSeek API, you may encounter the following error codes:

| CODE | DESCRIPTION | CAUSE | SOLUTION |
|------|-------------|-------|----------|
| 400 - Invalid Format | Invalid request body format | The request body doesn't follow the required format | Modify your request body according to the error message hints[5] |
| 401 - Authentication Fails | Authentication failure | Wrong API key provided | Check your API key or create a new one[5] |
| 402 - Insufficient Balance | Account balance depleted | You have run out of balance | Check your account balance and add funds if necessary[5] |
| 422 - Invalid Parameters | Request contains invalid parameters | The request parameters don't meet the requirements | Adjust your request parameters according to the error message[5] |
| 429 - Rate Limit Reached | Too many requests in a short time | Sending requests too quickly | Pace your requests reasonably or temporarily switch to alternative LLM service providers[5] |
| 500 - Server Error | Server-side issue | Internal server problem | Retry after a brief wait; contact support if the issue persists[5] |
| 503 - Server Overloaded | High traffic causing server overload | Too many concurrent requests to the server | Retry after a brief wait[5] |

## Beta Features

### Chat Prefix Completion

This feature allows users to provide an assistant's prefix message that the model will complete. To use Chat Prefix Completion:

1. Ensure the last message in the `messages` array has a `role` of `assistant`
2. Set the `prefix` parameter of the last message to `True`
3. Set the base URL to `https://api.deepseek.com/beta`

Example Python code:

```python
from openai import OpenAI

client = OpenAI(
  api_key="",
  base_url="https://api.deepseek.com/beta",
)

messages = [
  {"role": "user", "content": "Please write quick sort code"},
  {"role": "assistant", "content": "```
]

response = client.chat.completions.create(
  model="deepseek-chat",
  messages=messages,
  stop=["```"],
)

print(response.choices[0].message.content)
```

This example forces the model to output Python code by setting the prefix to the start of a Python code block and using the `stop` parameter to prevent additional explanations[3].

## Example API Requests

### Curl Example

```bash
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer " \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "stream": false
  }'
```

### Python Example (using OpenAI SDK)

```python
# Install OpenAI SDK first: pip install openai
from openai import OpenAI

client = OpenAI(api_key="", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
  model="deepseek-chat",
  messages=[
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"},
  ],
  stream=False
)

print(response.choices[0].message.content)
```

### Node.js Example (using OpenAI SDK)

```javascript
// Install OpenAI SDK first: npm install openai
import OpenAI from "openai";

const openai = new OpenAI({
  baseURL: 'https://api.deepseek.com',
  apiKey: ''
});

async function main() {
  const completion = await openai.chat.completions.create({
    model: "deepseek-chat",
    messages: [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "Hello"},
    ],
    stream: false
  });
  
  console.log(completion.choices[0].message.content);
}

main();
```

## Differences from OpenAI API

The DeepSeek API is designed to be compatible with the OpenAI API format, allowing developers to use the OpenAI SDK or software compatible with the OpenAI API to access DeepSeek services with minimal changes[1]. Key differences include:

1. **Base URL**: You need to set the base URL to `https://api.deepseek.com` or `https://api.deepseek.com/v1`[1]
2. **Available Models**: DeepSeek provides its own models (`deepseek-chat` and `deepseek-reasoner`) rather than OpenAI's models[1]
3. **Feature Support**: Currently, DeepSeek does not support Embedding or Function Calling features, although these are in their development plans[8]
4. **Pricing**: DeepSeek has a different pricing structure, typically offering more competitive rates. For example, DeepSeek R1 offers free access for up to 50 daily messages, and its API pricing is generally lower than OpenAI's[7]

## Limitations and Upcoming Features

According to the available information:

1. **No Embedding Support**: DeepSeek does not currently support embeddings of content, which limits certain RAG (Retrieval-Augmented Generation) implementation possibilities[8]
2. **No Function Calling**: Unlike OpenAI, the DeepSeek API does not currently support function calling capabilities[8]
3. **Beta Features**: Some features like Chat Prefix Completion are currently in beta and require using a specific beta endpoint[3]

## Conclusion

The DeepSeek API offers a familiar interface for developers who have worked with the OpenAI API, making it relatively straightforward to integrate or switch between services. With competitive pricing and specialized models like DeepSeek-R1 for reasoning tasks, it provides a viable alternative for many AI applications.

For building a robust Python wrapper, you should account for the authentication process, endpoint structure, model options, and error handling as described in this documentation. Additionally, you should be aware of the current limitations around embeddings and function calling if these features are required for your implementation.

As the DeepSeek API continues to evolve, staying updated with their official documentation would be beneficial for incorporating new features and capabilities as they become available.

Citations:
[1] https://api-docs.deepseek.com
[2] https://api-docs.deepseek.com/api/create-chat-completion
[3] https://api-docs.deepseek.com/guides/chat_prefix_completion
[4] https://docs.n8n.io/integrations/builtin/credentials/deepseek/
[5] https://api-docs.deepseek.com/quick_start/error_codes
[6] https://aws.amazon.com/blogs/big-data/use-deepseek-with-amazon-opensearch-service-vector-database-and-amazon-sagemaker/
[7] https://www.euclea-b-school.com/deepseek-ai-vs-open-ai-a-comprehensive-comparison/
[8] https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct/discussions/10
[9] https://platform.deepseek.com/docs/api-reference/chat/create
[10] https://api-docs.deepseek.com/api/create-completion
[11] https://api-docs.deepseek.com/quick_start/pricing
[12] https://www.datacamp.com/tutorial/deepseek-api
[13] https://www.reddit.com/r/SillyTavernAI/comments/1jbdccq/the_redacted_guide_to_deepseek_r1/
[14] https://api-docs.deepseek.com/api/deepseek-api
[15] https://www.postman.com/ai-on-postman/deepseek/documentation/gr0i44z/deepseek-api
[16] https://apidog.com/blog/how-to-use-deepseek-api-r1-v3/
[17] https://api-docs.deepseek.com/guides/fim_completion
[18] https://docs.gitguardian.com/secrets-detection/secrets-detection-engine/detectors/specifics/deepseek_api_key
[19] https://deepinfra.com/deepseek-ai/DeepSeek-R1/api
[20] https://python.useinstructor.com/integrations/deepseek/
[21] https://www.byteplus.com/en/topic/375654
[22] https://blog.skypilot.co/deepseek-rag/
[23] https://meetrix.io/articles/deepseekcoder-developer-guide/
[24] https://api-docs.deepseek.com/faq
[25] https://aws.amazon.com/blogs/big-data/use-deepseek-with-amazon-opensearch-service-vector-database-and-amazon-sagemaker/
[26] https://python.langchain.com/api_reference/deepseek/chat_models/langchain_deepseek.chat_models.ChatDeepSeek.html
[27] https://www.datacamp.com/tutorial/deepseek-api

---
Answer from Perplexity: pplx.ai/share