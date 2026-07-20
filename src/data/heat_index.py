import numpy as np
from typing import Union, List, Tuple

def calculate_heat_index(temperature_c: float, relative_humidity: float) -> float:
    """
    Calculate NWS/Steadman/Rothfusz Heat Index given dry-bulb temperature in °C and RH (0-100%).
    Returns Heat Index (apparent temperature) in °C.
    """
    T = (temperature_c * 9.0 / 5.0) + 32.0
    RH = relative_humidity

    HI_simple = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (RH * 0.094))

    if HI_simple < 80.0:
        HI_f = HI_simple
    else:
        HI_f = (-42.379 +
                2.04901523 * T +
                10.14333127 * RH -
                0.22475541 * T * RH -
                0.00683783 * T * T -
                0.05481717 * RH * RH +
                0.00122874 * T * T * RH +
                0.00085282 * T * RH * RH -
                0.00000199 * T * T * RH * RH)

        if RH < 13.0 and 80.0 <= T <= 112.0:
            adj = ((13.0 - RH) / 4.0) * np.sqrt((17.0 - abs(T - 95.0)) / 17.0)
            HI_f -= adj
        elif RH > 85.0 and 80.0 <= T <= 87.0:
            adj = ((RH - 85.0) / 10.0) * ((87.0 - T) / 5.0)
            HI_f += adj

    HI_c = (HI_f - 32.0) * 5.0 / 9.0
    return float(round(HI_c, 2))

def calculate_apparent_temp_lu_romps(temperature_c: float, dew_point_c: float, wind_speed_kmh: float = 0.0) -> float:
    """
    Calculate Lu & Romps / Steadman Apparent Temperature given dry-bulb temperature (°C),
    dew point (°C), and wind speed (km/h).
    Benchmark check: 30°C temp / 25°C dew point -> ~33.2°C.
    """
    # Water vapor pressure e (hPa) using Tetens equation from dew point
    e = 6.112 * np.exp((17.67 * dew_point_c) / (dew_point_c + 243.5))
    
    # Steadman / Lu & Romps approximation formula:
    # Apparent Temp = T + 0.33 * e - 0.70 * v_ms - 4.0
    v_ms = wind_speed_kmh / 3.6
    at = temperature_c + (0.33 * e) - (0.70 * v_ms) - 4.0
    return float(round(at, 2))

def calculate_wet_bulb_stull(temperature_c: float, relative_humidity: float) -> float:
    """
    Calculate Wet Bulb Temperature using Stull's empirical formula.
    Valid for T in [-20°C, 50°C] and RH in [5%, 99%].
    """
    T = temperature_c
    RH = relative_humidity

    tw = (T * np.arctan(0.151977 * np.sqrt(RH + 8.313659)) +
          np.arctan(T + RH) -
          np.arctan(RH - 1.676331) +
          0.00391838 * (RH ** 1.5) * np.arctan(0.023101 * RH) -
          4.686035)
    return float(round(tw, 2))

def calculate_heat_index_batch(temperatures: Union[List[float], np.ndarray], humidities: Union[List[float], np.ndarray]) -> np.ndarray:
    """
    Vectorized batch calculation of NWS Rothfusz Heat Index.
    """
    temps = np.asarray(temperatures, dtype=np.float64)
    rhs = np.asarray(humidities, dtype=np.float64)

    # Vectorized computation
    T = (temps * 9.0 / 5.0) + 32.0
    RH = rhs

    HI_simple = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (RH * 0.094))
    HI_full = (-42.379 +
               2.04901523 * T +
               10.14333127 * RH -
               0.22475541 * T * RH -
               0.00683783 * T * T -
               0.05481717 * RH * RH +
               0.00122874 * T * T * RH +
               0.00085282 * T * RH * RH -
               0.00000199 * T * T * RH * RH)

    HI_f = np.where(HI_simple < 80.0, HI_simple, HI_full)
    HI_c = (HI_f - 32.0) * 5.0 / 9.0
    return np.round(HI_c, 2)

def get_heat_risk_category(heat_index_c: float) -> str:
    """
    Categorize Heat Index in °C according to NOAA NWS risk bands.
    """
    if heat_index_c < 27.0:
        return "Normal"
    elif heat_index_c < 32.0:
        return "Caution"
    elif heat_index_c < 41.0:
        return "Extreme Caution"
    elif heat_index_c < 54.0:
        return "Danger"
    else:
        return "Extreme Danger"
