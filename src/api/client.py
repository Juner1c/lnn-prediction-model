import time
import requests
import logging
from typing import Dict, Any, Optional
from src.api.config import settings

logger = logging.getLogger("api.client")

class KloudtechProxyClient:
    """
    Backend Proxy & Cache Layer for KloudTrack API.
    Prevents exposing private API keys to client apps and manages rate-limit quotas.
    Routes requests directly to live Kloudtrack API (https://api.kloudtechsea.com/api/v1).
    """
    def __init__(self, base_url: str = None, api_key: str = None, cache_ttl: int = None):
        self.base_url = (base_url or settings.BASE_URL).rstrip('/')
        self.api_key = api_key or settings.API_KEY
        self.cache_ttl = cache_ttl or settings.CACHE_TTL_SECONDS
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
            elif resp.status_code == 429:
                logger.warning(f"[KLOUDTECH API RATE LIMIT 429] Endpoint {url} rate limited. Attempting cache fallback...")
                if cache_key in self._cache:
                    return self._cache[cache_key]["data"]
                # Try finding any cached entry for endpoint
                for k, entry in self._cache.items():
                    if k.startswith(endpoint):
                        return entry["data"]
                return {"success": False, "message": "Kloudtech API rate limit exceeded", "error": resp.text}
            else:
                logger.error(f"[KLOUDTECH API ERROR] HTTP {resp.status_code} from {url}: {resp.text}")
                if cache_key in self._cache:
                    return self._cache[cache_key]["data"]
                return {"success": False, "message": f"Kloudtech API returned HTTP {resp.status_code}", "error": resp.text}
        except Exception as err:
            logger.error(f"[KLOUDTECH API EXCEPTION] Failed to query {url}: {err}")
            if cache_key in self._cache:
                return self._cache[cache_key]["data"]
            return {"success": False, "message": f"Kloudtech API connection exception: {str(err)}", "error": str(err)}


    def fetch_station_history(self, station_id: str, take: int = 96) -> Dict[str, Any]:
        """
        Fetch historical time-series telemetry for a specific Kloudtech station.
        """
        endpoint = f"/telemetry/station/{station_id}/history"
        return self.fetch_with_cache(endpoint, params={"take": take})


proxy_client = KloudtechProxyClient()
