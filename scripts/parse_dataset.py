import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
raw_path = os.path.join(BASE_DIR, "obsidian-vault", "_raw", "open-meteo-dataset-for-heatindex-3months.csv")
output_dir = os.path.join(BASE_DIR, "data")
os.makedirs(output_dir, exist_ok=True)


with open(raw_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Split CSV sections by empty lines
sections = []
current_section = []
for line in lines:
    if line.strip() == "":
        if current_section:
            sections.append(current_section)
            current_section = []
    else:
        current_section.append(line)
if current_section:
    sections.append(current_section)

print(f"Found {len(sections)} sections in raw CSV.")

# Section 0: Locations Metadata
import io
df_locations = pd.read_csv(io.StringIO("".join(sections[0])))
df_locations.to_csv(os.path.join(output_dir, "locations.csv"), index=False)
print("--- Locations Metadata ---")
print(df_locations)

# Section 1: Current Weather Snapshot
df_current = pd.read_csv(io.StringIO("".join(sections[1])))
df_current.to_csv(os.path.join(output_dir, "current_snapshot.csv"), index=False)
print("\n--- Current Weather Snapshot ---")
print(df_current)

# Section 2: 15-Minute Timeseries
df_ts = pd.read_csv(io.StringIO("".join(sections[2])))
print("\n--- Raw Timeseries Info ---")
print(df_ts.info())
print("\nMissing values per column:")
print(df_ts.isna().sum())

# Drop rows where all weather values are NaN
weather_cols = [c for c in df_ts.columns if c not in ['location_id', 'time']]
df_ts_clean = df_ts.dropna(subset=weather_cols, how='all').copy()

print(f"\nCleaned timeseries count: {len(df_ts_clean)} rows (from {len(df_ts)} total rows).")
print(f"Time range of valid data: {df_ts_clean['time'].min()} to {df_ts_clean['time'].max()}")

df_ts_clean.to_csv(os.path.join(output_dir, "timeseries_15min_clean.csv"), index=False)

print("\n--- Summary Statistics (Valid Data) ---")
print(df_ts_clean.describe())

# Per-location statistics
print("\n--- Per-Location Breakdown ---")
for loc_id, group in df_ts_clean.groupby('location_id'):
    print(f"Location {loc_id}: {len(group)} rows | Time: {group['time'].min()} to {group['time'].max()}")
