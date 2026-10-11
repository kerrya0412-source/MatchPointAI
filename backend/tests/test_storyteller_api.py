from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


@pytest.mark.parametrize("audience", ["analyst", "broadcaster", "fan"])
@pytest.mark.parametrize("seconds", [0, 180, 600])
def test_storyteller_audience_and_evidence(audience, seconds):
    with patch(
        "backend.app.api.match_intelligence.azure_commentary.generate_cached",
        return_value=None,
    ) as mock_azure:
        response = client.get(
            "/api/match/storyteller",
            params={"seconds": seconds, "audience": audience},
        )

    assert response.status_code == 200

    data = response.json()
    narrative = data["narrative"]

    assert data["playback_seconds"] == seconds
    assert data["audience"] == audience
    assert narrative["audience"] == audience
    assert narrative["headline"]
    assert narrative["narrative"]
    assert data["commentary_source"] == "deterministic"
    assert data["ai_commentary_validated"] is False

    for key in ("match_validation", "tactical_validation"):
        validation = data[key]
        assert validation["missing_event_ids"] == []
        assert (
            validation["verified_references"]
            == validation["total_references"]
        )

    if seconds == 0:
        assert narrative["evidence_verified"] is False

    # Mocking prevents real Azure calls, even when goals are present.
    assert mock_azure.call_count <= 1


def test_storyteller_rejects_unsupported_audience():
    response = client.get(
        "/api/match/storyteller",
        params={"audience": "unsupported"},
    )

    assert response.status_code == 422