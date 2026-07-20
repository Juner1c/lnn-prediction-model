from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class KloudtrackResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Request processed successfully"
    data: T

class StationInfo(BaseModel):
    id: str = Field(..., description="Station hashid e.g., 'st_123abc' or numeric string")
    name: str = Field(..., description="Human-readable station name")
    latitude: float
    longitude: float
    elevation: float
    organizationId: str = "org_default"

class WeatherStationApiReading(BaseModel):
    id: int = Field(..., description="Numeric telemetry record ID")
    recordedAt: str = Field(..., description="ISO 8601 timestamp when reading was recorded")
    createdAt: str = Field(..., description="ISO 8601 timestamp when reading was ingested")
    temperature: float = Field(..., description="Ambient air temperature in °C")
    humidity: float = Field(..., description="Relative humidity percentage (0-100)")
    dewPoint: Optional[float] = Field(None, description="Dew point temperature in °C")
    apparentTemperature: Optional[float] = Field(None, description="Apparent temperature in °C")
    heatIndex: Optional[float] = Field(None, description="Calculated Heat Index in °C")
    windSpeed: Optional[float] = Field(None, description="Wind speed in km/h or m/s")
    windDirection: Optional[float] = Field(None, description="Wind direction in degrees (0-360)")
    pressure: Optional[float] = Field(None, description="Atmospheric surface pressure in hPa")

class VariableReading(BaseModel):
    id: int
    recordedAt: str
    createdAt: str
    value: float

class WeatherStationDashboardEntry(BaseModel):
    station: StationInfo
    telemetry: Optional[WeatherStationApiReading] = None

class HeatIndexCalculationRequest(BaseModel):
    temperature: float = Field(..., description="Dry-bulb temperature in °C")
    humidity: float = Field(..., description="Relative humidity percentage (0-100)")

class HeatIndexCalculationResponse(BaseModel):
    temperature: float
    humidity: float
    heatIndex: float
    riskLevel: str
