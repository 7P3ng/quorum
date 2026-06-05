"""Thin, agentic dispatcher: read a target, pick the pipeline that fits.

Deliberately *thin* — a heuristic classifier with an optional cheap-model
tie-breaker (DeepSeek, the cheapest tier) for ambiguous inputs. It proves the
"an agent picks its own pipeline" seam without a plugin marketplace or config
DSL. The ``research`` pipeline is registered but not built in this artifact
(that is Phase 7) — dispatching to it returns a clear, honest "not available"
result rather than pretending.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from typing import Optional

from pipelines.code_review.finder import DEFAULT_LENSES

# pipeline name -> whether it is actually built in this artifact
REGISTERED_PIPELINES = {"code_review": True, "research": False}

_CODE_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
             ".rb", ".c", ".cpp", ".h", ".cs", ".php")
_CODE_SIGNALS = ("diff --git", "@@", "def ", "function ", "class ", "import ",
                 "const ", "=>", "return ", "bug", "review", "lint", "vulnerab")
_RESEARCH_SIGNALS = ("research", "papers", "literature", "summarize", "what ",
                     "why ", "how does", "compare", "find sources", "?")


@dataclass
class DispatchResult:
    pipeline: str
    confidence: float
    available: bool
    config: dict = field(default_factory=dict)


def classify_heuristic(target: str) -> tuple[str, float]:
    t = target.strip()
    low = t.lower()
    if any(low.endswith(e) for e in _CODE_EXT):
        return "code_review", 0.9
    if "diff --git" in t or t.count("@@") >= 2:
        return "code_review", 0.95
    code_hits = sum(1 for s in _CODE_SIGNALS if s in low)
    research_hits = sum(1 for s in _RESEARCH_SIGNALS if s in low)
    if code_hits > research_hits:
        return "code_review", min(0.85, 0.5 + 0.1 * code_hits)
    if research_hits > 0:
        return "research", min(0.85, 0.5 + 0.1 * research_hits)
    return "code_review", 0.5  # default to the built pipeline when truly ambiguous


def classify(target: str, router=None) -> tuple[str, float]:
    """Heuristic first; if low-confidence and a router is given, ask DeepSeek."""
    name, conf = classify_heuristic(target)
    if conf >= 0.6 or router is None:
        return name, conf
    from core.types import Task, Tier
    task = Task(id="dispatch", kind="classify", prompt=target[:400], difficulty=1)
    run_id = router.store.new_run(label="dispatch")
    resp = router.call(
        task,
        system="Classify the user's target as exactly one word: 'code_review' "
               "(it is code, a diff, a file, or a bug-finding request) or 'research' "
               "(it is a question or a literature/analysis request). One word only.",
        prompt=target[:1500], run_id=run_id, max_tokens=8, force_tier=Tier.DEEPSEEK,
    )
    guess = "research" if "research" in resp.text.lower() else "code_review"
    return guess, 0.75


def dispatch(target: str, router=None) -> DispatchResult:
    name, conf = classify(target, router)
    available = REGISTERED_PIPELINES.get(name, False)
    config = {"k": 3, "lenses": list(DEFAULT_LENSES)} if name == "code_review" else {}
    return DispatchResult(pipeline=name, confidence=round(conf, 2),
                          available=available, config=config)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Quorum dispatcher — pick a pipeline for a target")
    ap.add_argument("target", help="a file path, a diff, or a task description")
    args = ap.parse_args(argv)
    r = dispatch(args.target)
    print(f"pipeline   : {r.pipeline}")
    print(f"confidence : {r.confidence}")
    print(f"available  : {r.available}" + ("" if r.available
          else "  (registered seam — built in Phase 7, not this artifact)"))
    if r.config:
        print(f"config     : {r.config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
