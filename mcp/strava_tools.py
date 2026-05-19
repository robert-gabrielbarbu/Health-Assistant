"""Strava API tools for retrieving athlete activities and stats."""

import os
import time
import requests
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv, set_key

load_dotenv()

STRAVA_API_BASE = "https://www.strava.com/api/v3"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
_ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")

_cached_token: str = ""
_cached_expires_at: float = 0.0


def _auth_headers() -> dict:
    global _cached_token, _cached_expires_at

    if _cached_token and time.time() < _cached_expires_at - 60:
        return {"Authorization": f"Bearer {_cached_token}"}

    # Try refresh-token flow first (long-lived, preferred)
    client_id = os.getenv("STRAVA_CLIENT_ID", "")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET", "")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN", "")

    if client_id and client_secret and refresh_token:
        resp = requests.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        _cached_token = data["access_token"]
        _cached_expires_at = float(data["expires_at"])
        # Persist the (possibly rotated) refresh token back to .env
        new_refresh = data.get("refresh_token", refresh_token)
        if new_refresh != refresh_token:
            set_key(_ENV_FILE, "STRAVA_REFRESH_TOKEN", new_refresh)
            os.environ["STRAVA_REFRESH_TOKEN"] = new_refresh
        return {"Authorization": f"Bearer {_cached_token}"}

    # Fall back to a static access token (expires in ~6 h)
    access_token = os.getenv("STRAVA_ACCESS_TOKEN", "")
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}

    raise ValueError(
        "Strava auth not configured. Set STRAVA_REFRESH_TOKEN (recommended) "
        "or STRAVA_ACCESS_TOKEN in your .env file."
    )


def get_athlete_profile() -> dict:
    """Return the authenticated athlete's profile."""
    resp = requests.get(f"{STRAVA_API_BASE}/athlete", headers=_auth_headers(), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "id": data.get("id"),
        "firstname": data.get("firstname"),
        "lastname": data.get("lastname"),
        "sex": data.get("sex"),
        "weight": data.get("weight"),
        "ftp": data.get("ftp"),
        "measurement_preference": data.get("measurement_preference"),
    }


def get_last_activity() -> dict:
    """Return the single most recent Strava activity with no time-window restriction."""
    params = {"per_page": 1, "page": 1}
    resp = requests.get(
        f"{STRAVA_API_BASE}/athlete/activities",
        headers=_auth_headers(),
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    activities = resp.json()
    if not activities:
        return {}
    a = activities[0]
    return {
        "id": a.get("id"),
        "name": a.get("name"),
        "type": a.get("type"),
        "sport_type": a.get("sport_type"),
        "start_date_local": a.get("start_date_local"),
        "distance_km": round(a.get("distance", 0) / 1000, 2),
        "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
        "total_elevation_gain_m": a.get("total_elevation_gain"),
        "average_speed_ms": a.get("average_speed"),
        "average_heartrate": a.get("average_heartrate"),
        "max_heartrate": a.get("max_heartrate"),
        "average_watts": a.get("average_watts"),
        "kilojoules": a.get("kilojoules"),
        "suffer_score": a.get("suffer_score"),
        "kudos_count": a.get("kudos_count"),
        "achievement_count": a.get("achievement_count"),
        "pr_count": a.get("pr_count"),
    }


def get_recent_activities(weeks: int = 4, per_page: int = 30) -> list[dict]:
    """Return activities from the past *weeks* weeks (max per_page items)."""
    after = int((datetime.utcnow() - timedelta(weeks=weeks)).timestamp())
    params = {"after": after, "per_page": per_page, "page": 1}
    resp = requests.get(
        f"{STRAVA_API_BASE}/athlete/activities",
        headers=_auth_headers(),
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    activities = []
    for a in resp.json():
        activities.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "type": a.get("type"),
            "sport_type": a.get("sport_type"),
            "start_date_local": a.get("start_date_local"),
            "distance_m": a.get("distance"),
            "distance_km": round(a.get("distance", 0) / 1000, 2),
            "moving_time_s": a.get("moving_time"),
            "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
            "elapsed_time_s": a.get("elapsed_time"),
            "total_elevation_gain_m": a.get("total_elevation_gain"),
            "average_speed_ms": a.get("average_speed"),
            "max_speed_ms": a.get("max_speed"),
            "average_heartrate": a.get("average_heartrate"),
            "max_heartrate": a.get("max_heartrate"),
            "average_watts": a.get("average_watts"),
            "kilojoules": a.get("kilojoules"),
            "suffer_score": a.get("suffer_score"),
            "kudos_count": a.get("kudos_count"),
            "achievement_count": a.get("achievement_count"),
            "pr_count": a.get("pr_count"),
        })
    return activities


def get_activity_detail(activity_id: int) -> dict:
    """Return detailed information for a single activity."""
    resp = requests.get(
        f"{STRAVA_API_BASE}/activities/{activity_id}",
        headers=_auth_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    a = resp.json()
    return {
        "id": a.get("id"),
        "name": a.get("name"),
        "description": a.get("description"),
        "type": a.get("type"),
        "sport_type": a.get("sport_type"),
        "start_date_local": a.get("start_date_local"),
        "distance_km": round(a.get("distance", 0) / 1000, 2),
        "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
        "total_elevation_gain_m": a.get("total_elevation_gain"),
        "average_speed_ms": a.get("average_speed"),
        "max_speed_ms": a.get("max_speed"),
        "average_heartrate": a.get("average_heartrate"),
        "max_heartrate": a.get("max_heartrate"),
        "average_watts": a.get("average_watts"),
        "weighted_average_watts": a.get("weighted_average_watts"),
        "max_watts": a.get("max_watts"),
        "kilojoules": a.get("kilojoules"),
        "suffer_score": a.get("suffer_score"),
        "perceived_exertion": a.get("perceived_exertion"),
        "splits_metric": a.get("splits_metric", []),
        "best_efforts": [
            {
                "name": e.get("name"),
                "distance_m": e.get("distance"),
                "elapsed_time_s": e.get("elapsed_time"),
            }
            for e in (a.get("best_efforts") or [])
        ],
        "laps": [
            {
                "lap_index": l.get("lap_index"),
                "distance_m": l.get("distance"),
                "moving_time_s": l.get("moving_time"),
                "average_speed_ms": l.get("average_speed"),
                "average_heartrate": l.get("average_heartrate"),
                "average_watts": l.get("average_watts"),
            }
            for l in (a.get("laps") or [])
        ],
    }


def get_athlete_stats() -> dict:
    """Return all-time and recent statistics for the authenticated athlete."""
    profile = get_athlete_profile()
    athlete_id = profile["id"]
    resp = requests.get(
        f"{STRAVA_API_BASE}/athletes/{athlete_id}/stats",
        headers=_auth_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    s = resp.json()

    def _summarise(block: Optional[dict]) -> dict:
        if not block:
            return {}
        return {
            "count": block.get("count"),
            "distance_km": round(block.get("distance", 0) / 1000, 1),
            "moving_time_h": round(block.get("moving_time", 0) / 3600, 1),
            "elevation_gain_m": block.get("elevation_gain"),
            "achievement_count": block.get("achievement_count"),
        }

    return {
        "recent_run": _summarise(s.get("recent_run_totals")),
        "recent_ride": _summarise(s.get("recent_ride_totals")),
        "recent_swim": _summarise(s.get("recent_swim_totals")),
        "ytd_run": _summarise(s.get("ytd_run_totals")),
        "ytd_ride": _summarise(s.get("ytd_ride_totals")),
        "ytd_swim": _summarise(s.get("ytd_swim_totals")),
        "all_run": _summarise(s.get("all_run_totals")),
        "all_ride": _summarise(s.get("all_ride_totals")),
        "all_swim": _summarise(s.get("all_swim_totals")),
        "biggest_ride_distance_km": round(s.get("biggest_ride_distance", 0) / 1000, 1),
        "biggest_climb_elevation_gain_m": s.get("biggest_climb_elevation_gain"),
    }
