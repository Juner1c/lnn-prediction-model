import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

KLOUDTRACK_KEY_HEADER = APIKeyHeader(name="x-kloudtrack-key", auto_error=False)
API_KEY_HEADER_FALLBACK = APIKeyHeader(name="x-api-key", auto_error=False)

import logging

logger = logging.getLogger("api.auth")

DEFAULT_API_KEY = os.getenv("KLOUDTRACK_API_KEY")
if not DEFAULT_API_KEY:
    DEFAULT_API_KEY = "kloudtrack_secret_key_123"
    logger.warning("[SECURITY WARN] KLOUDTRACK_API_KEY environment variable not set. Using default development key.")


def verify_api_key(
    kloudtrack_key: str = Security(KLOUDTRACK_KEY_HEADER),
    fallback_key: str = Security(API_KEY_HEADER_FALLBACK)
) -> str:
    key = kloudtrack_key or fallback_key
    if not key or key != DEFAULT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or Invalid API key"
        )
    return key
