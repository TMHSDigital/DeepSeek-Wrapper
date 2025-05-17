import os
from typing import Optional, List
from dotenv import load_dotenv
from .config_manager import load_config, save_config, update_config

load_dotenv()

class DeepSeekConfig:
    """Configuration for DeepSeek API client."""
    
    # Available DeepSeek models
    MODELS = [
        "deepseek-chat",
        "deepseek-coder",
        "deepseek-llm-67b-chat",
        "deepseek-llm-7b-chat",
        "deepseek-reasoner",
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        default_model: Optional[str] = None,
    ):
        # Load configuration from file
        config = load_config()
        
        # API key is sensitive, so we prioritize the argument, then env var, then config
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or config.get("api_key")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL") or config.get("base_url")
        self.timeout = timeout if timeout != 30.0 else config.get("timeout", 30.0)
        self.max_retries = max_retries if max_retries != 3 else config.get("max_retries", 3)
        
        # For model selection, prioritize argument, then config file, then env var as fallback
        self.default_model = default_model or config.get("default_model") or os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat")
        
        # Validate that the default model is in the list of available models
        if self.default_model not in self.MODELS:
            self.default_model = "deepseek-chat"  # Fallback to default model
            
        if not self.api_key:
            raise ValueError("DeepSeek API key must be set via argument or DEEPSEEK_API_KEY env var.")
        
        # Save the configuration back to file
        self._save_config()
    
    def _save_config(self):
        """Save the current configuration to the config file."""
        config = {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "default_model": self.default_model
        }
        save_config(config)
    
    def get_available_models(self) -> List[str]:
        """Return a list of available models."""
        return self.MODELS
        
    def set_default_model(self, model: str) -> bool:
        """Set the default model and save it to the configuration file.
        
        Args:
            model: The model name to set as default
            
        Returns:
            True if successful, False if the model is not valid
        """
        if model in self.MODELS:
            self.default_model = model
            update_config("default_model", model)
            return True
        return False 