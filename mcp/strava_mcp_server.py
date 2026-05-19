"""Strava MCP server — exposes Strava athlete data as MCP tools via FastMCP.

Run modes:
  stdio (default, for MCP clients):  python strava_mcp_server.py
  HTTP  (for remote clients):        python strava_mcp_server.py --http
"""

import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from strava_tools import (
    get_activity_detail as _get_activity_detail,
    get_athlete_profile as _get_athlete_profile,
    get_athlete_stats as _get_athlete_stats,
    get_last_activity as _get_last_activity,
    get_recent_activities as _get_recent_activities,
)

load_dotenv()

mcp = FastMCP(
    "Strava Coach",
    instructions="Strava athlete data tools for training load analysis and plan generation.",
)


@mcp.tool()
def get_athlete_profile() -> dict:
    """Retrieve the authenticated Strava athlete's profile.

    Returns name, weight, FTP, sex, and measurement preferences.
    """
    return _get_athlete_profile()


@mcp.tool()
def get_last_activity() -> dict:
    """Fetch the single most recent Strava activity with no time-window restriction.

    Use this when the user asks about their latest or last activity.
    Returns distance, duration, heart rate, power, and suffer score.
    """
    return _get_last_activity()


@mcp.tool()
def get_recent_activities(weeks: int = 4, per_page: int = 30) -> list:
    """Fetch recent Strava activities.

    Args:
        weeks: Number of weeks of history to retrieve (default 4).
        per_page: Maximum number of activities to return (default 30, max 200).

    Returns a list of activities with distance, duration, heart rate, power, and suffer score.
    """
    return _get_recent_activities(weeks=weeks, per_page=per_page)


@mcp.tool()
def get_activity_detail(activity_id: int) -> dict:
    """Get detailed information for a single Strava activity.

    Args:
        activity_id: The numeric Strava activity ID.

    Returns splits, laps, best efforts, perceived exertion, and power data.
    """
    return _get_activity_detail(activity_id)


@mcp.tool()
def get_athlete_stats() -> dict:
    """Retrieve all-time, year-to-date, and recent totals for the athlete.

    Returns aggregated run, ride, and swim stats (distance, time, elevation).
    """
    return _get_athlete_stats()


if __name__ == "__main__":
    transport = "streamable-http" if "--http" in sys.argv else "stdio"
    mcp.run(transport=transport)
