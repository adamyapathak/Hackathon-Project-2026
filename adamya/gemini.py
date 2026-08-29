"""Gemini-powered explanations and astronomy tutoring."""

from google import genai

from .config import Settings


class GeminiTutor:
    """Thin service wrapper around the Gemini API."""

    def __init__(self, settings: Settings):
        self.enabled = bool(
            settings.gemini_api_key
        )
        self.model = settings.gemini_model

        self.client = (
            genai.Client(
                api_key=settings.gemini_api_key
            )
            if self.enabled
            else None
        )

    def _generate(
        self,
        prompt: str,
    ) -> str:
        """Generate text while failing gracefully if Gemini is unavailable."""

        if not self.client:
            return (
                "Gemini is not configured. "
                "Add GEMINI_API_KEY to the backend .env file."
            )

        try:
            response = (
                self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
            )

            return (
                response.text
                or "I could not generate an explanation right now."
            )

        except Exception:
            return (
                "Gemini is temporarily unavailable. "
                "The live astronomy data is still available."
            )

    def explain(
        self,
        object_name: str,
        level: str,
        context: dict,
    ) -> str:
        """Explain a selected object using verified backend measurements."""

        prompt = f"""You are the astronomy tutor inside Clemson SkyGuide.

Teach a {level} astronomy learner about {object_name}.

The backend calculated this verified live observing context:
{context}

Important rules:
- Never invent or change altitude, azimuth, direction, weather, or timing.
- Use the verified measurements exactly as provided.
- Explain what the user is looking at.
- Explain why it is interesting.
- Explain what the user can look for tonight.
- Teach one simple astronomy concept.
- Finish with one short observation challenge.
- Use plain language.
- Keep the answer under 150 words.
- Do not use tables.

Your response should feel like a helpful astronomy teacher, not a generic chatbot.
"""

        return self._generate(prompt)

    def chat(
        self,
        message: str,
        context: dict,
    ) -> str:
        """Answer a user's astronomy question using verified sky context."""

        prompt = f"""You are the astronomy tutor inside Clemson SkyGuide.

Answer the user's question using the verified live sky context below.

Verified sky context:
{context}

Rules:
- Do not invent current astronomical measurements.
- Do not change any measurements supplied by the backend.
- If the context does not contain enough information, say so clearly.
- Explain concepts in simple educational language.
- Keep the answer under 180 words.
- Include one practical observation suggestion.

User question:
{message}
"""

        return self._generate(prompt)