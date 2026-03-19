import os
from .config import Settings

def load_config(config_path: str) -> Settings:
    return Settings.from_yaml(config_path)