"""Pydantic request and response models used by the frontend contract."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

class Location(BaseModel):
    """A geographic observing location."""

    name: str = "Clemson University"
    latitude: float = Field(34.6787, ge=-90, le=90)
    longitude: float = Field(-82.8399, ge=-180, le=180)
    timezone: str = "America/New_York"


class SkyRequest(BaseModel):
    """Optional location/time input for a sky calculation."""

    location: Location = Field(default_factory=Location)
    datetime_utc: datetime | None = None


class SkyObject(BaseModel):
    name: str
    object_type: Literal["star", "planet", "moon", "sun"]
    above_horizon: bool
    visible: bool
    altitude_deg: float
    azimuth_deg: float
    magnitude: float | None = None
    direction: str
    best_for: str
    educational_fact: str


class Weather(BaseModel):
    """Current observing conditions returned by Open-Meteo."""

    available: bool
    temperature_c: float | None = None
    cloud_cover_percent: float | None = None
    humidity_percent: float | None = None
    wind_speed_kmh: float | None = None
    precipitation_probability_percent: float | None = None
    summary: str = "Weather data unavailable"


class SkyResponse(BaseModel):
    """Complete state needed to render the sky dashboard."""

    location: Location
    observed_at: datetime
    sunset: datetime
    sunrise_next: datetime
    darkness_start: datetime
    moon_phase: str
    moon_illumination_percent: float
    objects: list[SkyObject]
    highlights: list[SkyObject]
    weather: Weather
    observing_score: int
    data_sources: list[str]


class ExplainRequest(BaseModel):
    object_name: str = Field(min_length=1, max_length=80)
    audience_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    sky_context: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    sky_context: dict[str, Any] = Field(default_factory=dict)


class TextResponse(BaseModel):
    text: str
    powered_by: str


class MissionResponse(BaseModel):
    title: str
    objective: str
    hint: str
    learning_goal: str
    xp: int

