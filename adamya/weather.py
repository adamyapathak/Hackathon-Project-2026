"""Small client for live weather conditions from Open-Meteo."""

import httpx

from .schemas import Location, Weather

async def get_weather(location: Location) -> Weather:
    """Fetch current conditions; return a safe unavailable response on failure."""
    params = {
        "latitude": location.latitude, "longitude": location.longitude,
        "current": "temperature_2m,relative_humidity_2m,cloud_cover,wind_speed_10m",
        "hourly": "precipitation_probability", "forecast_days": 1,
        "timezone": location.timezone,
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            data = response.json()
        current = data["current"]
        precipitation = data.get("hourly", {}).get("precipitation_probability", [None])[0]
        cloud = current.get("cloud_cover")
        summary = "Excellent visibility" if cloud is not None and cloud < 20 else "Partly cloudy" if cloud is not None and cloud < 60 else "Cloudy"
        return Weather(
            available=True, temperature_c=current.get("temperature_2m"),
            cloud_cover_percent=cloud, humidity_percent=current.get("relative_humidity_2m"),
            wind_speed_kmh=current.get("wind_speed_10m"),
            precipitation_probability_percent=precipitation, summary=summary,
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return Weather(available=False)

