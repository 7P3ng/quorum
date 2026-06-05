# Quorum — methodology & results

A short research-style note on the two claims Quorum makes, how they were measured,
and where they are weak. The numbers below are produced by `evals/run_evals.py` and
committed under `evals/results/`. The verification number is reproducible offline
(`make eval-dry`); the routing number is operator-gated on an Anthropic key (see §2).

## 0. System in one paragraph

Quorum routes each task to the cheapest model tier likely to get it right
(`core/router.py`), runs work through a fault-tolerant orchestrator
(`core/orchestrator.py`) that fans out and degrades gracefully, and records every
model call as a structured span (`core/tracing.py`) — prompt, tier decision, tokens,
cost, latency, retries, outcome. One pipeline is built to depth: autonomous code
review with **adversarial K-skeptic verification** (`pipelines/code_review/`). A
thin dispatcher (`core/dispatcher.py`) picks the pipeline for a target. Everything
talks to models through one mockable interface (`core/model_client.py`), so the whole
system is unit-tested with zero paid calls, and dry-run evals replay recorded fixtures.

## 1. Claim 2 — adversarial verification cuts false positives

**Hypothesis.** A single LLM "finder" pass over code is trigger-happy: it reports
plausible-but-wrong bugs. Asking K independent skeptics to *refute* each finding, and
keeping it only on a majority, should cut false positives sharply.

**Setup.** A labeled benchmark of 24 small snippets (`evals/benchmark/bugs/`): 12 with
exactly one seeded, triggerable bug (off-by-one, wrong operator, missing-None, resource
leak, assignment-in-condition, missing-await, silent-except, …) and 12 genuinely clean,
idiomatic counterparts. A reported bug on a clean snippet is a **false positive**.
Each skeptic attacks from a distinct angle (does it trigger? is it reachable? is it a
nit? could a test expose it? do guards prevent it?) and is told to **refute when
uncertain**. A finding survives on a strict majority of "real" votes; ties and failed
skeptics resolve toward refute.

**Metric.** False-positive rate = fraction of clean snippets on which the system reports
≥1 bug. Recall = fraction of buggy snippets whose seeded bug survives (line within ±2).

**Model.** DeepSeek (`deepseek-v4-pro`), tier-0 of the router. ~216 calls, ≈ $0.04.

**Result (committed: `evals/results/verification.md`).**

K=3 adversarial verification cut the false-positive rate on clean code from
**50.0% → 0.0%**, with recall on buggy code moving **100.0% → 66.7%**.

| K (skeptics) | False-positive rate | Recall | Kept findings |
|---:|---:|---:|---:|
| 0 (no verification) | 50.0% | 100.0% | 18 |
| 1 | 0.0% | 66.7% | 8 |
| 3 | 0.0% | 66.7% | 8 |
| 5 | 0.0% | 66.7% | 8 |

**Ablation reading.** On this benchmark the conservative skeptic *prior* does the heavy
lifting: a single skeptic (K=1) already removes every false positive. Larger K does not
reduce FP further here — its value is **stability** (robustness to a single skeptic's
variance), not additional precision. The cost is recall: verification drops 4 of 12
real bugs along with all 6 false ones. That is the honest trade — Quorum is tuned for
*precision* (don't cry wolf), which is the right bias for an autonomous reviewer a human
must trust, but it is a trade, not a free lunch.

**Threats to validity.** (a) Single model and a small (n=24) benchmark — the *direction*
is robust but the exact percentages will move with model and data. (b) The seeded bugs
are clear-cut; subtle real-world bugs would lower recall. (c) Skeptics share the finder's
model, so correlated blind spots are possible; perspective-diverse personas mitigate but
do not eliminate this. (d) Recall is line-tolerance based (±2), a deliberately lenient
detection criterion.

## 2. Claim 1 — tiered routing holds quality at lower cost

**Hypothesis.** Routing each task to the cheapest sufficient tier
(DeepSeek → Haiku → Sonnet → Opus, by `default_policy`) retains most of single-Opus
task success at a fraction of the cost.

**Setup.** 24 gold-labeled tasks (`evals/benchmark/routing/`) spanning difficulty 1–5
(factual, transform, arithmetic, code-output, reasoning), auto-graded by normalized
match. Baseline routes everything to Opus; the treatment uses the cost-aware policy.
Metrics: success rate and total cost for each, then quality-retained and cost-fraction.

**Status — operator-gated.** This comparison needs a real cost spread across Anthropic
tiers, so it requires `ANTHROPIC_API_KEY`. It is **not fabricated**. The harness builds
the clients, prints an estimated cost before the first paid call, and writes the table.
Reproduce:

```
export ANTHROPIC_API_KEY=sk-ant-...
QUORUM_EVAL_LIVE=1 python evals/run_evals.py --claim routing
```

The harness is exercised end-to-end in dry-run and unit tests; only the live multi-tier
number awaits a key.

## 3. Why this is trustworthy

- **Reproducible.** `make eval-dry` replays committed fixtures (zero network) and
  regenerates the verification table byte-for-byte; a test asserts it
  (`tests/test_run_evals_dryrun.py`).
- **Cost-gated.** Live evals require `QUORUM_EVAL_LIVE=1`, print an estimate before the
  first paid call, and refuse runs over `QUORUM_EVAL_MAX_USD` (default $1).
- **Fail-loud.** Missing keys raise with an actionable message; unknown models raise in
  pricing rather than silently costing $0; a dry-run never falls back to a live call.
- **Honest accounting.** During development a routing bug was found where
  `force_tier=Tier.DEEPSEEK` (IntEnum value 0) was silently dropped by a truthiness
  check (`force_tier or route(task)`); it is fixed and covered by a regression test
  (`tests/test_router.py::test_force_tier_deepseek_is_honored_not_falsy`). The kind of
  bug this project exists to catch.
