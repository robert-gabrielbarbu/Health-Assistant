# main.py
import io
import logging
import os

import click
import httpx
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
from pypdf import PdfReader
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from agent.agent import CoachAgent
from agent.agent_executor import CoachAgentExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Raised when a required environment variable is not set."""


async def parse_pdf(request: Request) -> JSONResponse:
    """Accept a PDF file upload and return extracted plain text."""
    form = await request.form()
    upload = form.get("file")
    if not upload:
        return JSONResponse({"error": "No file provided"}, status_code=400)
    contents = await upload.read()
    try:
        reader = PdfReader(io.BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return JSONResponse({"text": text})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def nearby_doctors(request: Request) -> JSONResponse:
    """Proxy Google Maps Places API to find nearby doctors by specialty."""
    params = dict(request.query_params)
    lat = params.get("lat")
    lng = params.get("lng")
    specialty = params.get("specialty", "doctor")
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "GOOGLE_MAPS_API_KEY not set"}, status_code=500)
    if not lat or not lng:
        return JSONResponse({"error": "lat and lng required"}, status_code=400)
    keyword = specialty if specialty else "doctor"
    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}&radius=5000&type=doctor"
        f"&keyword={keyword}&key={api_key}"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    data = resp.json()
    places = []
    for p in data.get("results", [])[:8]:
        places.append({
            "name": p.get("name"),
            "address": p.get("vicinity"),
            "rating": p.get("rating"),
            "user_ratings_total": p.get("user_ratings_total"),
            "open_now": (p.get("opening_hours") or {}).get("open_now"),
            "place_id": p.get("place_id"),
        })
    return JSONResponse({"places": places, "status": data.get("status")})


async def strava_stats(request: Request) -> JSONResponse:
    """Return Strava stats summary for the dashboard panel."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp"))
        from strava_tools import get_last_activity, get_recent_activities, get_athlete_stats
        last = get_last_activity()
        recent = get_recent_activities(weeks=4, per_page=30)
        stats = get_athlete_stats()

        # Weekly hours for the last 4 weeks
        from datetime import datetime, timedelta
        weekly_hours = {}
        for a in recent:
            date = datetime.fromisoformat(a["start_date_local"].replace("Z", ""))
            week = date.strftime("W%W")
            weekly_hours[week] = round(weekly_hours.get(week, 0) + a.get("moving_time_min", 0) / 60, 1)

        # Suggested training based on recent load
        total_km = sum(a.get("distance_km", 0) for a in recent)
        avg_hr_values = [a["average_heartrate"] for a in recent if a.get("average_heartrate")]
        avg_hr = round(sum(avg_hr_values) / len(avg_hr_values)) if avg_hr_values else None

        if total_km > 100:
            suggestion = "Recovery week — keep intensity low"
        elif total_km > 60:
            suggestion = "Maintain current load, add one tempo run"
        else:
            suggestion = "Build phase — increase volume gradually"

        return JSONResponse({
            "last_activity": last,
            "weekly_hours": weekly_hours,
            "monthly_km": round(total_km, 1),
            "avg_hr": avg_hr,
            "suggestion": suggestion,
            "recent_run": stats.get("recent_run", {}),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)



@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=int(os.getenv("PORT", 8080)), type=int)
def main(host, port):
    """Start the Health Assistant A2A Agent server."""
    load_dotenv()

    required_env_vars = ["LITELLM_BASE_URL", "LITELLM_API_KEY"]
    for var in required_env_vars:
        if not os.getenv(var):
            logger.error(f"Required environment variable {var} is not set.")
            raise MissingAPIKeyError(f"{var} is not set.")

    logger.info("All required environment variables loaded.")

    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
    skill = AgentSkill(
        id="health-assistant",
        name="Health Assistant",
        description=(
            "Analyses your Strava workouts and Withings biometric data (weight, sleep, "
            "heart rate, blood pressure, SpO2) to give personalised health insights and "
            "training recommendations."
        ),
        tags=["health", "fitness", "strava", "withings", "sleep", "heart rate"],
        examples=[
            "How was my sleep this week?",
            "Create my training plan for next week",
            "What is my current weight trend?",
            "Analyse my recovery based on last night's sleep",
        ],
    )

    agent_card = AgentCard(
        name="Health Assistant",
        description=(
            "A personal health assistant combining Strava workout data with Withings "
            "biometrics to provide holistic health insights and training guidance."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=CoachAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=CoachAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    httpx_client = httpx.AsyncClient()
    push_notifier = InMemoryPushNotifier(httpx_client=httpx_client)

    request_handler = DefaultRequestHandler(
        agent_executor=CoachAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_notifier=push_notifier,
    )

    server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
    app = server.build()
    app.routes.append(Route("/parse-pdf", parse_pdf, methods=["POST"]))
    app.routes.append(Route("/strava-stats", strava_stats, methods=["GET"]))
    app.routes.append(Route("/nearby-doctors", nearby_doctors, methods=["GET"]))
    logger.info(f"Health Assistant agent running at http://{host}:{port}/")
    logger.info(f"Agent card: http://{host}:{port}/.well-known/agent.json")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
