import pytest

from core.tracing import TraceStore
from core.types import ModelResponse, RunOutcome, Tier


def test_new_run_and_empty_query():
    s = TraceStore(":memory:")
    run = s.new_run(label="demo")
    assert isinstance(run, str) and run
    assert s.query(run) == []


def test_single_span_persists_with_defaults():
    s = TraceStore(":memory:")
    run = s.new_run()
    with s.span("finder", run_id=run) as sp:
        sp.record(input_tokens=10, output_tokens=5, cost_usd=0.001)
    rows = s.query(run)
    assert len(rows) == 1
    r = rows[0]
    assert r["name"] == "finder"
    assert r["run_id"] == run
    assert r["parent_id"] is None
    assert r["outcome"] == RunOutcome.OK.value
    assert r["input_tokens"] == 10 and r["output_tokens"] == 5
    assert r["latency_ms"] >= 0
    assert r["started_at"] <= r["ended_at"]


def test_record_response_copies_fields():
    s = TraceStore(":memory:")
    run = s.new_run()
    resp = ModelResponse(text="x", model="deepseek-chat", input_tokens=7,
                         output_tokens=3, cost_usd=0.5, latency_ms=12.0, tier=Tier.DEEPSEEK)
    with s.span("call", run_id=run) as sp:
        sp.record_response(resp)
    r = s.query(run)[0]
    assert r["model"] == "deepseek-chat"
    assert r["tier"] == Tier.DEEPSEEK.value
    assert r["cost_usd"] == 0.5
    assert r["input_tokens"] == 7 and r["output_tokens"] == 3


def test_parent_child_link():
    s = TraceStore(":memory:")
    run = s.new_run()
    with s.span("verify", run_id=run) as parent:
        with s.span("skeptic", run_id=run, parent=parent.id) as child:
            child.record(input_tokens=1, output_tokens=1, cost_usd=0.0)
    rows = {r["name"]: r for r in s.query(run)}
    assert rows["skeptic"]["parent_id"] == rows["verify"]["id"]


def test_exception_marks_failed_and_reraises():
    s = TraceStore(":memory:")
    run = s.new_run()
    with pytest.raises(ValueError):
        with s.span("boom", run_id=run) as sp:
            raise ValueError("kaboom")
    r = s.query(run)[0]
    assert r["outcome"] == RunOutcome.FAILED.value
    assert "kaboom" in (r["error"] or "")


def test_query_runs_rollup():
    s = TraceStore(":memory:")
    run = s.new_run(label="rollup")
    with s.span("a", run_id=run) as sp:
        sp.record(input_tokens=0, output_tokens=0, cost_usd=0.25)
    with s.span("b", run_id=run) as sp:
        sp.record(input_tokens=0, output_tokens=0, cost_usd=0.75)
    runs = {r["run_id"]: r for r in s.query_runs()}
    assert runs[run]["label"] == "rollup"
    assert runs[run]["total_cost_usd"] == pytest.approx(1.0)
    assert runs[run]["span_count"] == 2
