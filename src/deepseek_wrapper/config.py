import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class DeepSeekConfig:
    """Configuration for DeepSeek API client."""
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.timeout = timeout
        self.max_retries = max_retries
        if not self.api_key:
            raise ValueError("DeepSeek API key must be set via argument or DEEPSEEK_API_KEY env var.") 