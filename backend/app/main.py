from fastapi import FastAPI

app = FastAPI(
    title="MatchPoint AI",
    description="Explainable AI-powered football match intelligence.",
    version="0.1.0",
)


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
