"""OpenTelemetry GenAI / agent spans for the FastPay copilot.

Span shapes follow the development GenAI semantic conventions:
invoke_agent (INTERNAL), chat (CLIENT), execute_tool (INTERNAL),
retrieval (CLIENT), and a custom guardrail INTERNAL span.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PAN_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

_MEMORY: InMemorySpanExporter | None = None
_PROVIDER: TracerProvider | None = None


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k.lower() in {"email", "ssn", "ssn_last4", "pan", "pan_last4"}:
                out[k] = "[REDACTED]"
            else:
                out[k] = redact(v)
        return out
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
        value = PAN_RE.sub("[REDACTED_PAN]", value)
        return value
    return value


def _dumps(value: Any) -> str:
    return json.dumps(redact(value), default=str)


def configure_tracer(service_name: str = "agent-trace-eval") -> tuple[Tracer, InMemorySpanExporter]:
    """Idempotent: OTel forbids replacing the global TracerProvider."""
    global _MEMORY, _PROVIDER
    if _PROVIDER is not None and _MEMORY is not None:
        _MEMORY.clear()
        return trace.get_tracer("agent-trace-eval", "0.1.0"), _MEMORY
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "service.version": "0.1.0",
            }
        )
    )
    memory = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory))
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _PROVIDER = provider
    _MEMORY = memory
    return trace.get_tracer("agent-trace-eval", "0.1.0"), memory


def memory_exporter() -> InMemorySpanExporter | None:
    return _MEMORY


def set_json(span: Span, key: str, value: Any) -> None:
    span.set_attribute(key, _dumps(value))


@contextmanager
def invoke_agent_span(
    tracer: Tracer,
    *,
    agent_name: str,
    conversation_id: str | None,
    model: str,
    prompt: str,
) -> Iterator[Span]:
    attrs = {
        "gen_ai.operation.name": "invoke_agent",
        "gen_ai.agent.name": agent_name,
        "gen_ai.agent.version": "0.1.0",
        "gen_ai.agent.description": "FastPay payment-exception copilot",
        "gen_ai.request.model": model,
        "gen_ai.output.type": "json",
        "gen_ai.provider.name": "heuristic" if model == "heuristic" else "openai",
    }
    if conversation_id:
        attrs["gen_ai.conversation.id"] = conversation_id
    with tracer.start_as_current_span(
        f"invoke_agent {agent_name}",
        kind=SpanKind.INTERNAL,
        attributes=attrs,
    ) as span:
        set_json(span, "gen_ai.input.messages", [{"role": "user", "parts": [{"type": "text", "content": prompt}]}])
        try:
            yield span
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.set_attribute("error.type", type(exc).__name__)
            raise


@contextmanager
def chat_span(tracer: Tracer, *, model: str, provider: str) -> Iterator[Span]:
    with tracer.start_as_current_span(
        f"chat {model}",
        kind=SpanKind.CLIENT,
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": provider,
            "gen_ai.request.model": model,
            "gen_ai.request.temperature": 0.0,
        },
    ) as span:
        yield span


@contextmanager
def execute_tool_span(
    tracer: Tracer,
    *,
    tool_name: str,
    call_id: str,
    arguments: dict[str, Any],
    description: str,
) -> Iterator[Span]:
    with tracer.start_as_current_span(
        f"execute_tool {tool_name}",
        kind=SpanKind.INTERNAL,
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": tool_name,
            "gen_ai.tool.type": "function",
            "gen_ai.tool.call.id": call_id,
            "gen_ai.tool.description": description,
        },
    ) as span:
        set_json(span, "gen_ai.tool.call.arguments", arguments)
        yield span


@contextmanager
def retrieval_span(tracer: Tracer, *, query: str, top_k: int) -> Iterator[Span]:
    with tracer.start_as_current_span(
        "retrieval fastpay-runbooks",
        kind=SpanKind.CLIENT,
        attributes={
            "gen_ai.operation.name": "retrieval",
            "gen_ai.data_source.id": "fastpay-runbooks",
            "gen_ai.request.top_k": top_k,
            "gen_ai.provider.name": "heuristic",
        },
    ) as span:
        span.set_attribute("gen_ai.retrieval.query.text", redact(query) if isinstance(query, str) else query)
        yield span


@contextmanager
def guardrail_span(tracer: Tracer, *, policy_id: str, tool_name: str) -> Iterator[Span]:
    with tracer.start_as_current_span(
        f"guardrail {policy_id}",
        kind=SpanKind.INTERNAL,
        attributes={
            "gen_ai.operation.name": "guardrail",
            "gen_ai.guardrail.id": policy_id,
            "gen_ai.tool.name": tool_name,
        },
    ) as span:
        yield span
