import os
import glob
import pandas as pd
import numpy as np

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

print(f"Found {len(csv_files)} total CSV files in data/.")

# Group files by station
station_files = {}
for filepath in csv_files:
    filename = os.path.basename(filepath)
    if "_ from" not in filename:
        continue
    st_name = filename.split("_ from")[0]
    if st_name not in station_files:
        station_files[st_name] = []
    station_files[st_name].append(filepath)

summary_list = []

for st_name, files in station_files.items():
    dfs = []
    for f in files:
        df_f = pd.read_csv(f)
        dfs.append(df_f)
    
    df = pd.concat(dfs, ignore_index=True)
    df["recordedAt_dt"] = pd.to_datetime(df["recordedAt"], format="mixed", errors="coerce")
    df = df.dropna(subset=["recordedAt_dt"]).sort_values("recordedAt_dt").drop_duplicates("recordedAt_dt")
    
    num_rows = len(df)
    min_date = df["recordedAt_dt"].min()
    max_date = df["recordedAt_dt"].max()
    
    temp_nulls = df["temperature"].isna().sum() + (df["temperature"] <= 5.0).sum() + (df["temperature"] >= 50.0).sum()
    temp_min = df["temperature"].min()
    temp_max = df["temperature"].max()
    
    time_diffs = df["recordedAt_dt"].diff()
    max_gap_hours = time_diffs.max().total_seconds() / 3600.0 if not time_diffs.empty else 0
    
    summary_list.append({
        "station": st_name,
        "total_records": num_rows,
        "start_date": str(min_date),
        "end_date": str(max_date),
        "invalid_temp_readings": int(temp_nulls),
        "min_temp": float(temp_min) if not pd.isna(temp_min) else None,
        "max_temp": float(temp_max) if not pd.isna(temp_max) else None,
        "max_outage_hours": round(max_gap_hours, 1)
    })

df_summary = pd.DataFrame(summary_list)
print("\n=== COMBINED 2025-2026 BATAAN STATIONS PROFILING SUMMARY ===")
print(df_summary.to_string(index=False))
