"""Run the code-review pipeline on the held-out target (real-world-style code with
unseeded bugs). Live DeepSeek run; honours the same QUORUM_EVAL_LIVE gate.

Ground truth (3 genuine bugs, author-verified):
  1. RateLimiter.allow: self.tokens is never capped at capacity -> unbounded burst
     after an idle period (should be min(capacity, tokens + elapsed*rate)).
  2. LRUCache.get: a hit does not update recency, so the LRU order is wrong.
  3. LRUCache.put: evicts self.order.pop() (most-recent / LIFO) instead of pop(0)
     (least-recent), so it evicts the wrong entry.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.router import Router
from core.tracing import TraceStore
from core.types import Tier
from pipelines.code_review.pipeline import run_code_review

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "evals", "results")

GROUND_TRUTH = [
    "RateLimiter.allow: tokens never capped at capacity (burst overflow)",
    "LRUCache.get: hit does not update recency",
    "LRUCache.put: evicts most-recent instead of least-recent",
]


def main() -> int:
    if os.environ.get("QUORUM_EVAL_LIVE") != "1":
        print("Held-out run needs QUORUM_EVAL_LIVE=1 + a DeepSeek key (OSSLLM_API_KEY).",
              file=sys.stderr)
        return 1
    from core.deepseek_client import DeepSeekClient
    code = open(os.path.join(HERE, "ratelimit.py")).read()
    client = DeepSeekClient()
    store = TraceStore(os.path.join(ROOT, "traces.db"))
    clients: dict[Tier, object] = {t: client for t in Tier}
    router = Router(clients, store, max_concurrency=4)  # type: ignore[arg-type]
    res = run_code_review({"ratelimit.py": code}, router, k=3, force_tier=Tier.DEEPSEEK)

    kept = [{"line": v.finding.line, "severity": v.finding.severity,
             "category": v.finding.category, "title": v.finding.title,
             "votes": f"{v.verdict.upheld_votes}-{v.verdict.refuted_votes}"} for v in res.kept]
    out = {"target": "ratelimit.py", "model": "deepseek (tier-0)",
           "n_candidates": res.summary["n_candidates"], "n_kept": res.summary["n_kept"],
           "ground_truth_bugs": GROUND_TRUTH, "kept_findings": kept}
    os.makedirs(RESULTS, exist_ok=True)
    json.dump(out, open(os.path.join(RESULTS, "holdout.json"), "w"), indent=2)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
