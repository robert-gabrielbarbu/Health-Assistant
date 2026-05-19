---
name: agent-core
description: Generates the core A2A+LangGraph agent project from agent-intent.md. Produces main.py, agent/ package (agent.py with StateGraph, agent_executor.py, mcp_client_connector.py if needed), requirements.txt, .env.example, and .gitignore. Run after agent-project-intent.
---

# Agent Core Generator

Reads `agent-intent.md` in the current directory and generates the core Python project for an A2A+LangGraph agent following the Strava-coach architecture pattern.

**Prerequisite:** `agent-intent.md` must exist. If it does not, run the `agent-project-intent` skill first.

---

## Instructions

### Step 1 — Read Intent

Read `agent-intent.md` and extract all values. Identify:
- `{{AGENT_NAME}}` — kebab-case project slug
- `{{AGENT_TITLE}}`, `{{AGENT_CLASS_NAME}}`, `{{AGENT_ID}}`, `{{AGENT_DESCRIPTION}}`
- `{{PORT}}`, `{{LLM_MODEL}}`
- `{{AGENT_TAGS}}`, `{{AGENT_EXAMPLES}}` (examples as Python list)
- `{{SYSTEM_PROMPT}}`
- Whether **MCP tools** are required (yes/no) and MCP details
- Whether **custom tools** are required (yes/no) and tool details
- `{{TOOL_WORKING_MESSAGE}}`, `{{TOOL_PROCESSING_MESSAGE}}`

### Step 2 — Create Project Directory

Create `{{AGENT_NAME}}/` and `{{AGENT_NAME}}/agent/` directories.

```bash
mkdir -p {{AGENT_NAME}}/agent
```

### Step 3 — Write All Files

Write each file below, substituting all `{{PLACEHOLDER}}` values from `agent-intent.md`.

Use the Write tool for each file. Write them all — do not skip any.

---

## File: `{{AGENT_NAME}}/requirements.txt`

```
a2a-sdk[all]==0.2.9
langchain-openai
langgraph==0.6.10
langchain-mcp-adapters==0.1.11
mcp[cli]>=1.0.0
httpx
uvicorn
click
python-dotenv
requests>=2.31.0
```

> If MCP tools are **not** required, omit `langchain-mcp-adapters==0.1.11` and `mcp[cli]>=1.0.0`.

---

## File: `{{AGENT_NAME}}/.gitignore`

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
build/
develop-eggs/
dist/
*.egg-info/
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Unit test / coverage
htmlcov/
.tox/
.coverage
.coverage.*
.cache
.pytest_cache/
cover/

# Jupyter
.ipynb_checkpoints

# mypy / pytype
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
.pytype/

# Tools
.ruff_cache/
.pdm.toml
.pdm-python
.pdm-build/

# IDEs
.DS_Store

# Node (for the Fiori UI app/)
*/node_modules/*
```

---

## File: `{{AGENT_NAME}}/.env.example`

```
# LiteLLM Proxy Configuration
LITELLM_BASE_URL=http://localhost:6655/litellm/v1
LITELLM_API_KEY=YOUR_API_KEY
# Available models: anthropic--claude-sonnet-4-6, anthropic--claude-opus-4-7, anthropic--claude-haiku-4-5
LITELLM_MODEL={{LLM_MODEL}}

# Optional: run MCP server separately and point agent to it via HTTP
# {{MCP_ENV_PREFIX}}_MCP_URL=http://localhost:8000/mcp
```

> Add any tool-specific env vars listed in `agent-intent.md` below the LiteLLM block (e.g. API keys, tokens).
> Only include the `{{MCP_ENV_PREFIX}}_MCP_URL` line if MCP tools are required.

---

## File: `{{AGENT_NAME}}/main.py`

```python
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

from agent.agent import {{AGENT_CLASS_NAME}}
from agent.agent_executor import {{AGENT_CLASS_NAME}}Executor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Raised when a required environment variable is not set."""


@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=int(os.getenv("PORT", {{PORT}})), type=int)
def main(host, port):
    """Start the {{AGENT_TITLE}} A2A Agent server."""
    load_dotenv()

    required_env_vars = ["LITELLM_BASE_URL", "LITELLM_API_KEY"]
    for var in required_env_vars:
        if not os.getenv(var):
            logger.error(f"Required environment variable {var} is not set.")
            raise MissingAPIKeyError(f"{var} is not set.")

    logger.info("All required environment variables loaded.")

    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
    skill = AgentSkill(
        id="{{AGENT_ID}}",
        name="{{AGENT_TITLE}}",
        description="{{AGENT_DESCRIPTION}}",
        tags={{AGENT_TAGS}},
        examples={{AGENT_EXAMPLES}},
    )

    agent_card = AgentCard(
        name="{{AGENT_TITLE}}",
        description="{{AGENT_DESCRIPTION}}",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes={{AGENT_CLASS_NAME}}.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes={{AGENT_CLASS_NAME}}.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    httpx_client = httpx.AsyncClient()
    push_notifier = InMemoryPushNotifier(httpx_client=httpx_client)

    request_handler = DefaultRequestHandler(
        agent_executor={{AGENT_CLASS_NAME}}Executor(),
        task_store=InMemoryTaskStore(),
        push_notifier=push_notifier,
    )

    server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
    logger.info(f"Agent running at http://{host}:{port}/")
    logger.info(f"Agent card: http://{host}:{port}/.well-known/agent.json")
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
```

> `{{AGENT_TAGS}}` must be a Python list literal, e.g. `["weather", "forecast"]`.
> `{{AGENT_EXAMPLES}}` must be a Python list literal, e.g. `["What is the weather today?", "Forecast for next week"]`.

---

## File: `{{AGENT_NAME}}/agent/__init__.py`

Empty file.

---

## File: `{{AGENT_NAME}}/agent/agent.py`

Use the variant that matches the tool configuration from `agent-intent.md`.

### Variant A — MCP tools only

```python
# agent/agent.py
import logging
import os
from collections.abc import AsyncIterable
from datetime import datetime
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv

from agent import mcp_client_connector

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory = MemorySaver()
mcp_client = None


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


class {{AGENT_CLASS_NAME}}:
    SYSTEM_INSTRUCTION = (
        "{{SYSTEM_PROMPT}}"
        f"Today's date is {datetime.now().strftime('%Y-%m-%d')}.\n\n"
        "Tone: helpful, direct, concise. No filler phrases."
    )

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        base_url = os.getenv("LITELLM_BASE_URL", "").rstrip("/")
        api_key = os.getenv("LITELLM_API_KEY", "")
        model = os.getenv("LITELLM_MODEL", "{{LLM_MODEL}}")
        self.model = ChatOpenAI(base_url=base_url, api_key=api_key, model=model, temperature=0, max_tokens=4096)
        self.graph = None

    async def init_agent(self):
        global mcp_client
        if mcp_client is None:
            logger.info("Initializing MCP client...")
            mcp_client = await mcp_client_connector.get_mcp_client()
            logger.info("MCP client initialized")

        tools = await mcp_client.get_tools()
        logger.info(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}")

        model_with_tools = self.model.bind_tools(tools)
        system_message = SystemMessage(content=self.SYSTEM_INSTRUCTION)

        async def agent_node(state: AgentState) -> dict:
            messages = [system_message] + state["messages"]
            response = await model_with_tools.ainvoke(messages)
            return {"messages": [response]}

        builder = StateGraph(AgentState)
        builder.add_node("agent", agent_node)
        builder.add_node("tools", ToolNode(tools))
        builder.set_entry_point("agent")
        builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
        builder.add_edge("tools", "agent")

        self.graph = builder.compile(checkpointer=memory)

    async def stream(self, query: str, context_id: str) -> AsyncIterable[dict[str, Any]]:
        if self.graph is None:
            await self.init_agent()

        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": context_id}}

        async for item in self.graph.astream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if isinstance(message, AIMessage) and getattr(message, "tool_calls", None):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "{{TOOL_WORKING_MESSAGE}}",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "{{TOOL_PROCESSING_MESSAGE}}",
                }

        yield self._get_agent_response(config)

    def _get_agent_response(self, config: dict) -> dict[str, Any]:
        state = self.graph.get_state(config)
        messages = state.values.get("messages", [])
        last = messages[-1] if messages else None

        if isinstance(last, AIMessage):
            content = last.content if isinstance(last.content, str) else str(last.content)
            return {"is_task_complete": True, "require_user_input": False, "content": content}

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "Unable to generate a response. Please provide more details.",
        }
```

### Variant B — Custom tools only (no MCP)

Replace the `init_agent` method and imports. Use `@tool` decorated functions instead of MCP tools:

```python
# agent/agent.py  — custom tools variant
import logging
import os
from collections.abc import AsyncIterable
from datetime import datetime
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory = MemorySaver()


# ── Tool definitions ──────────────────────────────────────────────────────────
# Define one @tool per custom tool from agent-intent.md.
# Replace stubs with real implementations.

@tool
def {{CUSTOM_TOOL_SNAKE_NAME}}({{TOOL_PARAMS}}) -> {{RETURN_TYPE}}:
    """{{TOOL_DESCRIPTION}}"""
    # TODO: implement
    raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────────


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


class {{AGENT_CLASS_NAME}}:
    SYSTEM_INSTRUCTION = (
        "{{SYSTEM_PROMPT}}"
        f"Today's date is {datetime.now().strftime('%Y-%m-%d')}.\n\n"
        "Tone: helpful, direct, concise. No filler phrases."
    )

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        base_url = os.getenv("LITELLM_BASE_URL", "").rstrip("/")
        api_key = os.getenv("LITELLM_API_KEY", "")
        model = os.getenv("LITELLM_MODEL", "{{LLM_MODEL}}")
        self.model = ChatOpenAI(base_url=base_url, api_key=api_key, model=model, temperature=0, max_tokens=4096)
        self.graph = None

    async def init_agent(self):
        tools = [{{CUSTOM_TOOL_SNAKE_NAME}}]  # add all @tool functions here

        model_with_tools = self.model.bind_tools(tools)
        system_message = SystemMessage(content=self.SYSTEM_INSTRUCTION)

        async def agent_node(state: AgentState) -> dict:
            messages = [system_message] + state["messages"]
            response = await model_with_tools.ainvoke(messages)
            return {"messages": [response]}

        builder = StateGraph(AgentState)
        builder.add_node("agent", agent_node)
        builder.add_node("tools", ToolNode(tools))
        builder.set_entry_point("agent")
        builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
        builder.add_edge("tools", "agent")

        self.graph = builder.compile(checkpointer=memory)

    async def stream(self, query: str, context_id: str) -> AsyncIterable[dict[str, Any]]:
        if self.graph is None:
            await self.init_agent()

        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": context_id}}

        async for item in self.graph.astream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if isinstance(message, AIMessage) and getattr(message, "tool_calls", None):
                yield {"is_task_complete": False, "require_user_input": False, "content": "{{TOOL_WORKING_MESSAGE}}"}
            elif isinstance(message, ToolMessage):
                yield {"is_task_complete": False, "require_user_input": False, "content": "{{TOOL_PROCESSING_MESSAGE}}"}

        yield self._get_agent_response(config)

    def _get_agent_response(self, config: dict) -> dict[str, Any]:
        state = self.graph.get_state(config)
        messages = state.values.get("messages", [])
        last = messages[-1] if messages else None

        if isinstance(last, AIMessage):
            content = last.content if isinstance(last.content, str) else str(last.content)
            return {"is_task_complete": True, "require_user_input": False, "content": content}

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "Unable to generate a response. Please provide more details.",
        }
```

### Variant C — Both MCP and custom tools

Use Variant A as the base. In `init_agent`, after loading MCP tools, append the custom `@tool` functions:

```python
from langchain_core.tools import tool

@tool
def {{CUSTOM_TOOL_SNAKE_NAME}}({{TOOL_PARAMS}}) -> {{RETURN_TYPE}}:
    """{{TOOL_DESCRIPTION}}"""
    raise NotImplementedError

# In init_agent:
mcp_tools = await mcp_client.get_tools()
custom_tools = [{{CUSTOM_TOOL_SNAKE_NAME}}]
tools = mcp_tools + custom_tools
```

---

## File: `{{AGENT_NAME}}/agent/agent_executor.py`

```python
# agent/agent_executor.py
import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from agent.agent import {{AGENT_CLASS_NAME}}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {{AGENT_CLASS_NAME}}Executor(AgentExecutor):

    def __init__(self):
        self.agent = {{AGENT_CLASS_NAME}}()
        self._initialized = False

    async def _ensure_initialized(self):
        if not self._initialized:
            await self.agent.init_agent()
            self._initialized = True

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._ensure_initialized()

        if self._validate_request(context):
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.contextId)
        try:
            async for item in self.agent.stream(query, task.contextId):
                is_complete = item["is_task_complete"]
                needs_input = item["require_user_input"]
                content = item.get("content", "")

                if not is_complete and not needs_input:
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(content, task.contextId, task.id),
                    )
                elif needs_input:
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(content, task.contextId, task.id),
                        final=True,
                    )
                    break
                else:
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name="{{AGENT_ID}}-result",
                    )
                    await updater.complete()
                    break

        except Exception as e:
            logger.exception("Error while executing agent")
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:
        return False

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
```

---

## File: `{{AGENT_NAME}}/agent/mcp_client_connector.py`

**Only generate this file if MCP tools are required.**

```python
# agent/mcp_client_connector.py
"""MCP client — connects to the {{MCP_SERVER_NAME}} server via stdio (default) or HTTP."""

import logging
import os

from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


async def get_mcp_client() -> MultiServerMCPClient:
    """
    Return a MultiServerMCPClient connected to the {{MCP_SERVER_NAME}} server.

    Set {{MCP_ENV_PREFIX}}_MCP_URL=http://localhost:8000/mcp to use HTTP instead of stdio.
    """
    mcp_url = os.getenv("{{MCP_ENV_PREFIX}}_MCP_URL")

    if mcp_url:
        logger.info(f"Connecting to {{MCP_SERVER_NAME}} via HTTP: {mcp_url}")
        mcp_config = {
            "{{MCP_SERVER_SLUG}}": {
                "url": mcp_url,
                "transport": "streamable_http",
            }
        }
    else:
        logger.info("Spawning {{MCP_SERVER_NAME}} via stdio")
        mcp_config = {
            "{{MCP_SERVER_SLUG}}": {
                "transport": "stdio",
                "command": "python",
                "args": ["{{MCP_SERVER_SLUG}}_mcp_server.py"],
                "cwd": os.path.join(os.path.dirname(__file__), "..", "mcp"),
                "env": {**os.environ},
            }
        }

    client = MultiServerMCPClient(mcp_config)
    logger.info(f"MCP client configured ({'HTTP' if mcp_url else 'stdio'})")
    return client
```

---

## File: `{{AGENT_NAME}}/README.md`

```markdown
# {{AGENT_TITLE}}

{{AGENT_DESCRIPTION}}

## Setup

1. Copy the environment file and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Mac/Linux
   # .venv\Scripts\activate.bat     # Windows cmd
   # .venv\Scripts\Activate.ps1     # Windows PowerShell
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running

Start the agent:
```bash
python main.py
```

Agent runs on `http://localhost:{{PORT}}`.

## Testing

```bash
# Check agent card
curl http://localhost:{{PORT}}/.well-known/agent.json

# Send a message
curl -X POST http://localhost:{{PORT}}/ \
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
        "parts": [{"kind": "text", "text": "{{EXAMPLE_1}}"}]
      }
    }
  }'
```
```

> **Note:** The `## Running` section should mention any prerequisites specific to this agent (e.g. a Strava auth script, API credentials). If `agent-intent.md` describes a setup step that must happen before `python main.py`, add it here.
> Fiori UI and Joule sections are added by their respective generation skills — do not add them here.

---

## Step 4 — Confirm

After writing all files, print a summary table of what was created:

```
Created:
  {{AGENT_NAME}}/requirements.txt
  {{AGENT_NAME}}/.gitignore
  {{AGENT_NAME}}/.env.example
  {{AGENT_NAME}}/README.md
  {{AGENT_NAME}}/main.py
  {{AGENT_NAME}}/agent/__init__.py
  {{AGENT_NAME}}/agent/agent.py         (Variant A/B/C)
  {{AGENT_NAME}}/agent/agent_executor.py
  {{AGENT_NAME}}/agent/mcp_client_connector.py   (if MCP)
```

Then tell the user which skills to run next based on their configuration:
- Run **`agent-mcp`** if MCP tools are required.
- Run **`agent-fiori`** if Fiori UI is required.
- Run **`agent-joule`** if Joule integration is required.
- Otherwise the project is ready — install deps with `pip install -r requirements.txt` and start with `python main.py`.
