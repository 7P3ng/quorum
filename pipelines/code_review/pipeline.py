"""End-to-end code-review pipeline: find -> adversarially verify -> emit.

Fully traced under a single run_id: a root span with finder child spans and, per
candidate, K skeptic child spans. The whole tree lands in the trace store for
the UI to render.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Optional

from core.orchestrator import fan_out
from core.router import Router
from core.types import Tier

from .finder import DEFAULT_LENSES, find_in_file
from .schema import CandidateFinding, VerifiedFinding, Verdict
from .verifier import verify


@dataclass
class CodeReviewResult:
    run_id: str
    kept: list[VerifiedFinding]
    candidates: list[CandidateFinding]
    verified: list[VerifiedFinding]
    summary: dict = field(default_factory=dict)


def run_code_review(
    target: dict[str, str], router: Router, *, run_id: Optional[str] = None,
    k: int = 3, lenses: tuple[str, ...] = DEFAULT_LENSES,
    force_tier: Tier | None = None,
) -> CodeReviewResult:
    if run_id is None:
        run_id = router.store.new_run(label="code_review")

    candidates: list[CandidateFinding] = []
    with router.store.span("code_review", run_id=run_id) as root:
        files = list(target.items())

        def find_file(item):
            f, code = item
            return find_in_file(f, code, router, run_id=run_id, parent=root.id,
                                lenses=lenses, force_tier=force_tier)

        for r in fan_out(files, find_file, max_concurrency=max(1, min(8, len(files)))):
            if r:
                candidates.extend(r)

        if k <= 0:
            verified = [VerifiedFinding(c, Verdict(0, 0, True, [])) for c in candidates]
        else:
            def verify_one(c: CandidateFinding) -> VerifiedFinding:
                vd = verify(c, target[c.file], router, run_id=run_id, parent=root.id,
                            k=k, force_tier=force_tier)
                return VerifiedFinding(c, vd)

            verified = [v for v in fan_out(candidates, verify_one,
                                           max_concurrency=max(1, min(8, len(candidates))))
                        if v is not None]

        kept = [v for v in verified if v.verdict.kept]
        root.set(n_candidates=len(candidates), n_kept=len(kept), k=k)

    summary = {"run_id": run_id, "n_candidates": len(candidates),
               "n_kept": len(kept), "k": k}
    return CodeReviewResult(run_id, kept, candidates, verified, summary)


# --- offline demo (no API keys): canned fakes so `make pipeline-demo` always runs ---

_DEMO_TARGET = {
    "checkout.py": (
        "def apply_discount(prices, pct):\n"
        "    total = 0\n"
        "    for i in range(len(prices) + 1):   # off-by-one: indexes past the end\n"
        "        total += prices[i] * (1 - pct)\n"
        "    return total\n"
    ),
    "auth.py": (
        "def is_admin(user):\n"
        "    # candidate the finder flags but is actually correct\n"
        "    return user is not None and user.get('role') == 'admin'\n"
    ),
}


def _demo_router():
    from core.model_client import FakeClient
    from core.tracing import TraceStore
    from .prompts import FINDER_SYSTEM, SKEPTIC_SYSTEM

    def responder(model, system, messages, max_tokens):
        prompt = "".join(str(m.get("content", "")) for m in messages)
        if system == FINDER_SYSTEM:
            if "checkout.py" in prompt:
                return ('[{"line": 3, "severity": "high", "category": "correctness",'
                        ' "title": "Off-by-one in range", "rationale": "range(len+1) indexes past the list end"}]')
            return ('[{"line": 3, "severity": "medium", "category": "security",'
                    ' "title": "Missing role check", "rationale": "may not verify admin role"}]')
        if system == SKEPTIC_SYSTEM:
            # uphold the real off-by-one; refute the spurious auth finding
            if "Off-by-one" in prompt:
                return '{"verdict": "real", "reason": "range(len+1) raises IndexError"}'
            return '{"verdict": "not_a_bug", "reason": "role is checked correctly"}'
        return "[]"

    store = TraceStore("traces.db")
    clients = {t: FakeClient(responder) for t in Tier}
    return Router(clients, store)


def _demo() -> None:
    router = _demo_router()
    res = run_code_review(_DEMO_TARGET, router, k=3)
    print(f"run_id={res.run_id}")
    print(f"candidates={res.summary['n_candidates']} kept={res.summary['n_kept']} (k=3)")
    for v in res.kept:
        f = v.finding
        print(f"  KEPT  {f.file}:{f.line} [{f.severity}] {f.title} "
              f"({v.verdict.upheld_votes}-{v.verdict.refuted_votes})")
    dropped = [v for v in res.verified if not v.verdict.kept]
    for v in dropped:
        f = v.finding
        print(f"  DROP  {f.file}:{f.line} {f.title} "
              f"({v.verdict.upheld_votes}-{v.verdict.refuted_votes}) — refuted by skeptics")
    print("\nTrace written to traces.db. Run `make export && make ui-dev` to view it.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Quorum code-review pipeline")
    ap.add_argument("--demo", action="store_true", help="run the offline canned demo")
    args = ap.parse_args()
    if args.demo:
        _demo()
    else:
        ap.print_help()
