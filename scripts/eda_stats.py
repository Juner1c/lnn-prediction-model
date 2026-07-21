import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
csv_path = os.path.join(BASE_DIR, "data", "timeseries_15min_clean.csv")
df = pd.read_csv(csv_path)


# Clean column names
df.columns = [c.encode('ascii', 'ignore').decode('ascii').strip() for c in df.columns]
print("Cleaned Columns:", df.columns.tolist())

temp_col = [c for c in df.columns if 'temperature_2m' in c][0]
rh_col = [c for c in df.columns if 'relative_humidity_2m' in c][0]
dew_col = [c for c in df.columns if 'dew_point_2m' in c][0]
app_temp_col = [c for c in df.columns if 'apparent_temperature' in c][0]
wind_col = [c for c in df.columns if 'wind_speed' in c][0]

print("\n--- Detailed Statistical Summary ---")
stats = df[[temp_col, rh_col, dew_col, app_temp_col, wind_col]].describe()
print(stats)

# Heat Index Risk Levels (based on Apparent Temperature)
app = df[app_temp_col]
caution = (app >= 27) & (app < 32)
extreme_caution = (app >= 32) & (app < 41)
danger = (app >= 41) & (app < 54)
extreme_danger = app >= 54

print("\n--- Heat Index Risk Breakdown (% of total readings) ---")
print(f"Normal (<27°C): {(app < 27).sum() / len(df) * 100:.2f}%")
print(f"Caution (27°C - 32°C): {caution.sum() / len(df) * 100:.2f}%")
print(f"Extreme Caution (32°C - 41°C): {extreme_caution.sum() / len(df) * 100:.2f}%")
print(f"Danger (41°C - 54°C): {danger.sum() / len(df) * 100:.2f}%")
print(f"Extreme Danger (>=54°C): {extreme_danger.sum() / len(df) * 100:.2f}%")

print("\nPeak Apparent Temperature:", app.max(), "°C at time:", df.loc[app.idxmax(), 'time'], "at location:", df.loc[app.idxmax(), 'location_id'])
