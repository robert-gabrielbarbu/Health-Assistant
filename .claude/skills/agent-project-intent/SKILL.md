---
name: agent-project-intent
description: Captures requirements for a new A2A+LangGraph agent project (Strava-coach pattern). Asks the user about agent purpose, tools (MCP / custom), Fiori UI, and Joule integration, then writes agent-intent.md. Run this skill first before agent-core, agent-mcp, agent-fiori, or agent-joule.
---

# Agent Project Intent

Captures the user's requirements for a new A2A+LangGraph agent project and writes `agent-intent.md` — the single source of truth consumed by the `agent-core`, `agent-mcp`, `agent-fiori`, and `agent-joule` skills.

**Check for existing file first:**
- If `agent-intent.md` already exists → enter Refinement Mode (read it, ask what to change, update and save).
- If it does not exist → run the Workflow below.

---

## Workflow

### Step 1 — Ask Clarifying Questions

Use the `question` tool (or equivalent) to collect the following. Ask all questions in a single interaction where possible.

**Required questions:**

1. **Agent name** — kebab-case slug (e.g. `weather-agent`, `invoice-processor`).
2. **Agent description** — one or two sentences: what the agent does and for whom.
3. **MCP tools** — Does the agent need MCP tools (tools that call an external API/service via a FastMCP server)?
   - If yes: for each MCP server needed:
     - Server name (kebab-case, e.g. `weather-server`)
     - What API or service it connects to (URL, SDK, or service name)
     - List of tools to expose: for each tool give a name, what it does, its parameters (name + type), and what it returns.
4. **Custom tools** — Does the agent need any custom Python tools (LangChain `@tool` functions — no separate MCP server)?
   - If yes: for each tool give a name, what it does, parameters, and return value.
5. **Fiori UI** — Should a SAPUI5 Fiori chat UI be generated for this agent?
   - If yes: Fiori dev server port (default: `8081`). The UI proxies calls to the agent, so the agent and UI can run side by side.
6. **Joule integration** — Should this agent be deployable via Joule (SAP DAS)?
   - If yes: BTP destination name (SCREAMING_SNAKE, e.g. `WEATHER_AGENT`), and a one-sentence description of what the Joule scenario does.
   - Note: Fiori UI and Joule are independent — you can choose one, both, or neither.
7. **LLM model** — Which model? Default: `anthropic--claude-sonnet-4-6`. Accept any `LITELLM_MODEL` value.
8. **Port** — Default: `8080`.

### Step 2 — Derive All Values

From the answers, derive the following (do not ask the user — compute them):

| Field | Derivation |
|---|---|
| `AGENT_TITLE` | Title-case of agent name (replace `-` with space, capitalize each word) |
| `AGENT_CLASS_NAME` | PascalCase of agent name (e.g. `weather-agent` → `WeatherAgent`) |
| `AGENT_NAME_YAML` | snake_case of agent name (e.g. `weather-agent` → `weather_agent`) |
| `AGENT_ID` | Same as agent name (kebab-case) |
| `AGENT_TAGS` | Split agent name by `-` into list (e.g. `["weather", "agent"]`) |
| `AGENT_EXAMPLES` | Generate 3 realistic example prompts a user would send to this agent |
| `SYSTEM_PROMPT` | Write a focused system prompt: persona, what data/tools to always use, output format, tone |
| `MCP_SERVER_SLUG` | snake_case of MCP server name (e.g. `weather_server`) |
| `MCP_ENV_PREFIX` | SCREAMING_SNAKE of MCP server name (e.g. `WEATHER`) — used as env var prefix |
| `TOOL_WORKING_MESSAGE` | Short present-continuous message shown while a tool runs (e.g. "Fetching weather data...") |
| `TOOL_PROCESSING_MESSAGE` | Short present-continuous message shown while processing tool result (e.g. "Analysing forecast...") |
| `UI5_NAMESPACE` | `com.` + agent name parts joined with `.` (e.g. `weather-agent` → `com.weather.agent`) |
| `FIORI_PORT` | The dev server port the user provided, or `8081` |
| `SYSTEM_ALIAS` | SCREAMING_SNAKE version of agent name (e.g. `WEATHER_AGENT`) — only if Joule required |
| `BTP_DESTINATION` | The destination name the user provided — only if Joule required |
| `SCENARIO_NAME` | snake_case of agent name — used for Joule scenario folder and file name |
| `FUNCTION_NAME` | `agent_` + SCENARIO_NAME (e.g. `agent_weather_agent`) |

### Step 3 — Write `agent-intent.md`

Write the file in the **current directory** using the template below. Replace every `{{PLACEHOLDER}}` with the derived value. Do not leave any placeholder unfilled.

**After writing, do not reproduce or summarise the file in chat.** Confirm it was saved (one line).

---

## `agent-intent.md` Template

```markdown
# Agent Intent: {{AGENT_TITLE}}

## Metadata

- **Name**: {{AGENT_NAME}}
- **Title**: {{AGENT_TITLE}}
- **Class**: {{AGENT_CLASS_NAME}}
- **ID**: {{AGENT_NAME}}
- **Name (YAML)**: {{AGENT_NAME_YAML}}
- **Description**: {{AGENT_DESCRIPTION}}
- **Port**: {{PORT}}
- **LLM Model**: {{LLM_MODEL}}

## System Prompt

{{SYSTEM_PROMPT}}

## Tools

### MCP Tools

- **Required**: yes | no
- **MCP Server Name (kebab)**: {{MCP_SERVER_NAME}}
- **MCP Server Slug (snake)**: {{MCP_SERVER_SLUG}}
- **MCP Env Prefix**: {{MCP_ENV_PREFIX}}
- **API / Service**: {{MCP_API_SERVICE}}

#### {{TOOL_NAME}}

- Description: {{TOOL_DESCRIPTION}}
- Parameters: {{PARAM_NAME}} ({{PARAM_TYPE}})[, ...]
- Returns: {{RETURN_DESCRIPTION}}

<!-- repeat for each MCP tool -->

### Custom Tools

- **Required**: yes | no

#### {{CUSTOM_TOOL_NAME}}

- Description: {{CUSTOM_TOOL_DESCRIPTION}}
- Parameters: {{PARAM_NAME}} ({{PARAM_TYPE}})[, ...]
- Returns: {{RETURN_DESCRIPTION}}
- Implementation note: {{IMPLEMENTATION_NOTE}}

<!-- repeat for each custom tool -->

## Fiori UI

- **Required**: yes | no
- **UI5 Namespace**: {{UI5_NAMESPACE}}
- **Fiori Dev Port**: {{FIORI_PORT}}

## Joule Integration

- **Required**: yes | no
- **System Alias**: {{SYSTEM_ALIAS}}
- **BTP Destination**: {{BTP_DESTINATION}}
- **Agent Name (YAML)**: {{AGENT_NAME_YAML}}
- **Scenario Name**: {{SCENARIO_NAME}}
- **Function Name**: {{FUNCTION_NAME}}
- **Scenario Description**: {{SCENARIO_DESCRIPTION}}

## Agent Card

- **Tags**: {{AGENT_TAGS}}
- **Examples**:
  - {{EXAMPLE_1}}
  - {{EXAMPLE_2}}
  - {{EXAMPLE_3}}

## Streaming Messages

- **Tool working**: {{TOOL_WORKING_MESSAGE}}
- **Tool processing**: {{TOOL_PROCESSING_MESSAGE}}
```

---

## Refinement Mode

When `agent-intent.md` already exists:
1. Read the file.
2. Ask the user what they want to change.
3. Apply changes, overwrite the file.
4. Confirm (one line) what changed.
5. Ask if they want further changes or to proceed to skill generation.

---

## Next Steps

After writing `agent-intent.md`, tell the user the generation skills to run next:

1. **`agent-core`** — generates `main.py`, `agent/`, `requirements.txt`, `.env.example`, `.gitignore`
2. **`agent-mcp`** — generates `mcp/` folder with FastMCP server and tool stubs *(skip if no MCP tools)*
3. **`agent-fiori`** — generates `app/` folder with the SAPUI5 Fiori chat UI *(skip if Fiori not required)*
4. **`agent-joule`** — generates `joule/` folder with DAS deployment descriptors *(skip if Joule not required)*

Ask if they want to proceed with all applicable skills immediately or run them one at a time.
