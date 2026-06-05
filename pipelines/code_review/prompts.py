"""Prompt templates + lenient JSON extraction for finders and skeptics.

The skeptic prompt encodes the adversarial-verification rule: *default to
refuting when uncertain*. That asymmetry trades a little recall for a large drop
in false positives — the mechanism behind headline claim #2. Each skeptic also
gets a distinct PERSONA (a different angle of attack), which both diversifies the
verification (perspective-diverse, not redundant) and gives every skeptic call a
unique prompt — so recorded eval fixtures store independent votes, not one
collapsed cache entry.
"""
from __future__ import annotations

import json
from typing import Any, Optional

FINDER_SYSTEM = (
    "You are a meticulous code reviewer. Identify REAL, triggerable bugs only — "
    "logic errors, off-by-one, wrong operators, missing null/None checks, resource "
    "leaks, race conditions, incorrect return values. Ignore style and nits.\n"
    "Respond with ONLY a JSON array. Each element: "
    '{"line": <int>, "severity": "low|medium|high|critical", '
    '"category": "correctness|security|resource|concurrency|api-misuse", '
    '"title": "<short>", "rationale": "<why it is a bug>"}. '
    "If there are no real bugs, respond with []. No prose, no markdown fences."
)

SKEPTIC_SYSTEM = (
    "You are a skeptical staff engineer reviewing a CLAIMED bug. Your job is to "
    "REFUTE it unless it is clearly a real, triggerable defect. Be conservative: "
    "if the claim is speculative, stylistic, or you are uncertain, refute it.\n"
    'Respond with ONLY JSON: {"verdict": "real" | "not_a_bug", "reason": "<one line>"}. '
    "No prose, no markdown fences."
)

# Distinct angles of attack — one per skeptic index (cycled if k exceeds the list).
SKEPTIC_PERSONAS = [
    "Angle: does this defect actually TRIGGER on realistic inputs?",
    "Angle: is the flagged code path actually REACHABLE in normal use?",
    "Angle: is this a genuine defect, or merely a style/nit preference?",
    "Angle: could a concrete unit test EXPOSE this bug as written?",
    "Angle: do guards or surrounding context already PREVENT this?",
]


def persona_for(i: int) -> str:
    return SKEPTIC_PERSONAS[i % len(SKEPTIC_PERSONAS)]


def number_code(code: str) -> str:
    return "\n".join(f"{i+1:>4}  {ln}" for i, ln in enumerate(code.splitlines()))


def finder_user(file: str, code: str, lens: str) -> str:
    return f"Review this file for {lens} bugs.\nFILE: {file}\n```\n{number_code(code)}\n```"


def skeptic_user(file: str, code: str, finding, persona: str = "") -> str:
    tail = f"\n{persona}" if persona else ""
    return (
        f"FILE: {file}\n```\n{number_code(code)}\n```\n\n"
        f"CLAIMED BUG (line {finding.line}, {finding.category}): {finding.title}\n"
        f"Reviewer's rationale: {finding.rationale}\n\n"
        f"Is this a real, triggerable bug? Refute if uncertain.{tail}"
    )


def _decode_json_at(text: str, opener: str) -> Optional[Any]:
    """Decode the first JSON value beginning at ``opener``.

    Uses ``raw_decode`` so brackets inside string literals are handled correctly
    (a hand-rolled depth counter miscounts e.g. a title like "arr[0]").
    """
    start = text.find(opener)
    if start == -1:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text, start)
        return obj
    except json.JSONDecodeError:
        return None


def parse_findings_json(text: str) -> list[dict[str, Any]]:
    obj = _decode_json_at(text, "[")
    return obj if isinstance(obj, list) else []


def parse_verdict_json(text: str) -> Optional[dict[str, Any]]:
    obj = _decode_json_at(text, "{")
    return obj if isinstance(obj, dict) else None
