# Web UI Guide

The DeepSeek Wrapper provides a modern, feature-rich chat interface for interacting with DeepSeek AI models.

## Interface Overview

![UI Overview](images/ui-overview.png)

The interface consists of several key components:
- **Chat Area**: The main area where conversations are displayed
- **Input Box**: Where you type your messages
- **Settings Button**: Access to customize your experience
- **File Upload**: Button to upload documents for context
- **Conversation History**: List of your previous conversations

## Starting a New Chat

1. When you first open the application, you'll see an empty chat
2. Type your message in the input box at the bottom of the screen
3. Press Enter or click the send button to submit your message
4. The AI will respond in the chat area

## Chat Features

### Markdown Support

The chat interface supports full Markdown formatting, including:
- **Bold**, *italic*, and ~~strikethrough~~ text
- Code blocks with syntax highlighting
- Lists and tables
- Links and images

### Code Handling

Code snippets are displayed with syntax highlighting for better readability. You can:
- Copy code blocks with a single click on the copy button
- See the language identified in the top-right of each code block

### Uploading Files

To provide context from a document:

1. Click the upload button next to the input field
2. Select a supported file (PDF, DOCX, or TXT)
3. Once uploaded, the content will be processed and included in your next message
4. You can reference the document in your query

## Customizing Your Experience

### Profile Settings

1. Click the settings icon in the top right corner
2. In the modal, you can:
   - Set your display name
   - Choose or upload an avatar
   - Configure system prompts
   - Adjust UI preferences

### System Prompts

System prompts help guide the AI's behavior:

1. Access system prompt settings via the settings modal
2. Enter your custom system prompt or select from templates
3. Save your changes
4. New conversations will use your custom system prompt

### Conversation Management

- **Starting a new conversation**: Click the "New Chat" button
- **Viewing history**: See previous conversations in the sidebar
- **Continuing a conversation**: Click on any previous conversation to resume it

## Keyboard Shortcuts

- `Ctrl+Enter` / `Cmd+Enter`: Send message
- `Esc`: Cancel current input
- `Up Arrow`: Edit your last message
- `Ctrl+K` / `Cmd+K`: Quick action menu

## Mobile Usage

The interface is fully responsive and works on mobile devices:
- Swipe from the left edge to access conversation history on small screens
- All features are accessible through touch-friendly controls 