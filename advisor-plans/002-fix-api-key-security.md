# Plan 002 — Fix API Key Security

**Finding**: SEC-01, BUG-03 | **Commit**: `3f04f14` | **Effort**: M | **Risk**: MED

## Why This Matters

The API key `kloudtrack_secret_key_123` is hardcoded in 5 locations including the frontend JavaScript (`static/app.js:L2`), which ships it to every browser. Authentication is cosmetic — anyone with DevTools can extract the key.

## Current State

The same static key appears in:
1. `src/api/config.py:L6` — Pydantic Settings default
2. `src/api/auth.py:L9` — `DEFAULT_API_KEY` fallback
3. `static/app.js:L2` — JavaScript constant sent to browser
4. `docker-compose.yml:L12` — environment variable
5. `.env:L31` — environment file (gitignored but value is duplicated in committed files)

## Steps

### Step 1: Remove API key from frontend JavaScript

The dashboard is served from the same origin as the API. Dashboard endpoints should not require API key auth — they're internal monitoring. Split the routes:

In `src/api/routes.py`:
- Dashboard endpoint (`/telemetry/dashboard`) — remove `api_key: str = Depends(verify_api_key)` parameter
- Forecast endpoint (`/telemetry/station/{stationId}/forecast`) — remove auth dependency
- Current endpoint (`/telemetry/station/{stationId}/current`) — remove auth dependency
- Keep auth on POST `/api/v1/heat-index/calculate` (programmatic API)

In `static/app.js`:
- Remove `const API_KEY = "kloudtrack_secret_key_123";`
- Remove `const HEADERS = { "x-kloudtrack-key": API_KEY, ... };`
- Change all `fetch(url, { headers: HEADERS })` to `fetch(url)`

### Step 2: Remove hardcoded default from auth.py and config.py

In `src/api/auth.py`, change:
```python
DEFAULT_API_KEY = os.getenv("KLOUDTRACK_API_KEY", "kloudtrack_secret_key_123")
```
To:
```python
DEFAULT_API_KEY = os.getenv("KLOUDTRACK_API_KEY", "")
```

Same for `src/api/config.py:L6`:
```python
API_KEY: str = os.getenv("KLOUDTRACK_API_KEY", "")
```

This forces the key to be set via environment variable — no functional default.

### Step 3: Create `.env.example`

Create a `.env.example` file at repo root:
```
KLOUDTRACK_API_KEY=your_api_key_here
KLOUDTECH_BASE_URL=https://api.kloudtechsea.com/api/v1
```

### Step 4: Update docker-compose.yml

Replace the hardcoded key with an env_file reference:
```yaml
env_file:
  - .env
```

### Step 5: Update tests

In `tests/test_api.py`, update `test_dashboard_success` and other dashboard tests to work without the API key header. Keep auth tests for the programmatic POST endpoint.

### Step 6: Verify

```bash
python -m pytest tests/ -v
```

Expected: All tests pass with the new auth split.

```bash
grep -r "kloudtrack_secret_key_123" src/ static/ docker-compose.yml
```

Expected: No results.

## Done Criteria

- `grep -r "kloudtrack_secret_key_123" src/ static/ docker-compose.yml` returns nothing
- Dashboard endpoints work without API key
- POST `/api/v1/heat-index/calculate` still requires API key
- `.env.example` exists
- All tests pass

## Scope Boundaries

- **In scope**: Removing hardcoded keys, splitting auth between dashboard and API, creating `.env.example`
- **Out of scope**: Implementing session-based auth, JWT tokens, or OAuth — those are future enhancements

## Escape Hatches

- If the project requires ALL endpoints to be authenticated (e.g., deployed publicly), STOP and report back. The plan assumes the dashboard is internal/same-origin.
