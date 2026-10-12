
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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
