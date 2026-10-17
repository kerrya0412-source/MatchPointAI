import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.app.services.azure_speech_service import AzureSpeechService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/speech",
    tags=["Speech"],
)

speech_service = AzureSpeechService()


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    style: str = Field(default="professional", pattern="^(professional|excited)$")


@router.post("/synthesize")
def synthesize_speech(request: SpeechRequest):
    try:
        audio = speech_service.synthesize(
            text=request.text,
            style=request.style,
        )

        return Response(
            content=audio,
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-store"},
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception:
        logger.exception("Azure Speech synthesis failed")
        raise HTTPException(
            status_code=503,
            detail="Speech synthesis is temporarily unavailable.",
        )
