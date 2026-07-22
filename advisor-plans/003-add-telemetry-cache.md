# Plan 003 — Add Telemetry Cache Layer

**Finding**: PERF-01 | **Commit**: `3f04f14` | **Effort**: S | **Risk**: LOW

## Why This Matters

Every API call (dashboard, forecast, current, record-by-id) calls `load_real_openmeteo_telemetry()` which re-reads a 2.6MB CSV, parses it with pandas, iterates all 7 stations, and computes heat indices. The frontend polls every 3 seconds. That's ~20 full CSV re-parses per minute per connected client.

## Current State

```python
# src/api/routes.py — every endpoint does this:
readings = load_real_openmeteo_telemetry()  # 2.6MB CSV read + parse + compute
```

No caching anywhere. Ironically, `src/api/client.py` implements an in-memory TTL cache that is never used.

## Steps

### Step 1: Add module-level cache with TTL

Add a simple time-based cache at the top of `src/api/routes.py`, after the global variables:

```python
import time

_telemetry_cache = None
_telemetry_cache_time = 0.0
_CACHE_TTL_SECONDS = 10.0  # Refresh every 10s, not every call

def get_cached_telemetry():
    global _telemetry_cache, _telemetry_cache_time
    now = time.time()
    if _telemetry_cache is None or (now - _telemetry_cache_time) > _CACHE_TTL_SECONDS:
        _telemetry_cache = load_real_openmeteo_telemetry()
        _telemetry_cache_time = now
    return _telemetry_cache
```

### Step 2: Replace all `load_real_openmeteo_telemetry()` calls with `get_cached_telemetry()`

Four call sites:
- `get_dashboard()` at L225
- `get_station_forecast()` at L243
- `get_station_current()` at L350
- `get_telemetry_by_id()` at L361

### Step 3: Verify

```bash
python -m pytest tests/test_api.py -v
```

Expected: All tests pass (cache is transparent to consumers).

Manual verification: Start the server, open dashboard, check that the server log doesn't show CSV reads every 3 seconds.

## Done Criteria

- `grep "load_real_openmeteo_telemetry" src/api/routes.py` returns only the function definition and the cache wrapper call, not direct calls from endpoints
- All tests pass
- No behavioral change from the user's perspective (data still updates, just not wastefully)

## Scope Boundaries

- **In scope**: Adding the TTL cache wrapper for telemetry reads
- **Out of scope**: Caching the forecast computation (that should be addressed separately), the dead `client.py` proxy cache code

## Maintenance Note

When a real database or streaming data source replaces the CSV, this cache pattern remains useful but the TTL should be configurable via environment variable.
