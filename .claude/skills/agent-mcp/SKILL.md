---
name: agent-mcp
description: Generates the mcp/ folder for an A2A+LangGraph agent project — a FastMCP server and tool implementation stubs — from agent-intent.md. Run after agent-project-intent and agent-core when MCP tools are required.
---

# Agent MCP Generator

Reads `agent-intent.md` and generates the `mcp/` folder: a FastMCP server and the tool implementation file.

**Prerequisite:** `agent-intent.md` must exist (run `agent-project-intent` first). Only run this skill if MCP tools are required per `agent-intent.md`.

---

## Instructions

### Step 1 — Read Intent

Read `agent-intent.md` and extract:
- `{{AGENT_NAME}}` — project folder name
- `{{MCP_SERVER_NAME}}` — kebab-case server name (e.g. `weather-server`)
- `{{MCP_SERVER_SLUG}}` — snake_case server name (e.g. `weather_server`)
- `{{MCP_SERVER_TITLE}}` — title-case server name (e.g. `Weather Server`)
- `{{MCP_ENV_PREFIX}}` — SCREAMING_SNAKE prefix (e.g. `WEATHER`)
- `{{MCP_API_SERVICE}}` — the external API or service the tools connect to
- All MCP tool definitions: name, description, parameters, return value

Derive:
- `{{MCP_SERVER_FILE}}` = `{{MCP_SERVER_SLUG}}_mcp_server.py`
- `{{MCP_TOOLS_FILE}}` = `{{MCP_SERVER_SLUG}}_tools.py`
- For each tool: `{{TOOL_SNAKE_NAME}}` = snake_case of tool name

### Step 2 — Create Directory

```bash
mkdir -p {{AGENT_NAME}}/mcp
```

### Step 3 — Write All Files

Write both files below with all placeholders substituted.

---

## File: `{{AGENT_NAME}}/mcp/{{MCP_TOOLS_FILE}}`

This file contains the actual API/service call implementations. Each function maps directly to one MCP tool.

```python
"""{{MCP_SERVER_TITLE}} tools — wraps {{MCP_API_SERVICE}} calls."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Authentication / client setup ────────────────────────────────────────────
# Add any API client initialization, token caching, or auth helpers here.
# Use module-level globals for token caching (see pattern below).

_cached_token: str = ""
_cached_expires_at: float = 0.0


def _get_headers() -> dict:
    """Return auth headers for {{MCP_API_SERVICE}} requests.

    Replace with real auth logic. Common patterns:
    - Static API key:  {"Authorization": f"Bearer {os.getenv('{{MCP_ENV_PREFIX}}_API_KEY')}"}
    - OAuth refresh:   implement token refresh + module-level cache
    """
    api_key = os.getenv("{{MCP_ENV_PREFIX}}_API_KEY", "")
    if not api_key:
        raise ValueError(
            "{{MCP_ENV_PREFIX}}_API_KEY is not set. "
            "Add it to your .env file."
        )
    return {"Authorization": f"Bearer {api_key}"}


# ── Tool implementations ──────────────────────────────────────────────────────
# One function per MCP tool. Keep functions focused: one API call each.
# Return plain dicts/lists — no pydantic models needed here.
```

Then append one function per MCP tool defined in `agent-intent.md`, following this pattern for each:

```python
def {{TOOL_SNAKE_NAME}}({{TOOL_PARAMS_WITH_DEFAULTS}}) -> {{RETURN_TYPE_HINT}}:
    """{{TOOL_DESCRIPTION}}

    Args:
        {{PARAM_NAME}}: {{PARAM_DESCRIPTION}}

    Returns:
        {{RETURN_DESCRIPTION}}
    """
    # TODO: implement — replace with real {{MCP_API_SERVICE}} call
    raise NotImplementedError(
        "{{TOOL_SNAKE_NAME}} is not yet implemented. "
        "Replace this stub with the actual {{MCP_API_SERVICE}} API call."
    )
```

> Rules for the implementations:
> - Use `requests` for HTTP calls (already in requirements.txt).
> - Always call `.raise_for_status()` after HTTP responses.
> - Return only the fields the agent actually needs — filter raw API responses to a flat dict.
> - Use module-level caching for any tokens/sessions that are expensive to create.
> - Load env vars with `os.getenv()` — never hardcode credentials.

---

## File: `{{AGENT_NAME}}/mcp/{{MCP_SERVER_FILE}}`

This file is the FastMCP server. It wraps each tool implementation function as an MCP tool.

```python
"""{{MCP_SERVER_TITLE}} MCP server — exposes {{MCP_API_SERVICE}} data as MCP tools via FastMCP.

Run modes:
  stdio (default, for MCP clients):  python {{MCP_SERVER_FILE}}
  HTTP  (for remote clients):        python {{MCP_SERVER_FILE}} --http
"""

import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from {{MCP_SERVER_SLUG}}_tools import (
```

Then for each tool, add the import:
```python
    {{TOOL_SNAKE_NAME}} as _{{TOOL_SNAKE_NAME}},
```

Then continue:
```python
)

load_dotenv()

mcp = FastMCP(
    "{{MCP_SERVER_TITLE}}",
    instructions="{{MCP_SERVER_TITLE}} tools for {{MCP_API_SERVICE}} data access.",
)
```

Then for each tool from `agent-intent.md`, generate a `@mcp.tool()` decorated wrapper:

```python
@mcp.tool()
def {{TOOL_SNAKE_NAME}}({{TOOL_PARAMS_WITH_DEFAULTS}}) -> {{RETURN_TYPE_HINT}}:
    """{{TOOL_DESCRIPTION}}

    Args:
        {{PARAM_NAME}}: {{PARAM_DESCRIPTION}}

    Returns:
        {{RETURN_DESCRIPTION}}
    """
    return _{{TOOL_SNAKE_NAME}}({{TOOL_PARAM_NAMES_ONLY}})
```

Close with the entry point:
```python

if __name__ == "__main__":
    transport = "streamable-http" if "--http" in sys.argv else "stdio"
    mcp.run(transport=transport)
```

---

## Step 4 — Update `.env.example`

Append the MCP-specific env vars to `{{AGENT_NAME}}/.env.example`:

```
# {{MCP_SERVER_TITLE}} Configuration
{{MCP_ENV_PREFIX}}_API_KEY=YOUR_{{MCP_ENV_PREFIX}}_API_KEY_HERE
# Add any other service-specific vars here (tokens, base URLs, etc.)
```

Also add the HTTP transport toggle comment if not already present:
```
# Optional: run MCP server separately over HTTP
# {{MCP_ENV_PREFIX}}_MCP_URL=http://localhost:8000/mcp
```

---

## Step 5 — Confirm

Print a summary of what was created:

```
Created:
  {{AGENT_NAME}}/mcp/{{MCP_TOOLS_FILE}}      (tool implementations — fill in stubs)
  {{AGENT_NAME}}/mcp/{{MCP_SERVER_FILE}}      (FastMCP server — ready to run)
Updated:
  {{AGENT_NAME}}/.env.example               (added {{MCP_ENV_PREFIX}}_* vars)
```

Then remind the user:
- Fill in the `NotImplementedError` stubs in `{{MCP_TOOLS_FILE}}` with real API calls.
- Add any required credentials to `.env`.
- Test the MCP server standalone: `python mcp/{{MCP_SERVER_FILE}}`
- Or run it over HTTP: `python mcp/{{MCP_SERVER_FILE}} --http` then set `{{MCP_ENV_PREFIX}}_MCP_URL=http://localhost:8000/mcp`.

---

## Reference: FastMCP Parameter Types

Use standard Python type hints in `@mcp.tool()` signatures:

| Intent | Type hint |
|---|---|
| String input | `str` |
| Integer input | `int` |
| Float input | `float` |
| Boolean flag | `bool` |
| Optional param | `str = "default"` or `int = 0` |
| List return | `list` or `list[dict]` |
| Dict return | `dict` |

Keep parameter names snake_case. Add docstring Args/Returns for every tool — FastMCP exposes these as the MCP tool schema the LLM sees.
