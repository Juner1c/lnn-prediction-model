import os
from pydantic import BaseModel

# Parse .env file directly using standard library
env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and not os.getenv(k):
                    os.environ[k] = v

class Settings(BaseModel):
    BASE_URL: str = os.getenv("KLOUDTECH_BASE_URL", "https://api.kloudtechsea.com/api/v1")
    API_KEY: str = os.getenv("KLOUDTRACK_API_KEY", "kloudtrack_secret_key_123")

    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "60"))

settings = Settings()

