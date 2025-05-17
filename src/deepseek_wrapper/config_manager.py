import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default path for the config file, relative to the project root
DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                 "config.json")

# Default configuration values
DEFAULT_CONFIG = {
    "api_key": None,
    "base_url": "https://api.deepseek.com/v1",
    "default_model": "deepseek-chat",
    "timeout": 30.0,
    "max_retries": 3,
    "extract_answer_only": False  # Added setting to control answer extraction
}

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_file: Path to the config file. If None, uses the default path.
        
    Returns:
        Dictionary containing configuration values.
    """
    config_file = config_file or DEFAULT_CONFIG_FILE
    
    # Start with default configuration
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from environment variables first (higher priority than config file for secrets)
    if os.getenv("DEEPSEEK_API_KEY"):
        config["api_key"] = os.getenv("DEEPSEEK_API_KEY")
    
    if os.getenv("DEEPSEEK_BASE_URL"):
        config["base_url"] = os.getenv("DEEPSEEK_BASE_URL")
    
    # Override with values from config file if it exists
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                
            # Update config with values from file, except API key which should come from env vars
            for key, value in file_config.items():
                if key != "api_key" or not config["api_key"]:  # Don't override API key from env
                    config[key] = value
                    
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {str(e)}")
    else:
        logger.info(f"Config file {config_file} not found, using defaults")
        
        # Create the config file with default values if it doesn't exist
        try:
            save_config(config, config_file)
        except Exception as e:
            logger.warning(f"Could not create default config file: {str(e)}")
    
    return config

def save_config(config: Dict[str, Any], config_file: Optional[str] = None) -> bool:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Dictionary containing configuration values.
        config_file: Path to the config file. If None, uses the default path.
        
    Returns:
        True if successful, False otherwise.
    """
    config_file = config_file or DEFAULT_CONFIG_FILE
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Don't save API key to config file for security reasons
        save_config = config.copy()
        if "api_key" in save_config:
            save_config["api_key"] = None
            
        with open(config_file, 'w') as f:
            json.dump(save_config, f, indent=2)
            
        logger.info(f"Saved configuration to {config_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving config file {config_file}: {str(e)}")
        return False

def update_config(key: str, value: Any, config_file: Optional[str] = None) -> bool:
    """
    Update a specific configuration value and save it.
    
    Args:
        key: Configuration key to update.
        value: New value to set.
        config_file: Path to the config file. If None, uses the default path.
        
    Returns:
        True if successful, False otherwise.
    """
    config = load_config(config_file)
    config[key] = value
    return save_config(config, config_file)

def get_config_value(key: str, config_file: Optional[str] = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key to retrieve.
        config_file: Path to the config file. If None, uses the default path.
        
    Returns:
        The value for the specified key, or None if the key doesn't exist.
    """
    config = load_config(config_file)
    return config.get(key) 