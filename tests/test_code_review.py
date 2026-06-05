import pytest

from core.model_client import FakeClient
from core.router import Router
from core.tracing import TraceStore
from core.types import Tier
from pipelines.code_review.finder import find_in_file, dedupe
from pipelines.code_review.verifier import verify
from pipelines.code_review.pipeline import run_code_review
from pipelines.code_review.schema import CandidateFinding
from pipelines.code_review.prompts import FINDER_SYSTEM, SKEPTIC_SYSTEM


def _router(responder, max_concurrency=8):
    store = TraceStore(":memory:")
    clients = {t: FakeClient(responder) for t in Tier}
    return Router(clients, store, max_concurrency=max_concurrency)


# ---- finder ----

def test_finder_parses_json_findings():
    r = _router(lambda m, s, msgs, mt:
                '[{"line": 4, "severity": "high", "category": "correctness",'
                ' "title": "bug", "rationale": "because"}]')
    run = r.store.new_run()
    found = find_in_file("a.py", "x=1\n", r, run_id=run)
    assert len(found) == 1
    assert found[0].line == 4 and found[0].category == "correctness"


def test_finder_malformed_json_yields_empty_not_crash():
    r = _router(lambda m, s, msgs, mt: "sorry, I could not produce JSON")
    run = r.store.new_run()
    assert find_in_file("a.py", "x=1\n", r, run_id=run) == []


def test_dedupe_collapses_same_file_line_category():
    a = CandidateFinding("f", 1, "high", "correctness", "t", "r", "lensA")
    b = CandidateFinding("f", 1, "low", "correctness", "t2", "r2", "lensB")
    assert len(dedupe([a, b])) == 1


# ---- verifier (majority + conservative tie-break) ----

def _vote_router(votes):
    """votes: list of 'real'/'not_a_bug' served in order across skeptic calls."""
    seq = iter(votes)

    def responder(m, s, msgs, mt):
        v = next(seq)
        return f'{{"verdict": "{v}", "reason": "r"}}'

    # serialize skeptic calls so the vote order is deterministic
    return _router(responder, max_concurrency=1)


def test_verify_majority_refute_drops_finding():
    r = _vote_router(["not_a_bug", "not_a_bug", "real"])
    run = r.store.new_run()
    f = CandidateFinding("a.py", 1, "high", "correctness", "t", "r")
    vd = verify(f, "code", r, run_id=run, k=3)
    assert vd.kept is False and vd.refuted_votes == 2


def test_verify_majority_uphold_keeps_finding():
    r = _vote_router(["real", "real", "not_a_bug"])
    run = r.store.new_run()
    f = CandidateFinding("a.py", 1, "high", "correctness", "t", "r")
    vd = verify(f, "code", r, run_id=run, k=3)
    assert vd.kept is True and vd.upheld_votes == 2


def test_verify_k0_keeps_all_no_calls():
    r = _vote_router([])  # no skeptic should be called
    run = r.store.new_run()
    f = CandidateFinding("a.py", 1, "high", "correctness", "t", "r")
    vd = verify(f, "code", r, run_id=run, k=0)
    assert vd.kept is True and vd.upheld_votes == 0


# ---- pipeline end-to-end ----

def test_pipeline_keeps_real_drops_spurious_and_traces():
    def responder(m, s, msgs, mt):
        prompt = "".join(str(x.get("content", "")) for x in msgs)
        if s == FINDER_SYSTEM:
            if "buggy.py" in prompt:
                return ('[{"line": 1, "severity": "high", "category": "correctness",'
                        ' "title": "real off-by-one", "rationale": "x"}]')
            return ('[{"line": 1, "severity": "low", "category": "style",'
                    ' "title": "spurious nit", "rationale": "y"}]')
        if s == SKEPTIC_SYSTEM:
            if "real off-by-one" in prompt:
                return '{"verdict": "real", "reason": "ok"}'
            return '{"verdict": "not_a_bug", "reason": "fine"}'
        return "[]"

    r = _router(responder)
    target = {"buggy.py": "a[i] for i in range(len(a)+1)\n", "clean.py": "y = 2\n"}
    res = run_code_review(target, r, k=3)
    titles = {v.finding.title for v in res.kept}
    assert "real off-by-one" in titles
    assert "spurious nit" not in titles
    assert res.summary["n_candidates"] == 2 and res.summary["n_kept"] == 1
    # full trace tree present: root + finder calls + skeptic calls
    rows = r.store.query(res.run_id)
    names = [row["name"] for row in rows]
    assert "code_review" in names
    assert names.count("model_call") >= 2 + 3  # 2 finders + >=3 skeptics


def test_parse_findings_handles_brackets_inside_strings():
    """Regression: JSON extraction must not miscount brackets inside string values."""
    from pipelines.code_review.prompts import parse_findings_json, parse_verdict_json
    text = ('[{"line": 2, "severity": "high", "category": "correctness", '
            '"title": "index arr[0] out of range", "rationale": "a[i] for i in {0}"}]')
    found = parse_findings_json(text)
    assert len(found) == 1 and found[0]["line"] == 2
    assert parse_verdict_json('{"verdict": "real", "reason": "see x[0]"}')["verdict"] == "real"
