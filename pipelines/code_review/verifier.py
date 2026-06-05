"""Adversarial verification: K independent skeptics try to refute each finding.

A finding survives only on a strict majority of "real" votes (ties and failed
skeptics resolve toward *refute* — the conservative bias that cuts false
positives). Each skeptic attacks from a different angle (persona) so the panel is
perspective-diverse, not redundant. This is the engine behind headline claim #2.
"""
from __future__ import annotations

from core.orchestrator import fan_out
from core.router import Router
from core.types import Task, Tier

from .prompts import SKEPTIC_SYSTEM, parse_verdict_json, persona_for, skeptic_user
from .schema import CandidateFinding, Verdict


def verify(
    finding: CandidateFinding, code: str, router: Router, *, run_id: str,
    parent: str | None = None, k: int = 3, force_tier: Tier | None = None,
    difficulty: int = 2, max_tokens: int = 1500,
) -> Verdict:
    if k <= 0:
        return Verdict(upheld_votes=0, refuted_votes=0, kept=True, skeptic_notes=[])

    def run_skeptic(i: int) -> tuple[str, str]:
        task = Task(id=f"skeptic:{finding.file}:{finding.line}:{i}", kind="verify",
                    prompt="", difficulty=difficulty)
        resp = router.call(task, system=SKEPTIC_SYSTEM,
                           prompt=skeptic_user(finding.file, code, finding, persona_for(i)),
                           run_id=run_id, parent=parent, max_tokens=max_tokens,
                           force_tier=force_tier)
        parsed = parse_verdict_json(resp.text) or {}
        verdict = "real" if parsed.get("verdict") == "real" else "not_a_bug"
        return verdict, str(parsed.get("reason", ""))[:300]

    votes = fan_out(list(range(k)), run_skeptic, max_concurrency=k)
    upheld = refuted = 0
    notes: list[str] = []
    for vote in votes:
        if vote is None:
            refuted += 1
            continue
        verdict, reason = vote
        if verdict == "real":
            upheld += 1
        else:
            refuted += 1
        if reason:
            notes.append(reason)
    return Verdict(upheld_votes=upheld, refuted_votes=refuted,
                   kept=upheld > refuted, skeptic_notes=notes[:k])
