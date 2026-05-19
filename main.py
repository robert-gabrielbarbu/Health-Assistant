# main.py
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

from agent.agent import CoachAgent
from agent.agent_executor import CoachAgentExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Raised when a required environment variable is not set."""


@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=int(os.getenv("PORT", 8080)), type=int)
def main(host, port):
    """Start the Strava Coach A2A Agent server."""
    load_dotenv()

    required_env_vars = ["LITELLM_BASE_URL", "LITELLM_API_KEY"]
    for var in required_env_vars:
        if not os.getenv(var):
            logger.error(f"Required environment variable {var} is not set.")
            raise MissingAPIKeyError(f"{var} is not set.")

    logger.info("All required environment variables loaded.")

    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
    skill = AgentSkill(
        id="strava-coach",
        name="Strava Workout Coach",
        description=(
            "Analyses Strava training data and creates personalised weekly training plans. "
            "Fetches athlete profile, recent activities, and stats, then builds a science-based "
            "day-by-day plan with HR/power zone targets and coaching tips."
        ),
        tags=["strava", "fitness", "training", "running", "cycling", "triathlon"],
        examples=[
            "Create my training plan for next week",
            "Analyse my recent training load",
            "Am I overtraining?",
            "What should my long run be this weekend?",
        ],
    )

    agent_card = AgentCard(
        name="Strava Workout Coach",
        description=(
            "A personalised endurance sports coach that reads your Strava data "
            "and builds science-based weekly training plans."
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
    logger.info(f"Coach agent running at http://{host}:{port}/")
    logger.info(f"Agent card: http://{host}:{port}/.well-known/agent.json")
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
