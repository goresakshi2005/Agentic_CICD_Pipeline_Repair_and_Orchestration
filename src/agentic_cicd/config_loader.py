import yaml
import os
from .config import Settings

def load_config(path: str) -> Settings:
    """Load configuration from a YAML file and override with environment variables."""
    if os.path.exists(path):
        with open(path) as f:
            yaml_config = yaml.safe_load(f)
        # Merge with environment (env takes precedence)
        return Settings(**yaml_config)
    else:
        # Fallback to env only
        return Settings()