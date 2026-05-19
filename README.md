# Strava Workout Coach Agent

An A2A-protocol AI agent that reads your Strava data and generates personalised weekly training plans.


Copy the environment file and fill in your credentials:
- Fill in API_KEY from Hyperspace API Key
- Fill in Strava Client ID and Client Secret

```bash
cp .env.example .env
```

## Setup Python virtual environment
 1. Create Python venv:
    ```bash
    python3 -m venv .venv
    ```
 2. Activate Python venv:
    ### In cmd.exe
    ```bash
    .venv\Scripts\activate.bat
    ```
    ### In PowerShell
    ```bash
    .venv\Scripts\Activate.ps1
    ```
    ### In Mac
    ```bash
    source .venv/bin/activate
    ```

 ## Install dependencies:
```bash
pip3 install -r requirements.txt
```

## Running Agent locally

### 1 — Start the agent

The agent auto-spawns the Strava MCP server as a subprocess — no separate terminal needed.

```bash
python strava_auth.py
python main.py
```

Agent runs on `http://localhost:8080`.

## Test

```bash
# Check agent card
curl http://localhost:8080/.well-known/agent.json

# Request a training plan
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "kind": "message",
        "messageId": "msg-001",
        "role": "user",
        "parts": [{"kind": "text", "text": "Create my training plan for next week"}]
      }
    }
  }'
```

## Run App locally

```bash
cd app/
npm install
npm run start
```

## Project structure

```
main.py                         # A2A server entry point
mcp/
  strava_mcp_server.py          # Strava MCP server (FastMCP)
  strava_tools.py               # Strava API functions
agent/
  agent.py                      # LangGraph ReAct agent + coaching prompt
  agent_executor.py             # A2A protocol executor
  mcp_client_connector.py       # Connects agent to Strava MCP server
joule/
  da.sapdas.yaml                # Joule deployment descriptor
  a2a/
    capability.sapdas.yaml      # System alias → BTP destination
    capability_context.yaml     # Conversation context variable
    functions/agent_coach.yaml  # A2A request function
    scenarios/coach/coach.yaml  # Joule routing scenario
```