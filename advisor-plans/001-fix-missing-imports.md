# Plan 001 — Fix Missing `urllib` and `json` Imports in `routes.py`

**Finding**: BUG-01 | **Commit**: `3f04f14` | **Effort**: S | **Risk**: LOW

## Why This Matters

`fetch_live_openmeteo_station_telemetry()` at `src/api/routes.py:L55-L72` uses `urllib.request.Request`, `urllib.request.urlopen`, and `json.loads` — none of which are imported. Every call to this function raises a `NameError`, which is silently swallowed by `except Exception: pass` at L70-71. The API then falls through to stale CSV data or hardcoded fallbacks while returning `"Real Open-Meteo telemetry retrieved successfully"` — a lie.

## Current State

```python
# src/api/routes.py (lines 1-6)
import os
import torch
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
```

No `import urllib.request` or `import json` anywhere in the file.

## Steps

### Step 1: Add missing imports

Add `import json` and `import urllib.request` to the imports block at the top of `src/api/routes.py`, after `import os` (line 1).

```python
import os
import json
import urllib.request
import torch
# ... rest unchanged
```

### Step 2: Verify the fix

```bash
python -c "from src.api.routes import fetch_live_openmeteo_station_telemetry; print('Import OK')"
```

Expected: `Import OK` (no `NameError`)

### Step 3: Run existing tests

```bash
python -m pytest tests/test_api.py -v
```

Expected: All tests pass (no regressions — tests don't exercise the live fetch path).

## Done Criteria

- `python -c "from src.api.routes import fetch_live_openmeteo_station_telemetry"` exits 0
- `python -m pytest tests/test_api.py` passes all tests
- `grep -n "import json" src/api/routes.py` returns a line number
- `grep -n "import urllib.request" src/api/routes.py` returns a line number

## Scope Boundaries

- **In scope**: Adding the two import statements to `src/api/routes.py`
- **Out of scope**: Fixing the silent exception swallowing (Plan 005), adding tests for the live fetch path, or modifying the fallback cascade logic

## Escape Hatches

- If `urllib.request.urlopen` is blocked by a corporate proxy or firewall, STOP — the existing fallback to CSV data is intentional for offline development. The imports should still be added so the function doesn't crash with `NameError`.

## Maintenance Note

Any future addition of external HTTP calls should import `requests` (already in `requirements.txt`) instead of `urllib.request` — `requests` has better error handling and timeouts. But that's a separate change.
