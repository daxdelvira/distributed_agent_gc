import asyncio
import random
from typing import Awaitable, Callable, List, Dict
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.trace import TracerProvider
from opentelemetry.sdk.trace import ReadableSpan, Span
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult, SimpleSpanProcessor
from opentelemetry.sdk.resources import Resource

from _types import GroupChatMessage, MessageChunk, RequestToSpeak, UIAgentConfig
from _utils import export_metrics_to_csv
from autogen_core import DefaultTopicId, MessageContext, RoutedAgent, message_handler
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from rich.console import Console
from rich.markdown import Markdown
from agent_timeslices import track_time_and_memory
from state_updater import extract_valid_json, validate_keys, apply_state_update
from unified_state_config import PREDEFINED_STATE
from unified_state import shared_unified_state
import time
import threading
import tracemalloc

export_metrics: List[Dict] = []

class TimeAndMemoryTracker:
    def __init__(self, agent_label: str, function_name: str):
        self.agent_label = agent_label
        self.function_name = function_name
        self.thread_id = threading.get_ident()

    def __enter__(self):
        self.start_time = time.perf_counter()
        tracemalloc.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.perf_counter()
        duration = end_time - self.start_time

        metric = {
            "agent": self.agent_label,
            "function": self.function_name,
            "thread_id": self.thread_id,
            "duration_sec": duration,
            "peak_memory_bytes": peak,
        }
        export_metrics.append(metric)

class InMemorySpanExporter(SpanExporter):
    def __init__(self):
        self._spans: List[ReadableSpan] = []

    def export(self, spans: List[ReadableSpan]) -> SpanExportResult:
        self._spans.extend(spans)
        return SpanExportResult.SUCCESS

    def get_finished_spans(self) -> List[ReadableSpan]:
        return self._spans

    def clear(self):
        self._spans = []

# Initialize exporter and tracer
exporter = InMemorySpanExporter()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

class BaseGroupChatAgent(RoutedAgent):
    """A group chat participant using an LLM."""

    def __init__(
        self,
        description: str,
        group_chat_topic_type: str,
        model_client: ChatCompletionClient,
        system_message: str,
        ui_config: UIAgentConfig,
    ) -> None:
        super().__init__(description=description)
        self._group_chat_topic_type = group_chat_topic_type
        self._model_client = model_client
        self._system_message = SystemMessage(content=system_message)
        self._chat_history: List[LLMMessage] = []
        self._ui_config = ui_config
        self.console = Console()
        self._state_report_message = SystemMessage(
            content=""" 
            Please provide updates to the state based on your last message and the previous state, if any. 
            Use the following JSON format, replacing the 'type' values with the actual values. 
            {
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            "editor_num_lines_edited": 0,
            "writer_topic": "None",
            "writer_total_lines_written": 0,
            "editor_feedback_addressed": True,
            }
            """
        )
        self._state_history: List[LLMMessage] = []

    @message_handler
    async def handle_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
        self._chat_history.extend(
            [
                UserMessage(content=f"Transferred to {message.body.source}", source="system"),  # type: ignore[union-attr]
                message.body,
            ]
        )

    @message_handler
    @track_time_and_memory(get_label=lambda self: self.id.type)
    async def handle_request_to_speak(self, message: RequestToSpeak, ctx: MessageContext) -> None:
        self._chat_history.append(
            UserMessage(content=f"Transferred to {self.id.type}, adopt the persona immediately.", source="system")
        )
        completion = await self._model_client.create([self._system_message] + self._chat_history)
        assert isinstance(completion.content, str)
        new_message = AssistantMessage(content=completion.content, source=self.id.type)
        self._chat_history.append(new_message)

        needsState = True
        while needsState:
            state = await self._model_client.create(
            [self._state_report_message] + self._state_history + [new_message]
            )
            parsed = extract_valid_json(state.content)
            if parsed and validate_keys(parsed, set(PREDEFINED_STATE.keys())):
                needsState = False
                with TimeAndMemoryTracker(agent_label=self.id.type, function_name="apply_state_update"):
                    apply_state_update(shared_unified_state, parsed)
                    with tracer.start_as_current_span(f"state:{self.id.type}") as span:
                        span.set_attribute("agent_id", self.id.type)

                        # Each key-value in state becomes a span attribute
                        for k, v in parsed.items():
                            attr_key = f"state.{k}"
                            try:
                                span.set_attribute(attr_key, v)
                            except Exception:
                                span.set_attribute(attr_key, str(v))
                  # type: ignore[call-arg]
        

        new_state = AssistantMessage(content=state.content, source=self.id.type)
        self._state_history.append(new_state)

        console_message = f"\n{'-'*80}\n**{self.id.type}**: {completion.content}"
        self.console.print(Markdown(console_message))

        await publish_message_to_ui_and_backend(
            runtime=self,
            source=self.id.type,
            user_message=completion.content,
            ui_config=self._ui_config,
            group_chat_topic_type=self._group_chat_topic_type,
        )


class GroupChatManager(RoutedAgent):
    def __init__(
        self,
        model_client: ChatCompletionClient,
        participant_topic_types: List[str],
        participant_descriptions: List[str],
        ui_config: UIAgentConfig,
        max_rounds: int = 3,
    ) -> None:
        super().__init__("Group chat manager")
        self._model_client = model_client
        self._num_rounds = 0
        self._participant_topic_types = participant_topic_types
        self._chat_history: List[GroupChatMessage] = []
        self._max_rounds = max_rounds
        self.console = Console()
        self._participant_descriptions = participant_descriptions
        self._previous_participant_topic_type: str | None = None
        self._ui_config = ui_config

    @message_handler
    @track_time_and_memory(get_label=lambda self: self.id.type)
    async def handle_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
        assert isinstance(message.body, UserMessage)

        self._chat_history.append(message.body)  # type: ignore[reportargumenttype,arg-type]

        # Format message history.
        messages: List[str] = []
        for msg in self._chat_history:
            if isinstance(msg.content, str):  # type: ignore[attr-defined]
                messages.append(f"{msg.source}: {msg.content}")  # type: ignore[attr-defined]
            elif isinstance(msg.content, list):  # type: ignore[attr-defined]
                messages.append(f"{msg.source}: {', '.join(msg.content)}")  # type: ignore[attr-defined,reportUnknownArgumentType]
        history = "\n".join(messages)
        # Format roles.
        roles = "\n".join(
            [
                f"{topic_type}: {description}".strip()
                for topic_type, description in zip(
                    self._participant_topic_types, self._participant_descriptions, strict=True
                )
                if topic_type != self._previous_participant_topic_type
            ]
        )
        participants = str(
            [
                topic_type
                for topic_type in self._participant_topic_types
                if topic_type != self._previous_participant_topic_type
            ]
        )

        selector_prompt = f"""You are in a role play game. The following roles are available:
{roles}.
Read the following conversation. Then select the next role from {participants} to play. Only return the role.

{history}

Read the above conversation. Then select the next role from {participants} to play. if you think it's enough talking (for example they have talked for {self._max_rounds} rounds), return 'FINISH'.
"""
        system_message = SystemMessage(content=selector_prompt)
        completion = await self._model_client.create([system_message], cancellation_token=ctx.cancellation_token)

        assert isinstance(
            completion.content, str
        ), f"Completion content must be a string, but is: {type(completion.content)}"

        if completion.content.upper() == "FINISH":
            finish_msg = "I think it's enough iterations on the story! Thanks for collaborating!"
            manager_message = f"\n{'-'*80}\n Manager ({id(self)}): {finish_msg}"
            await publish_message_to_ui(
                runtime=self, source=self.id.type, user_message=finish_msg, ui_config=self._ui_config
            )
            self.console.print(Markdown(manager_message))
            return

        selected_topic_type: str
        for topic_type in self._participant_topic_types:
            if topic_type.lower() in completion.content.lower():
                selected_topic_type = topic_type
                self._previous_participant_topic_type = selected_topic_type
                self.console.print(
                    Markdown(f"\n{'-'*80}\n Manager ({id(self)}): Asking `{selected_topic_type}` to speak")
                )
                await self.publish_message(RequestToSpeak(), DefaultTopicId(type=selected_topic_type))
                return
        raise ValueError(f"Invalid role selected: {completion.content}")


class UIAgent(RoutedAgent):
    """Handles UI-related tasks and message processing for the distributed group chat system."""

    def __init__(self, on_message_chunk_func: Callable[[MessageChunk], Awaitable[None]]) -> None:
        super().__init__("UI Agent")
        self._on_message_chunk_func = on_message_chunk_func

    @message_handler
    async def handle_message_chunk(self, message: MessageChunk, ctx: MessageContext) -> None:
        await self._on_message_chunk_func(message)


async def publish_message_to_ui(
    runtime: RoutedAgent | GrpcWorkerAgentRuntime,
    source: str,
    user_message: str,
    ui_config: UIAgentConfig,
) -> None:
    message_id = str(uuid4())
    # Stream the message to UI
    message_chunks = (
        MessageChunk(message_id=message_id, text=token + " ", author=source, finished=False)
        for token in user_message.split()
    )
    for chunk in message_chunks:
        await runtime.publish_message(
            chunk,
            DefaultTopicId(type=ui_config.topic_type),
        )
        await asyncio.sleep(random.uniform(ui_config.min_delay, ui_config.max_delay))

    await runtime.publish_message(
        MessageChunk(message_id=message_id, text=" ", author=source, finished=True),
        DefaultTopicId(type=ui_config.topic_type),
    )


async def publish_message_to_ui_and_backend(
    runtime: RoutedAgent | GrpcWorkerAgentRuntime,
    source: str,
    user_message: str,
    ui_config: UIAgentConfig,
    group_chat_topic_type: str,
) -> None:
    # Publish messages for ui
    await publish_message_to_ui(
        runtime=runtime,
        source=source,
        user_message=user_message,
        ui_config=ui_config,
    )

    # Publish message to backend
    await runtime.publish_message(
        GroupChatMessage(body=UserMessage(content=user_message, source=source)),
        topic_id=DefaultTopicId(type=group_chat_topic_type),
    )