from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.match_intelligence import router as match_intelligence_router

app = FastAPI(
    title="MatchPoint AI",
    description="Explainable AI-powered football match intelligence.",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5180",
        "http://127.0.0.1:5180",
        "https://orange-bay-09c579b10.4.azurestaticapps.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


