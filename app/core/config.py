import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/youtube_analyzer")

settings = Settings()
