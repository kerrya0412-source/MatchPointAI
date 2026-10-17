import os
import urllib.request
from xml.sax.saxutils import escape


class AzureSpeechService:
    VOICES = {
        "professional": {
            "name": "en-US-AndrewMultilingualNeural",
            "rate": "0%",
            "pitch": "0%",
        },
        "excited": {
            "name": "en-US-AdamMultilingualNeural",
            "rate": "+15%",
            "pitch": "+5%",
        },
    }

    def synthesize(self, text: str, style: str = "professional") -> bytes:
        key = os.getenv("MATCHPOINT_AZURE_SPEECH_KEY")
        region = os.getenv("MATCHPOINT_AZURE_SPEECH_REGION", "westus3")

        if not key:
            raise RuntimeError("Azure Speech key is not configured.")

        if style not in self.VOICES:
            raise ValueError("Unsupported commentary style.")

        voice = self.VOICES[style]

        # Give goal announcements a slower, more dramatic delivery.
        # Escape ordinary text before inserting trusted SSML markup.
        speech_text = escape(text)

        if style == "excited" and text.startswith("GOAL!!!"):
            remainder = escape(text[len("GOAL!!!"):].strip())
            speech_text = (
                '<prosody rate="-75%" pitch="+12%">GOAL!</prosody>'
                '<break time="250ms"/>'
                + remainder
            )

        ssml = f"""
<speak version="1.0"
       xmlns="http://www.w3.org/2001/10/synthesis"
       xml:lang="en-US">
    <voice name="{voice['name']}">
        <prosody rate="{voice['rate']}" pitch="{voice['pitch']}">
            {speech_text}
        </prosody>
    </voice>
</speak>
"""

        url = (
            f"https://{region}.tts.speech.microsoft.com"
            "/cognitiveservices/v1"
        )

        request = urllib.request.Request(
            url,
            data=ssml.encode("utf-8"),
            headers={
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                "User-Agent": "MatchPointAI",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()
