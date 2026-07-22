# Plan 004 — Fix Hardcoded Absolute Paths

**Finding**: TEST-02, SEC-03, DEBT-04 | **Commit**: `3f04f14` | **Effort**: S | **Risk**: LOW

## Why This Matters

Multiple files hardcode `c:\Users\Jhonric Gorillo\Desktop\JHONRIC_FILES\OJT\LNN-Prediction-Model-Project\...` as absolute paths. These break on any other machine, any CI runner (GitHub Actions runs `ubuntu-latest`), any Docker container, and any teammate's laptop.

## Affected Files

1. `src/data/storage_adapter.py:L10` — `base_dir` default
2. `tests/test_ingestion.py:L10, L60` — test paths
3. `tests/test_stgnn_forecaster.py:L10` — locations CSV path
4. `tests/test_deployment.py:L11-L24` — file existence checks
5. `scripts/parse_dataset.py:L4-L5` — raw data paths
6. `scripts/eda_stats.py:L4` — CSV path

## Steps

### Step 1: Define a project root helper

Convention: compute paths relative to the file's location. The pattern used throughout this repo is `os.path.dirname(__file__)`.

### Step 2: Fix `storage_adapter.py`

Change L10 from:
```python
def __init__(self, base_dir: str = r"c:\Users\Jhonric Gorillo\Desktop\..."):
```
To:
```python
def __init__(self, base_dir: str = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")):
```

### Step 3: Fix all test files

Use `os.path.dirname(__file__)` to construct paths relative to the test file location.

Example for `test_ingestion.py:L10`:
```python
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TestDataIngestion(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(PROJECT_ROOT, "data", "test_raw")
```

Same pattern for `test_stgnn_forecaster.py:L10`:
```python
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TestSpatialTemporalGNN(unittest.TestCase):
    def setUp(self):
        self.locations_csv = os.path.join(PROJECT_ROOT, "data", "locations.csv")
```

For `test_deployment.py`, replace all 4 hardcoded paths with `os.path.join(PROJECT_ROOT, ...)`.

### Step 4: Fix scripts

Same pattern for `parse_dataset.py` and `eda_stats.py` — use `os.path.dirname(__file__)` relative paths.

### Step 5: Fix `routes.py:L35`

`CSV_PATH = "data/timeseries_15min_clean.csv"` is a relative path that depends on the working directory. Make it absolute relative to the project:
```python
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "timeseries_15min_clean.csv")
```

### Step 6: Verify

```bash
grep -rn "Jhonric Gorillo" src/ tests/ scripts/
```

Expected: No results.

```bash
python -m pytest tests/ -v
```

Expected: All tests pass on any machine.

## Done Criteria

- `grep -rn "Jhonric Gorillo" src/ tests/ scripts/` returns nothing
- All tests pass
- `python -m pytest tests/ -v` from the project root works
- Docker build still works

## Scope Boundaries

- **In scope**: Replacing all hardcoded absolute paths in `src/`, `tests/`, `scripts/`
- **Out of scope**: The `.env` file paths (those are user-specific configuration, correctly gitignored), the obsidian vault paths
