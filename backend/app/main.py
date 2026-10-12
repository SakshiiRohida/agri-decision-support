
from fastapi import FastAPI

app = FastAPI(
    title="Agri Decision Support API",
    description="Agricultural crop suitability and decision support",
    version="0.1.0",
)


@app.get("/")
def home():
    return {
        "message": "Agri Decision Support API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
