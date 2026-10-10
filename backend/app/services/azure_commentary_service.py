"""Azure GPT-5-mini commentary integration for MatchPoint AI."""

import logging
import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

logger = logging.getLogger(__name__)

AZURE_ENDPOINT = os.getenv(
    "MATCHPOINT_AZURE_ENDPOINT",
    "https://kerrya0412-7451-resource.services.ai.azure.com/openai/v1",
)

AZURE_DEPLOYMENT = os.getenv(
    "MATCHPOINT_AZURE_DEPLOYMENT",
    "gpt-5-mini-1",
)


class AzureCommentaryService:
    """Generate evidence-grounded commentary through Microsoft Foundry."""

    def __init__(self):
        self.client = None
        self._cache = {}

    def generate_cached(
        self,
        facts: str,
        audience: str,
    ) -> str | None:
        key = (facts, audience)

        if key in self._cache:
            return self._cache[key]

        commentary = self.generate(facts, audience)

        if commentary:
            self._cache[key] = commentary

        return commentary

    def _get_client(self):
        if self.client is None:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://ai.azure.com/.default",
            )

            self.client = OpenAI(
                base_url=AZURE_ENDPOINT,
                api_key=token_provider,
                timeout=15.0,
                max_retries=0,
            )

        return self.client

    def generate(self, facts: str, audience: str) -> str | None:
        if not facts.strip():
            return None

        try:
            response = self._get_client().responses.create(
                model=AZURE_DEPLOYMENT,
                reasoning={"effort": "minimal"},
                instructions=(
                    "You are MatchPoint AI, a professional football "
                    "commentator. Write one concise sentence for the "
                    "requested audience. Use only the supplied facts. "
                    "Do not invent players, goals, shots, causes, "
                    "or other match details."
                ),
                input=(
                    f"Audience: {audience}\n"
                    f"Verified match facts:\n{facts}"
                ),
                max_output_tokens=300,
            )

            if response.status != "completed":
                return None

            return response.output_text.strip() or None

        except Exception:
            logger.exception("Azure commentary request failed")
            return None
