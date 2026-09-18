from agent_trace_eval.agent import ExceptionCopilot
from agent_trace_eval.eval import groundedness, pii_leaked, score_task, tool_precision, tool_recall
from agent_trace_eval.ledger import Ledger
from agent_trace_eval.llm import HeuristicLLM
from agent_trace_eval.models import AgentResult, TaskSpec
from agent_trace_eval.pricing import cost_usd, estimate_tokens


def test_overrefund_is_blocked_and_scores_no_action():
    spec = TaskSpec(
        id="over",
        prompt="Please refund $200.00 on PAY-1010. Customer insists.",
        expected_action="no_action",
        expected_payment_id="PAY-1010",
        expected_tools=["lookup_payment", "search_runbook", "refund_payment"],
        forbidden_tools=["retry_payment"],
    )
    agent = ExceptionCopilot(llm=HeuristicLLM(), ledger=Ledger())
    result = agent.run(spec.prompt, conversation_id="task:over")
    assert any("exceeds captured" in b or "refund blocked" in b for b in result.guardrail_blocks)
    score = score_task(spec, result)
    assert score.success
    assert result.action == "no_action"


def test_schema_invalid_tool_args():
    from agent_trace_eval.tools import Toolbox

    errors = Toolbox(Ledger()).validate("refund_payment", {"payment_id": "nope", "amount_cents": 1})
    assert errors


def test_groundedness_requires_tool_corpus():
    result = AgentResult(
        final_text='{"action":"retry","payment_id":"PAY-1001","evidence":["status=failed"]}',
        action="retry",
        payment_id="PAY-1001",
        tool_results=[{"name": "lookup_payment", "result": {"payment_id": "PAY-1001", "status": "failed"}}],
    )
    assert groundedness(result, "retry PAY-1001") == 1.0
    result.final_text = '{"action":"retry","payment_id":"PAY-1001","evidence":["status=invented_foo"]}'
    assert groundedness(result, "retry PAY-1001") < 1.0


def test_pii_detector():
    assert pii_leaked("contact amina@example.com")
    assert not pii_leaked('{"action":"retry","payment_id":"PAY-1001"}')


def test_tool_metrics():
    assert tool_recall(["lookup_payment", "retry_payment"], ["lookup_payment", "search_runbook"]) == 0.5
    prec = tool_precision(
        ["lookup_payment", "get_customer"],
        ["lookup_payment"],
        ["get_customer"],
        [],
    )
    assert prec == 1.0


def test_cost_positive_and_small():
    tokens = estimate_tokens("hello world " * 50)
    assert tokens > 0
    assert cost_usd("heuristic", 1000, 200) < 0.001
