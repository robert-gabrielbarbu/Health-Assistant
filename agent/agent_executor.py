# app/agent_executor.py
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

from agent.agent import CoachAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoachAgentExecutor(AgentExecutor):
    """AgentExecutor for the Strava Workout Coach Agent."""

    def __init__(self):
        self.agent = CoachAgent()
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
                        name="health_response",
                    )
                    await updater.complete()
                    break

        except Exception as e:
            logger.exception("Error while executing coach agent")
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:
        return False

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
