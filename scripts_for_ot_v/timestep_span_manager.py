# timestep_span_manager.py
from contextvars import ContextVar
from opentelemetry import trace
from opentelemetry.context import attach, detach, set_span_in_context, get_current
from typing import Optional

class TimestepSpanManager:
    def __init__(self, tracer_name: str = "group_chat_system"):
        self._tracer = trace.get_tracer(tracer_name)
        self._current_span_token: Optional[object] = None
        self._current_span_context: Optional[object] = None
        self._current_span = None

    def start_timestep_span(self, label: str = "timestep") -> None:
        self._current_span = self._tracer.start_span(label)
        self._current_span_context = set_span_in_context(self._current_span)
        self._current_span_token = attach(self._current_span_context)

    def end_timestep_span(self) -> None:
        if self._current_span_token:
            detach(self._current_span_token)
        if self._current_span:
            self._current_span.end()
        self._current_span = None
        self._current_span_token = None
        self._current_span_context = None

    def get_current_context(self):
        return self._current_span_context or get_current()

    def add_event_to_current_span(self, name: str, attributes: dict):
        if self._current_span:
            self._current_span.add_event(name, attributes=attributes)
