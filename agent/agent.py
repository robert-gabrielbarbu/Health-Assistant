# app/agent.py
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


class CoachAgent:
    """
    Personal health assistant agent.
    Combines Strava workout data with Withings biometric data to provide
    holistic health insights. Never fabricates data.
    """

    SYSTEM_INSTRUCTION = (
        "You are a personal health assistant with two capabilities:\n\n"
        "1. FITNESS & BIOMETRIC DATA: You have access to the user's Strava workout data "
        "(activities, HR, pace, power) via tools. Always fetch real data before answering fitness questions.\n\n"
        "2. MEDICAL DOCUMENT TRANSLATION: When the user provides a medical document or text, "
        "you MUST translate it into plain language using exactly this structure:\n"
        "   **What this document says** — 2-3 simple sentences, no jargon\n"
        "   **What you should do next** — clear bullet point action steps\n"
        "   **Recommendations** — practical advice bullets\n"
        "   **Don't panic** — reassurance about what is normal and not an emergency\n"
        "   Never refuse to translate a medical document. Always respond with the above structure.\n\n"
        "When asked about training or workouts:\n"
        "- Fetch Strava data first, then give a day-by-day plan with HR zone targets.\n\n"
        "Never fabricate fitness data — always call the tools first.\n"
        f"Today's date is {datetime.now().strftime('%Y-%m-%d')}.\n\n"
        "Tone: clear, supportive, concise. No filler phrases. Never refuse a medical translation request."
    )

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        base_url = os.getenv("LITELLM_BASE_URL", "").rstrip("/")
        api_key = os.getenv("LITELLM_API_KEY", "")
        model = os.getenv("LITELLM_MODEL", "anthropic--claude-sonnet-4-6")
        self.model = ChatOpenAI(base_url=base_url, api_key=api_key, model=model, temperature=0, max_tokens=4096)
        self.graph = None

    async def init_agent(self):
        global mcp_client
        if mcp_client is None:
            logger.info("Initializing Health MCP client...")
            mcp_client = await mcp_client_connector.get_mcp_client()
            logger.info("Health MCP client initialized")

        tools = await mcp_client.get_tools()
        logger.info(f"Loaded {len(tools)} Health MCP tools: {[t.name for t in tools]}")

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
        """Stream agent responses. Yields working updates then a final result."""
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
                    "content": "Fetching health data...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Analysing health data...",
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
            "content": "Unable to produce a response. Please provide more details.",
        }
