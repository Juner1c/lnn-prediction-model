# Plan 005 — Replace Silent Exception Swallowing With Structured Logging

**Finding**: SEC-04 | **Commit**: `3f04f14` | **Effort**: S | **Risk**: LOW

## Why This Matters

Six `except Exception: pass` blocks silently eat all errors including the `NameError` from missing imports (BUG-01). Production debugging is impossible — you can't troubleshoot what you can't see. The API returns "success" with fallback data while critical paths are broken.

## Affected Locations

1. `src/api/routes.py:L70-71` — Live API fetch failure
2. `src/api/routes.py:L136-137` — Live API data processing failure
3. `src/api/routes.py:L183-184` — CSV fallback read failure
4. `src/data/storage_adapter.py:L25-26` — JSON file read failure

## Steps

### Step 1: Add Python logging to routes.py

At the top of `src/api/routes.py`, add:
```python
import logging

logger = logging.getLogger("lnn-api")
```

### Step 2: Replace each `except Exception: pass` with logged warnings

Example for L70-71:
```python
except Exception as e:
    logger.warning("Live Open-Meteo fetch failed for (%.4f, %.4f): %s", lat, lon, e)
```

Example for L136-137:
```python
except Exception as e:
    logger.warning("Failed to process live API response: %s", e)
```

Example for L183-184:
```python
except Exception as e:
    logger.warning("CSV fallback read failed: %s", e)
```

Example for storage_adapter.py L25-26:
```python
except Exception as e:
    logger.warning("Failed to read existing file %s: %s", target_file, e)
    existing = []
```

### Step 3: Add data provenance to API responses

In `get_dashboard()`, track which data source actually served the data. Add a `source` field:
```python
return KloudtrackResponse(
    message=f"Telemetry retrieved ({data_source})",  # "live_api" | "csv_cache" | "fallback"
    data=entries
)
```

### Step 4: Verify

```bash
python -m pytest tests/ -v
```

Expected: All tests pass.

```bash
grep -n "except Exception" src/api/routes.py src/data/storage_adapter.py
```

Expected: No bare `pass` after any `except Exception`.

## Done Criteria

- `grep -n "except.*pass" src/api/routes.py src/data/storage_adapter.py` returns nothing
- All exception handlers log the error with context
- Tests pass
- Starting the server with `PYTHONUNBUFFERED=1` shows log output when the live API path fails

## Scope Boundaries

- **In scope**: Replacing `pass` with `logger.warning()` in the 4 identified locations
- **Out of scope**: Setting up a full logging infrastructure (structured JSON logging, log aggregation, log levels). That's a future enhancement. Python's built-in `logging` module is sufficient here.

## Maintenance Note

When transitioning to production, configure the logger with `logging.basicConfig(level=logging.INFO)` in `main.py` and consider adding `uvicorn` log integration.
