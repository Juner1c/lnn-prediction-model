import os
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

KLOUDTRACK_KEY_HEADER = APIKeyHeader(name="x-kloudtrack-key", auto_error=False)
API_KEY_HEADER_FALLBACK = APIKeyHeader(name="x-api-key", auto_error=False)

import logging

logger = logging.getLogger("api.auth")

from src.api.config import settings

DEFAULT_API_KEY = settings.API_KEY or "kloudtrack_secret_key_123"

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


def verify_optional_api_key(
    kloudtrack_key: str = Security(KLOUDTRACK_KEY_HEADER),
    fallback_key: str = Security(API_KEY_HEADER_FALLBACK)
) -> Optional[str]:
    return kloudtrack_key or fallback_key
