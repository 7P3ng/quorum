import threading
import time

import pytest

from core.model_client import FakeClient
from core.orchestrator import fan_out
from core.router import Router, default_policy
from core.tracing import TraceStore
from core.types import ModelError, RateLimitError, Task, Tier


def _task(diff, kind="qa", tid="t"):
    return Task(id=tid, kind=kind, prompt="q", difficulty=diff)


def test_policy_routes_by_difficulty():
    assert default_policy(_task(1)) == Tier.HAIKU
    assert default_policy(_task(3)) == Tier.SONNET
    assert default_policy(_task(5)) == Tier.OPUS


def test_policy_cheap_kinds_use_deepseek():
    assert default_policy(_task(1, kind="classify")) == Tier.DEEPSEEK


def _ok_client():
    return FakeClient(lambda *a, **k: "ok")


def _router_all_ok(store, max_concurrency=8):
    clients = {t: _ok_client() for t in Tier}
    return Router(clients, store, max_concurrency=max_concurrency)


def test_force_tier_override():
    s = TraceStore(":memory:")
    run = s.new_run()
    r = _router_all_ok(s)
    resp = r.call(_task(1), system="s", prompt="p", run_id=run, force_tier=Tier.OPUS)
    assert resp.tier == Tier.OPUS


def test_fallback_on_rate_limit_escalates_and_traces():
    class RateLimited:
        def complete(self, **kw):
            raise RateLimitError("429")

    s = TraceStore(":memory:")
    run = s.new_run()
    clients = {Tier.HAIKU: RateLimited(), Tier.SONNET: _ok_client(), Tier.OPUS: _ok_client()}
    r = Router(clients, s)
    resp = r.call(_task(1), system="s", prompt="p", run_id=run)  # routes HAIKU -> rate limited -> SONNET
    assert resp.tier == Tier.SONNET
    span = s.query(run)[0]
    assert span["retries"] >= 1
    assert span["attrs"].get("fell_back_to") == "SONNET"


def test_all_tiers_failing_raises_and_marks_failed():
    class Boom:
        def complete(self, **kw):
            raise ModelError("down")

    s = TraceStore(":memory:")
    run = s.new_run()
    clients = {t: Boom() for t in Tier}
    r = Router(clients, s)
    with pytest.raises(ModelError):
        r.call(_task(5), system="s", prompt="p", run_id=run)
    assert s.query(run)[0]["outcome"] == "failed"


def test_concurrency_cap_enforced():
    cur = {"n": 0, "max": 0}
    lock = threading.Lock()

    class Counting:
        def complete(self, **kw):
            with lock:
                cur["n"] += 1
                cur["max"] = max(cur["max"], cur["n"])
            time.sleep(0.02)
            with lock:
                cur["n"] -= 1
            return FakeClient(lambda *a, **k: "ok").complete(**kw)

    s = TraceStore(":memory:")
    run = s.new_run()
    clients = {t: Counting() for t in Tier}
    r = Router(clients, s, max_concurrency=2)
    tasks = [_task(1, tid=f"t{i}") for i in range(6)]
    fan_out(tasks, lambda t: r.call(t, system="s", prompt="p", run_id=run),
            max_concurrency=6)
    assert cur["max"] <= 2


def test_force_tier_deepseek_is_honored_not_falsy():
    """Regression: Tier.DEEPSEEK == 0 is falsy; force_tier must still be honored."""
    s = TraceStore(":memory:")
    run = s.new_run()
    r = _router_all_ok(s)
    resp = r.call(_task(5, kind="find_bugs"), system="s", prompt="p",
                  run_id=run, force_tier=Tier.DEEPSEEK)
    assert resp.tier == Tier.DEEPSEEK
    assert s.query(run)[0]["attrs"]["routed_tier"] == "DEEPSEEK"
