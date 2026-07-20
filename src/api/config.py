import os
from pydantic import BaseModel

class Settings(BaseModel):
    BASE_URL: str = os.getenv("KLOUDTECH_BASE_URL", "https://api.kloudtechsea.com/api/v1")
    API_KEY: str = os.getenv("KLOUDTRACK_API_KEY", "kloudtrack_secret_key_123")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "60"))

settings = Settings()
