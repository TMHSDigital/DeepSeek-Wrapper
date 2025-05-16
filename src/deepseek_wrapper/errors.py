class DeepSeekAPIError(Exception):
    """Raised for API errors from DeepSeek."""
    pass

class DeepSeekAuthError(DeepSeekAPIError):
    """Raised for authentication errors from DeepSeek."""
    pass 