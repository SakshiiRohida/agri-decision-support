
import httpx


WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


async def get_weather(latitude: float, longitude: float):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "wind_speed_10m",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
        ],
        "forecast_days": 3,
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(WEATHER_URL, params=params)
        response.raise_for_status()
        data = response.json()

    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "current": data.get("current", {}),
        "daily": data.get("daily", {}),
        "source": "Open-Meteo",
        "notice": (
            "Weather values are API-provided estimates or observations "
            "as labelled by the provider, not farm sensor measurements."
        ),
    }
