from fastapi import FastAPI
from backend.app.api.match_intelligence import router as match_intelligence_router

app = FastAPI(
    title="MatchPoint AI",
    description="Explainable AI-powered football match intelligence.",
    version="0.1.0",
)


app.include_router(match_intelligence_router)


@app.get("/")
def root():
    return {
        "name": "MatchPoint AI",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}

