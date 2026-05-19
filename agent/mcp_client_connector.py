# app/mcp_client_connector.py
"""Strava MCP client — connects to the local Strava MCP server via stdio transport."""

import logging
import os

from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


async def get_mcp_client() -> MultiServerMCPClient:
    """
    Initialize and return an MCP client connected to the Strava MCP server.

    To use HTTP transport instead (e.g. if the server is already running):
      Set STRAVA_MCP_URL=http://localhost:8000/mcp and restart.
    """
    mcp_url = os.getenv("STRAVA_MCP_URL")

    if mcp_url:
        logger.info(f"Connecting to Strava MCP server via HTTP: {mcp_url}")
        mcp_config = {
            "strava": {
                "url": mcp_url,
                "transport": "streamable_http",
            }
        }
    else:
        logger.info("Spawning Strava MCP server via stdio")
        mcp_config = {
            "strava": {
                "transport": "stdio",
                "command": "python",
                "args": ["strava_mcp_server.py"],
                "cwd": os.path.join(os.path.dirname(__file__), "..", "mcp"),
                "env": {**os.environ},
            }
        }

    client = MultiServerMCPClient(mcp_config)
    logger.info(f"Strava MCP client configured ({'HTTP' if mcp_url else 'stdio'})")
    return client
