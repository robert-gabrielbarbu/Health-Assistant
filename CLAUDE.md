# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

```
main.py                      # A2A server entry point (Click CLI + uvicorn)
strava_auth.py               # One-time OAuth flow to obtain a Strava refresh token
requirements.txt
agent/
  agent.py                   # LangGraph StateGraph + CoachAgent class
  agent_executor.py          # A2A AgentExecutor bridging the protocol to LangGraph
  mcp_client_connector.py    # Connects agent to MCP server (stdio or HTTP)
mcp/
  strava_mcp_server.py       # FastMCP server — exposes Strava tools over stdio/HTTP
  strava_tools.py            # Raw Strava API calls (auth, token refresh, activity fetch)
app/                         # SAPUI5 Fiori chat UI
  ui5.yaml                   # Proxies /api/agent → http://localhost:8080
  webapp/
    service/A2AService.js    # JSON-RPC 2.0 A2A client (streaming with sendMessage fallback)
    controller/Chat.controller.js
    view/Chat.view.xml
    css/style.css
joule/                       # SAP DAS deployment descriptors
.claude/skills/              # Agent scaffolding skills (see Skills section below)
```

> The workspace-level `.mcp.json` (one directory above this repo) configures MCP servers for Claude Code — see the MCP section below.

## Development commands

```bash
# First-time setup
cp .env.example .env          # fill in credentials
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# One-time Strava OAuth (opens browser, writes tokens to .env)
python strava_auth.py

# Run the agent  (http://localhost:8080)
python main.py

# Run MCP server standalone over HTTP (port 8000)
cd mcp && python strava_mcp_server.py --http

# Start the Fiori UI  (http://localhost:8081)
cd app && npm install && npm start
```

Test the agent with curl:
```bash
curl http://localhost:8080/.well-known/agent.json

curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"kind":"message","messageId":"m1","role":"user","parts":[{"kind":"text","text":"Create my training plan for next week"}]}}}'
```

## Architecture

### A2A protocol layer

`main.py` builds an `A2AStarletteApplication` using `a2a-sdk==0.2.9`. The SDK only implements `message/send` (blocking JSON-RPC 2.0). `message/stream` (SSE) is **not** supported by this SDK version — `A2AService.js` in the Fiori UI attempts streaming first then falls back to `sendMessage` when the server returns `application/json` instead of `text/event-stream`.

The executor (`agent/agent_executor.py`) receives a task from the A2A layer, calls `agent.stream()`, and maps the yielded dicts to A2A `TaskState` events:
- `is_task_complete=False, require_user_input=False` → `working` status update
- `is_task_complete=False, require_user_input=True` → `input_required` (final)
- `is_task_complete=True` → artifact with text content + `complete()`

### LangGraph agent (`agent/agent.py`)

`CoachAgent` builds a `StateGraph` lazily on first call to `stream()`. The graph has two nodes — `agent` (LLM call) and `tools` (ToolNode) — connected by `tools_condition`. It uses `MemorySaver` for in-memory thread persistence keyed by `context_id` (the A2A `contextId`).

The MCP client is a module-level singleton initialized once; `mcp_client_connector.get_mcp_client()` checks `STRAVA_MCP_URL` — if set it connects via HTTP, otherwise it spawns `mcp/strava_mcp_server.py` as a subprocess via stdio.

### MCP layer (`mcp/`)

`strava_tools.py` holds all raw Strava REST calls. It caches the OAuth access token in module-level globals and auto-refreshes using `STRAVA_REFRESH_TOKEN`. `strava_mcp_server.py` wraps each tool as a `@mcp.tool()` using FastMCP and can run in `stdio` (default) or `streamable-http` (`--http` flag) mode.

### Fiori UI (`app/`)

Pure SAPUI5 1.120 SPA — no backend, no MockServer. The `ui5-middleware-simpleproxy` in `app/ui5.yaml` proxies `/api/agent/*` to `http://localhost:8080/*` to avoid CORS. `A2AService.js` is self-contained and requires no changes for different agents.

The chat area is a `VBox#chatArea` with `overflow-y: auto` in CSS (not a SAPUI5 `ScrollContainer`) — this bypasses SAPUI5's JS scroll management. `_scrollToBottom()` sets `domRef.scrollTop = domRef.scrollHeight` directly.

## Environment variables

```
LITELLM_BASE_URL      LiteLLM proxy URL (e.g. http://localhost:6655/litellm/v1)
LITELLM_API_KEY       API key for LiteLLM
LITELLM_MODEL         Model ID (e.g. anthropic--claude-sonnet-4-6)
STRAVA_CLIENT_ID      Strava API app client ID
STRAVA_CLIENT_SECRET
STRAVA_REFRESH_TOKEN  Written automatically by strava_auth.py
STRAVA_ACCESS_TOKEN
STRAVA_MCP_URL        (optional) point agent at a running MCP server via HTTP
```

## Agent scaffolding skills

Five Claude Code skills in `.claude/skills/` scaffold new A2A agents following this pattern:

| Skill | What it generates |
|---|---|
| `agent-project-intent` | `agent-intent.md` — source of truth consumed by all other skills |
| `agent-core` | `main.py`, `agent/`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md` |
| `agent-mcp` | `mcp/` — FastMCP server + tool stubs (only if MCP tools needed) |
| `agent-fiori` | `app/` — complete SAPUI5 Fiori chat UI (only if Fiori needed) |
| `agent-joule` | `joule/` — SAP DAS deployment YAMLs (only if Joule needed) |

Run `/agent-project-intent` first; it asks questions and writes `agent-intent.md`. Then run the generation skills in any order.

## MCP servers

Configured in `.mcp.json` one level above this repo (workspace root):

| Server | Transport | Purpose |
|---|---|---|
| `strava` | stdio | Local Strava MCP server (`mcp/strava_mcp_server.py`) via `.venv` Python |
| `n8n-mcp` | HTTP/OAuth | n8n workflow automation |
| `cds-mcp` | stdio (npx) | SAP CAP/CDS development tools |
| `ui5-mcp` | stdio (npx) | UI5 Web Components React API docs |
| `ibd-mcp` | HTTP/OAuth | SAP Intent-Based Development |
