from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

T = TypeVar("T")

class KloudtrackResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Request processed successfully"
    data: T

class StationInfo(BaseModel):
    id: str = Field(..., description="Station hashid e.g. 'Rjz2dbXW'")
    name: str = Field(..., description="Human-readable station name")
    latitude: float
    longitude: float
    elevation: float = 0.0
    organizationId: Optional[Any] = Field("org_default", description="Organization ID or name")
    isActive: bool = Field(True, description="Whether station is actively reporting live telemetry")
    status: str = Field("active", description="Station operational status e.g., 'active' or 'offline'")
    source: str = Field("Kloudtech API", description="Telemetry data ingestion source")

class WeatherStationApiReading(BaseModel):
    id: int = Field(..., description="Numeric telemetry record ID")
    recordedAt: str = Field(..., description="ISO 8601 timestamp when reading was recorded")
    createdAt: Optional[str] = Field(None, description="ISO 8601 timestamp when reading was ingested")
    temperature: Optional[float] = Field(None, description="Ambient air temperature in °C")
    humidity: Optional[float] = Field(None, description="Relative humidity percentage (0-100)")
    dewPoint: Optional[float] = Field(None, description="Dew point temperature in °C")
    apparentTemperature: Optional[float] = Field(None, description="Apparent temperature in °C")
    heatIndex: Optional[float] = Field(None, description="Calculated Heat Index in °C")
    windSpeed: Optional[float] = Field(None, description="Wind speed")
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
