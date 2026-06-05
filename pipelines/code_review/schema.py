"""Findings schema for the code-review pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class CandidateFinding:
    file: str
    line: int
    severity: str          # low | medium | high | critical
    category: str          # correctness | security | resource | concurrency | ...
    title: str
    rationale: str
    finder_id: str = "finder"

    @property
    def dedup_key(self) -> tuple[str, int, str]:
        return (self.file, self.line, self.category)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Verdict:
    upheld_votes: int
    refuted_votes: int
    kept: bool
    skeptic_notes: list[str] = field(default_factory=list)


@dataclass
class VerifiedFinding:
    finding: CandidateFinding
    verdict: Verdict

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding": self.finding.to_dict(),
            "verdict": {
                "upheld_votes": self.verdict.upheld_votes,
                "refuted_votes": self.verdict.refuted_votes,
                "kept": self.verdict.kept,
                "skeptic_notes": self.verdict.skeptic_notes,
            },
        }
