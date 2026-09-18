"""Shared models for the FastPay exception-copilot eval harness."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    text: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "heuristic"
    provider: str = "heuristic"
    finish_reason: str = "stop"


class AgentResult(BaseModel):
    final_text: str
    action: str | None = None
    payment_id: str | None = None
    amount_cents: int | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    schema_errors: list[str] = Field(default_factory=list)
    guardrail_blocks: list[str] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    model: str = "heuristic"
    turns: int = 0


class TaskSpec(BaseModel):
    id: str
    prompt: str
    expected_action: str
    expected_payment_id: str | None = None
    expected_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    optional_tools: list[str] = Field(
        default_factory=lambda: [
            "get_customer",
            "list_exceptions",
            "acknowledge_exception",
            "escalate_to_ops",
        ]
    )


class TaskScore(BaseModel):
    task_id: str
    success: bool
    action: str | None
    expected_action: str
    tool_precision: float
    tool_recall: float
    schema_valid: bool
    groundedness: float
    pii_leaked: bool
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    turns: int
    detail: str = ""


class EvalReport(BaseModel):
    task_count: int
    success_rate: float
    schema_validity: float
    mean_tool_precision: float
    mean_tool_recall: float
    mean_groundedness: float
    pii_leak_rate: float
    usd_per_task: float
    p95_latency_ms: float
    total_cost_usd: float
    scores: list[TaskScore]
