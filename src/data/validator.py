from typing import Dict, Any, Optional
from pydantic import BaseModel

class TelemetryValidationResult(BaseModel):
    is_valid: bool
    quality_flag: str  # "GOOD", "OUT_OF_BOUNDS", "MISSING_FIELD"
    message: str
    cleaned_data: Dict[str, Any]

class TelemetryValidator:
    """
    Physical bounds validator for weather telemetry readings.
    Guards LNN/GNN pipelines against sensor spikes, physical impossibilities, and missing values.
    """
    TEMP_MIN = -10.0
    TEMP_MAX = 60.0
    RH_MIN = 0.0
    RH_MAX = 100.0
    WIND_MAX = 150.0

    @classmethod
    def validate_reading(cls, reading: Dict[str, Any]) -> TelemetryValidationResult:
        cleaned = dict(reading)
        
        # Check required fields
        temp = reading.get("temperature")
        rh = reading.get("humidity")

        if temp is None or rh is None:
            return TelemetryValidationResult(
                is_valid=False,
                quality_flag="MISSING_FIELD",
                message="Temperature and humidity fields are mandatory",
                cleaned_data=cleaned
            )

        try:
            temp_f = float(temp)
            rh_f = float(rh)
        except (ValueError, TypeError):
            return TelemetryValidationResult(
                is_valid=False,
                quality_flag="OUT_OF_BOUNDS",
                message="Non-numeric values detected in telemetry reading",
                cleaned_data=cleaned
            )

        # Check physical ranges
        if not (cls.TEMP_MIN <= temp_f <= cls.TEMP_MAX):
            return TelemetryValidationResult(
                is_valid=False,
                quality_flag="OUT_OF_BOUNDS",
                message=f"Temperature {temp_f}°C out of valid physical range [{cls.TEMP_MIN}, {cls.TEMP_MAX}]",
                cleaned_data=cleaned
            )

        if not (cls.RH_MIN <= rh_f <= cls.RH_MAX):
            return TelemetryValidationResult(
                is_valid=False,
                quality_flag="OUT_OF_BOUNDS",
                message=f"Relative humidity {rh_f}% out of valid physical range [{cls.RH_MIN}, {cls.RH_MAX}]",
                cleaned_data=cleaned
            )

        wind = reading.get("windSpeed")
        if wind is not None:
            try:
                wind_f = float(wind)
                if wind_f < 0 or wind_f > cls.WIND_MAX:
                    return TelemetryValidationResult(
                        is_valid=False,
                        quality_flag="OUT_OF_BOUNDS",
                        message=f"Wind speed {wind_f} out of valid range [0, {cls.WIND_MAX}]",
                        cleaned_data=cleaned
                    )
            except (ValueError, TypeError):
                pass

        return TelemetryValidationResult(
            is_valid=True,
            quality_flag="GOOD",
            message="Telemetry reading passed all physical range validations",
            cleaned_data=cleaned
        )
