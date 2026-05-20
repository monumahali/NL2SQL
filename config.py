import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    """Simple settings class that loads from environment variables"""
    def __init__(self):
        # Try multiple ways to get the API key
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")

settings = Settings()
