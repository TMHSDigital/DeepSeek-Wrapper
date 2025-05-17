# Frequently Asked Questions

## General Questions

### What is DeepSeek Wrapper?
DeepSeek Wrapper is a modern web interface and client library for interacting with DeepSeek's AI models. It provides a user-friendly chat interface, document processing capabilities, and a clean API for developers.

### Which DeepSeek models are supported?
The wrapper supports all the latest DeepSeek models for chat, completion, and embeddings. You can configure which model you want to use through environment variables or the API.

### Do I need a DeepSeek API key?
Yes, you need an API key from DeepSeek to use this wrapper. You can obtain one by signing up at [https://platform.deepseek.com](https://platform.deepseek.com).

## Installation & Setup

### How do I install DeepSeek Wrapper?
You can install it by cloning the repository and installing the dependencies with pip. See the [Getting Started](getting-started.md) guide for detailed instructions.

### What are the system requirements?
- Python 3.8 or higher
- Modern web browser (for UI)
- Internet connection
- DeepSeek API key

### How do I set my API key?
Add your API key to the `.env` file in the root directory:
```
DEEPSEEK_API_KEY=your_api_key_here
```

### Can I use this wrapper offline?
No, the wrapper needs to connect to the DeepSeek API servers, which requires an internet connection.

## Usage

### How do I start a new conversation?
In the web UI, click the "New Chat" button in the sidebar. In the API, make a request without specifying a conversation ID to start a new one.

### Can I upload files to provide context?
Yes, you can upload PDF, DOCX, and TXT files using the file upload button next to the input field. The content will be processed and included in the context for your next message.

### How do I set a custom system prompt?
In the web UI, click the settings icon and enter your system prompt in the appropriate field. In the API, include the `system_prompt` parameter in your request.

### Can I export my conversations?
Currently, there's no built-in export feature, but this is planned for a future release.

## Troubleshooting

### The application won't start
- Ensure you have Python 3.8+ installed
- Verify that all dependencies are installed
- Check that your `.env` file exists and contains your API key
- Look at the console output for specific error messages

### I'm getting API key errors
- Ensure your API key is correctly set in the `.env` file
- Check that the API key is valid and active
- Make sure there are no extra spaces or quotes around the key

### The AI responses are cut off
- This may be due to token limits. Try shortening your messages or context
- Check your internet connection, as streaming might be interrupted

### File uploads aren't working
- Ensure the file is in a supported format (PDF, DOCX, TXT)
- Check that the file size is within the limits (default is 10MB)
- Verify that the uploads directory exists and is writable

## Development

### How can I contribute to the project?
See the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to the project.

### Can I extend the UI with custom components?
Yes, the frontend is built with HTML, CSS, and JavaScript. You can modify or extend it by editing the templates and static files.

### How do I add support for a new file format?
To add support for a new file format, you'll need to implement a parser in the `document_processor.py` file and register it in the file type handlers.

### Is there an API for programmatic access?
Yes, you can use the Python client API or make HTTP requests directly to the REST API endpoints. See the [API Reference](api-reference.md) for details.

## Pricing & Limits

### Is DeepSeek Wrapper free to use?
The wrapper itself is open-source and free to use. However, you'll need a DeepSeek API key, which may have associated costs depending on your usage.

### Are there rate limits?
Rate limits are determined by DeepSeek's API policies. The wrapper itself doesn't impose additional limits.

### How can I monitor my API usage and costs?
You can track your API usage through the DeepSeek platform dashboard. The wrapper doesn't currently include built-in usage monitoring.

## Security

### Is my data secure?
The wrapper doesn't store your conversations on external servers. Data is stored locally, and API communications use HTTPS. However, your data is sent to DeepSeek's servers for processing, subject to their privacy policy.

### Are my API keys protected?
API keys are stored in the `.env` file, which should not be committed to version control. In production, use secure environment variable handling appropriate for your deployment platform. 