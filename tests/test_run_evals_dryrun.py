"""Dry-run reproducibility: replaying committed fixtures must reproduce the
committed verification table exactly, with zero network calls.

Skips cleanly until the one live run has populated fixtures + results (so the
suite is green on a fresh clone before any live run)."""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "evals", "fixtures", "verify_fixtures.json")
RES = os.path.join(ROOT, "evals", "results", "verification.json")


@pytest.mark.skipif(not (os.path.exists(FIX) and os.path.exists(RES)),
                    reason="no committed fixtures yet — run the live eval once")
def test_dryrun_reproduces_committed_verification(monkeypatch, tmp_path):
    committed = json.load(open(RES))
    monkeypatch.delenv("QUORUM_EVAL_LIVE", raising=False)  # force dry-run
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("QUORUM_TRACE_DB", str(tmp_path / "t.db"))
    from evals.run_evals import main
    rc = main(["--claim", "verify"])
    assert rc == 0
    reproduced = json.load(open(RES))
    assert reproduced["headline"] == committed["headline"]
    assert reproduced["ablation_k_sweep"] == committed["ablation_k_sweep"]


def test_dryrun_uses_recorded_client_no_network(monkeypatch, tmp_path):
    """A dry-run must never construct a live client."""
    monkeypatch.delenv("QUORUM_EVAL_LIVE", raising=False)
    import core.deepseek_client as ds

    def _boom(*a, **k):
        raise AssertionError("dry-run must not construct a live DeepSeek client")

    monkeypatch.setattr(ds, "DeepSeekClient", _boom)
    monkeypatch.setenv("QUORUM_TRACE_DB", str(tmp_path / "t2.db"))
    from evals.run_evals import run_verify
    # returns {} gracefully if no fixtures; never constructs a live client
    run_verify(live=False, max_usd=1.0, force=False)
