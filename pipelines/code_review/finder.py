"""Bug finders: fan out one finder per review lens, parse + dedupe candidates."""
from __future__ import annotations

from typing import Optional

from core.orchestrator import fan_out
from core.router import Router
from core.types import Task, Tier

from .prompts import FINDER_SYSTEM, finder_user, parse_findings_json
from .schema import CandidateFinding

DEFAULT_LENSES: tuple[str, ...] = ("correctness",)


def _coerce(raw: dict, file: str, lens: str) -> Optional[CandidateFinding]:
    try:
        return CandidateFinding(
            file=file,
            line=int(raw.get("line", 0) or 0),
            severity=str(raw.get("severity", "medium")),
            category=str(raw.get("category", "correctness")),
            title=str(raw.get("title", "")).strip()[:200],
            rationale=str(raw.get("rationale", "")).strip()[:600],
            finder_id=lens,
        )
    except (ValueError, TypeError):
        return None


def dedupe(cands: list[CandidateFinding]) -> list[CandidateFinding]:
    seen: dict[tuple, CandidateFinding] = {}
    for c in cands:
        seen.setdefault(c.dedup_key, c)
    return list(seen.values())


def find_in_file(
    file: str, code: str, router: Router, *, run_id: str,
    parent: str | None = None, lenses: tuple[str, ...] = DEFAULT_LENSES,
    force_tier: Tier | None = None, difficulty: int = 3, max_tokens: int = 1500,
) -> list[CandidateFinding]:
    def run_lens(lens: str) -> list[CandidateFinding]:
        task = Task(id=f"find:{file}:{lens}", kind="find_bugs", prompt=file,
                    difficulty=difficulty)
        resp = router.call(task, system=FINDER_SYSTEM,
                           prompt=finder_user(file, code, lens), run_id=run_id,
                           parent=parent, max_tokens=max_tokens, force_tier=force_tier)
        out = [_coerce(raw, file, lens) for raw in parse_findings_json(resp.text)]
        return [c for c in out if c is not None]

    results = fan_out(list(lenses), run_lens, max_concurrency=max(1, len(lenses)))
    candidates: list[CandidateFinding] = []
    for r in results:
        if r:
            candidates.extend(r)
    return dedupe(candidates)
