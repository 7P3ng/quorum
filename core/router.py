"""Cost-aware model routing — the author's hard-won knowledge made legible.

The router picks the *cheapest tier that should still get the task right*, then
escalates up the tier ladder if a tier rate-limits or errors. Every decision and
fallback is recorded on the call's trace span, so the routing behaviour is
auditable (and the routing eval can measure quality-vs-cost).

Routing policy is a pure function ``(Task) -> Tier`` so it is trivially
unit-testable and swappable; ``default_policy`` encodes a sensible cost ladder.
"""
from __future__ import annotations

import threading
from dataclasses import replace
from typing import Callable, Optional

from core.model_client import ModelClient
from core.tracing import TraceStore
from core.types import (
    ModelError, ModelResponse, RateLimitError, RunOutcome, Task, Tier,
)

# kinds that are pure mechanical classification/extraction -> cheapest tier
_CHEAP_KINDS = {"classify", "extract", "route", "dispatch"}


def default_policy(task: Task) -> Tier:
    """Map a task to the cheapest tier expected to hold quality."""
    if task.kind in _CHEAP_KINDS:
        return Tier.DEEPSEEK
    if task.difficulty <= 1:
        return Tier.HAIKU
    if task.difficulty <= 3:
        return Tier.SONNET
    return Tier.OPUS


class Router:
    def __init__(
        self,
        clients: dict[Tier, ModelClient],
        store: TraceStore,
        *, policy: Callable[[Task], Tier] = default_policy,
        max_concurrency: int = 8,
    ) -> None:
        self.clients = clients
        self.store = store
        self.policy = policy
        self._sem = threading.Semaphore(max_concurrency)

    def route(self, task: Task) -> Tier:
        return self.policy(task)

    def _ladder_from(self, tier: Tier) -> list[Tier]:
        """Tiers to try, starting at ``tier`` and escalating to the most capable."""
        return [t for t in sorted(Tier) if t >= tier and t in self.clients]

    def call(
        self, task: Task, *, system: str, prompt: str, run_id: str,
        parent: Optional[str] = None, max_tokens: int = 1024,
        force_tier: Optional[Tier] = None,
    ) -> ModelResponse:
        chosen = force_tier if force_tier is not None else self.route(task)
        ladder = self._ladder_from(chosen)
        if not ladder:
            raise ModelError(f"no client registered for tier {chosen.name} or above")

        with self._sem:
            with self.store.span("model_call", run_id=run_id, parent=parent,
                                 tier=chosen) as sp:
                sp.set(task_id=task.id, task_kind=task.kind, routed_tier=chosen.name)
                retries = 0
                last_err: BaseException | None = None
                for t in ladder:
                    try:
                        resp = self.clients[t].complete(
                            model=t.model_id, system=system,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=max_tokens,
                        )
                        resp = replace(resp, tier=t)
                        sp.record_response(resp, retries=retries)
                        if t != chosen:
                            sp.set(fell_back_to=t.name)
                        return resp
                    except RateLimitError as exc:
                        last_err = exc
                        retries += 1
                        sp.set(rate_limited_on=t.name)
                    except ModelError as exc:
                        last_err = exc
                        retries += 1
                        sp.set(errored_on=t.name)
                # exhausted the ladder
                sp.record(outcome=RunOutcome.FAILED, retries=retries,
                          error=str(last_err))
                raise last_err if last_err else ModelError("no tier succeeded")
