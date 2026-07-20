import time
import requests
from typing import Dict, Any, Optional
from src.api.config import settings

class KloudtechProxyClient:
    """
    Backend Proxy & Cache Layer for KloudTrack API.
    Prevents exposing private API keys to client apps and manages rate-limit quotas.
    Follows recommended flow: Client App -> Client Backend/Cache Layer -> KloudTrack API
    """
    def __init__(self, base_url: str = settings.BASE_URL, api_key: str = settings.API_KEY, cache_ttl: int = settings.CACHE_TTL_SECONDS):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-kloudtrack-key": self.api_key,
            "Accept": "application/json"
        }

    def fetch_with_cache(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cache_key = f"{endpoint}:{str(sorted(params.items()) if params else '')}"
        now = time.time()

        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self.cache_ttl:
                return entry["data"]

        # Call remote KloudTrack API
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._cache[cache_key] = {"timestamp": now, "data": data}
                return data
            else:
                return {"success": False, "message": f"KloudTrack API error: {resp.status_code}", "data": None}
        except Exception as e:
            return {"success": False, "message": f"Connection error to KloudTrack API: {str(e)}", "data": None}

proxy_client = KloudtechProxyClient()
