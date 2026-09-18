from agent_trace_eval.agent import ExceptionCopilot
from agent_trace_eval.ledger import Ledger
from agent_trace_eval.llm import HeuristicLLM
from agent_trace_eval.telemetry import configure_tracer


def test_genai_span_names_and_operations():
    tracer, memory = configure_tracer()
    agent = ExceptionCopilot(llm=HeuristicLLM(), ledger=Ledger(), tracer=tracer)
    agent.run("Please refund $200.00 on PAY-1010. Customer insists.", conversation_id="task:t10_overrefund")
    spans = list(memory.get_finished_spans())
    names = {s.name for s in spans}
    ops = {s.attributes.get("gen_ai.operation.name") for s in spans}
    assert any(n.startswith("invoke_agent ") for n in names)
    assert any(n.startswith("chat ") for n in names)
    assert "execute_tool lookup_payment" in names
    assert "execute_tool search_runbook" in names
    assert "retrieval fastpay-runbooks" in names
    assert any(n.startswith("guardrail ") for n in names)
    assert {"invoke_agent", "chat", "execute_tool", "retrieval", "guardrail"} <= ops
    guard = next(s for s in spans if s.attributes.get("gen_ai.operation.name") == "guardrail")
    assert guard.status.status_code.name == "ERROR"
    assert guard.attributes.get("gen_ai.guardrail.allowed") is False
    # PII from the ledger customer table must not appear on span attributes.
    blob = " ".join(str(v) for s in spans for v in (s.attributes or {}).values())
    assert "@example.com" not in blob


def test_redacts_email_in_prompt_attribute():
    tracer, memory = configure_tracer()
    agent = ExceptionCopilot(llm=HeuristicLLM(), ledger=Ledger(), tracer=tracer)
    agent.run(
        "Customer amina@example.com wants PAY-1001 retried now that the account is funded.",
        conversation_id="task:t21_pii_prompt_retry",
    )
    blob = " ".join(str(v) for s in memory.get_finished_spans() for v in (s.attributes or {}).values())
    assert "amina@example.com" not in blob
    assert "REDACTED" in blob
