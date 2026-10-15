
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.weather_service import get_weather
from app.crop_engine import (
    load_crops,
    recommend_crops,
    recommend_from_weather,
    build_weather_advisories,
)


app = FastAPI(
    title="Agri Decision Support API",
    description="Weather-based crop recommendations and "
                "agricultural decision support",
    version="0.3.0",
)


class RecommendationRequest(BaseModel):
    season: str
    temperature: float = Field(ge=-10, le=60)
    rainfall: float = Field(ge=0, le=10000)


@app.get("/")
def home():
    return {
        "message": "Agri Decision Support API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/crops")
def get_crops():
    return {"crops": load_crops()}


@app.post("/recommend")
def get_recommendations(request: RecommendationRequest):
    if request.season not in {"Kharif", "Rabi", "Zaid"}:
        raise HTTPException(
            status_code=400,
            detail="Season must be Kharif, Rabi, or Zaid.",
        )

    results = recommend_crops(
        season=request.season,
        temperature=request.temperature,
        rainfall=request.rainfall,
    )

    return {
        "season": request.season,
        "results": results,
        "notice": (
            "Prototype results use illustrative catalogue "
            "ranges. They are not validated agricultural advice."
        ),
    }


@app.get("/weather")
async def weather(latitude: float, longitude: float):
    try:
        return await get_weather(latitude, longitude)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Weather service is currently unavailable.",
        )


@app.get("/recommend-by-location")
async def recommend_by_location(
    latitude: float,
    longitude: float,
    season: str,
):
    season_mapping = {
        "Monsoon": "Kharif",
        "Winter": "Rabi",
        "Summer": "Zaid",
        "Kharif": "Kharif",
        "Rabi": "Rabi",
        "Zaid": "Zaid",
    }

    if season not in season_mapping:
        raise HTTPException(
            status_code=400,
            detail=(
                "Season must be Monsoon, Winter, Summer, "
                "Kharif, Rabi, or Zaid."
            ),
        )

    try:
        weather_data = await get_weather(latitude, longitude)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Weather service is currently unavailable.",
        )

    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    temperature = current.get("temperature_2m")

    if temperature is None:
        raise HTTPException(
            status_code=502,
            detail="Current temperature is unavailable.",
        )

    internal_season = season_mapping[season]

    try:
        results = recommend_from_weather(
            season=internal_season,
            weather_data=weather_data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    return {
        "location": weather_data["location"],
        "season": season,
        "agricultural_season_code": internal_season,
        "weather": {
            "temperature_c": temperature,
            "humidity_percent": current.get(
                "relative_humidity_2m"
            ),
            "apparent_temperature_c": current.get(
                "apparent_temperature"
            ),
            "current_rain_mm": current.get("rain"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "forecast_rainfall_mm": daily.get(
                "precipitation_sum", []
            ),
            "forecast_rain_probability_percent": daily.get(
                "precipitation_probability_max", []
            ),
            "forecast_days": daily.get("time", []),
        },
        "weather_advisories": build_weather_advisories(
            weather_data
        ),
        "top_recommendation": results[0] if results else None,
        "alternatives": results[1:],
        "ranking_method": (
            "Preliminary temperature-range heuristic using "
            "current and forecast temperatures and a season filter. "
            "It does not use the trained Random Forest model."
        ),
        "notice": (
            "The crop catalogue contains illustrative ranges. "
            "Soil nutrients, soil pH, irrigation, seasonal rainfall "
            "suitability and regional crop calendars have not been "
            "validated. These suggestions are experimental and "
            "should not be treated as farming advice."
        ),
    }
