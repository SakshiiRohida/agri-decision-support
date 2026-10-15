
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.weather_service import get_weather
from app.crop_engine import load_crops, recommend_crops

app = FastAPI(
    title="Agri Decision Support API",
    description="Seasonal crop suitability and decision support",
    version="0.2.0",
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
            "Prototype results based on illustrative data; "
            "not validated agricultural advice."
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
        # Continue accepting the original names for testing.
        "Kharif": "Kharif",
        "Rabi": "Rabi",
        "Zaid": "Zaid",
    }

    if season not in season_mapping:
        raise HTTPException(
            status_code=400,
            detail="Season must be Monsoon, Winter, or Summer.",
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

    results = recommend_crops(
        season=internal_season,
        temperature=temperature,
        rainfall=None,
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
            "forecast_rainfall_mm": daily.get(
                "precipitation_sum", []
            ),
            "forecast_days": daily.get("time", []),
        },
        "top_recommendation": results[0] if results else None,
        "alternatives": results[1:],
        "notice": (
            "Prototype ranking based on current temperature "
            "and an illustrative crop catalogue. Rainfall, soil, "
            "water availability and regional crop calendars still "
            "need validation."
        ),
    }

