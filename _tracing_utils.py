from typing import List
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace import ReadableSpan, Span
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult, SimpleSpanProcessor


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
# Initialize and register tracer + exporter
exporter = InMemorySpanExporter()
trace.set_tracer_provider(
    TracerProvider()
)
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(exporter))
tracer = trace.get_tracer(__name__)