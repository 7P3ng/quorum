from core.export_traces import build_payload
from core.tracing import TraceStore


def test_payload_has_runs_and_nested_tree():
    s = TraceStore(":memory:")
    run = s.new_run(label="t")
    with s.span("root", run_id=run) as root:
        root.record(cost_usd=0.1)
        with s.span("child", run_id=run, parent=root.id) as ch:
            ch.record(cost_usd=0.2)
    payload = build_payload(s)
    assert any(r["run_id"] == run for r in payload["runs"])
    tree = payload["runs_detail"][run]["tree"]
    assert len(tree) == 1 and tree[0]["name"] == "root"
    assert tree[0]["children"][0]["name"] == "child"
