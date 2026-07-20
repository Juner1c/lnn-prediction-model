import unittest
import numpy as np
from src.data.heat_index import (
    calculate_heat_index,
    calculate_apparent_temp_lu_romps,
    calculate_wet_bulb_stull,
    calculate_heat_index_batch,
    get_heat_risk_category
)

class TestHeatIndex(unittest.TestCase):
    def test_heat_index_baseline(self):
        # 27°C and 40% RH -> ~27°C
        hi = calculate_heat_index(27.0, 40.0)
        self.assertTrue(26.0 <= hi <= 28.0)

    def test_heat_index_extreme_caution(self):
        # 32°C and 70% RH -> ~40-44°C
        hi = calculate_heat_index(32.0, 70.0)
        self.assertTrue(39.0 <= hi <= 44.0)

    def test_heat_index_danger(self):
        # 35°C and 80% RH -> Danger level (>48°C)
        hi = calculate_heat_index(35.0, 80.0)
        self.assertTrue(hi >= 48.0)

    def test_lu_romps_benchmark(self):
        # 30°C temp / 25°C dew point (75% RH) -> Apparent Temp 36.45°C
        at = calculate_apparent_temp_lu_romps(30.0, 25.0, wind_speed_kmh=0.0)
        self.assertTrue(35.0 <= at <= 37.5)

    def test_stull_wet_bulb(self):
        # 30°C and 70% RH -> Wet bulb ~25.5°C
        tw = calculate_wet_bulb_stull(30.0, 70.0)
        self.assertTrue(24.0 <= tw <= 27.0)

    def test_heat_index_batch(self):
        temps = [27.0, 32.0, 35.0]
        rhs = [40.0, 70.0, 80.0]
        results = calculate_heat_index_batch(temps, rhs)
        self.assertEqual(len(results), 3)
        self.assertTrue(results[1] >= 39.0)

    def test_heat_risk_category(self):
        self.assertEqual(get_heat_risk_category(25.0), "Normal")
        self.assertEqual(get_heat_risk_category(30.0), "Caution")
        self.assertEqual(get_heat_risk_category(35.0), "Extreme Caution")
        self.assertEqual(get_heat_risk_category(45.0), "Danger")
        self.assertEqual(get_heat_risk_category(55.0), "Extreme Danger")

if __name__ == "__main__":
    unittest.main()
