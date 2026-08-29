"""FastAPI entry point for the Live Night Sky backend."""

from functools import lru_cache

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .astronomy import AstronomyEngine
from .config import get_settings
from .gemini import GeminiTutor
from .schemas import (
    ChatRequest,
    ExplainRequest,
    MissionResponse,
    SkyRequest,
    SkyResponse,
    TextResponse,
)
from .weather import get_weather

settings = get_settings()
app = FastAPI(title="Live Night Sky API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@lru_cache
def astronomy_engine() -> AstronomyEngine:
    """Create one reusable ephemeris engine for the server process."""
    return AstronomyEngine(settings.skyfield_data_dir)


@lru_cache
def gemini_tutor() -> GeminiTutor:
    """Create one reusable Gemini client for the server process."""
    return GeminiTutor(settings)


@app.get("/api/health")
def health() -> dict:
    """Deployment/readiness check for the frontend or hosting service."""
    return {"status": "ok", "gemini_configured": gemini_tutor().enabled}


@app.post("/api/sky", response_model=SkyResponse)
async def sky(request: SkyRequest) -> SkyResponse:
    """Return calculated sky positions plus live observing conditions."""
    location = request.location
    calculated = astronomy_engine().calculate(location, request.datetime_utc)
    weather = await get_weather(location)
    cloud_penalty = int(weather.cloud_cover_percent or 0) // 4 if weather.available else 25
    moon_penalty = 15 if calculated["moon_illumination_percent"] > 85 else 0
    score = max(0, min(100, 100 - cloud_penalty - moon_penalty))
    return SkyResponse(
        location=location, **calculated, weather=weather, observing_score=score,
        data_sources=["Skyfield/JPL DE421 ephemeris", "Open-Meteo current weather"],
    )


@app.post("/api/explain", response_model=TextResponse)
def explain(request: ExplainRequest) -> TextResponse:
    """Generate a grounded explanation for an object selected on the sky map."""
    tutor = gemini_tutor()
    return TextResponse(
        text=tutor.explain(request.object_name, request.audience_level, request.sky_context),
        powered_by="Gemini" if tutor.enabled else "local fallback",
    )


@app.post("/api/chat", response_model=TextResponse)
def chat(request: ChatRequest) -> TextResponse:
    """Answer an astronomy question using the current sky context."""
    tutor = gemini_tutor()
    return TextResponse(
        text=tutor.chat(request.message, request.sky_context),
        powered_by="Gemini" if tutor.enabled else "local fallback",
    )


@app.get(
    "/api/mission",
    response_model=MissionResponse,
)
def mission() -> MissionResponse:
    return MissionResponse(
        title="Jupiter Tracker",
        objective=(
            "Watch Jupiter for 10 minutes "
            "and determine whether it is rising or setting."
        ),
        hint=(
            "Record Jupiter's altitude now, "
            "then compare it again after 10 minutes."
        ),
        learning_goal=(
            "Use apparent motion to understand "
            "Earth's rotation."
        ),
        xp=100,
    )

