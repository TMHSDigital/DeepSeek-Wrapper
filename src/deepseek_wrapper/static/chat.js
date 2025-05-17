function handleStreamingEvent(event) {
    try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
            case 'user_msg_received':
                console.log('User message received:', data.message);
                break;
                
            case 'assistant_msg_start':
                console.log('Assistant starting to respond');
                createAssistantResponseElement(data.message);
                break;
                
            case 'content_chunk':
                appendToAssistantResponse(data.chunk);
                break;
                
            case 'replace_content':
                // Handle replacing the entire content (used for answer extraction)
                replaceAssistantResponseContent(data.content);
                break;
                
            case 'complete':
                console.log('Response complete');
                finalizeAssistantResponse(data.message);
                stopTypingIndicator();
                break;
                
            case 'error':
                console.error('Error from server:', data.error);
                showErrorInAssistantResponse(data.error);
                stopTypingIndicator();
                break;
                
            default:
                console.warn('Unknown event type:', data.type);
        }
    } catch (error) {
        console.error('Error handling streaming event:', error);
    }
}

// Add a function to replace assistant response content
function replaceAssistantResponseContent(content) {
    const lastAssistantBubble = document.querySelector('.assistant-msg:last-child .content');
    if (lastAssistantBubble) {
        // Clear existing content
        lastAssistantBubble.innerHTML = '';
        
        // Add new processed content
        const formattedContent = markdownToHtml(content);
        lastAssistantBubble.innerHTML = formattedContent;
        
        // Re-add code highlighting
        highlightCodeBlocks();
    }
} 