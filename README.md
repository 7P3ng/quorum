# Quorum

**A task-aware agent orchestrator: cost-aware model routing · adversarial multi-agent verification · every agent call traced · a trace UI that actually looks like a product.**

Quorum is a small, production-shaped substrate for running LLM agents. It routes each
task to the cheapest model tier likely to get it right, verifies findings with K
independent skeptics before trusting them, and records every call (model, tier decision,
tokens, cost, latency, retries, outcome) into a store a clean UI reads back. It proves
itself on **one** real pipeline built to research depth — autonomous code review — and
reports a **measured** result, not vibes.

![Quorum trace UI](docs/assets/trace-ui.gif)

## Headline results

1. **Verification** — K=3 adversarial verification cut the false-positive rate on clean
   code from **50.0% → 0.0%** (recall 100.0% → 66.7%) on a 24-snippet labeled bug set,
   using DeepSeek as the model. Reproducible offline: `make eval-dry`.
   ([methodology + ablation](docs/writeup.md#1-claim-2--adversarial-verification-cuts-false-positives))
2. **Routing** — tiered routing (DeepSeek → Haiku → Sonnet → Opus) holds task success at
   a fraction of all-Opus cost. The harness + benchmark are committed; the live
   multi-tier number is operator-gated on an `ANTHROPIC_API_KEY`
   ([reproduce](docs/writeup.md#2-claim-1--tiered-routing-holds-quality-at-lower-cost)).

> Numbers are produced by `evals/run_evals.py` and committed under `evals/results/`.
> Nothing here is fabricated; the routing live number awaits a key and says so.

## Run it

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

make test          # full kernel + pipeline test suite — zero network
make eval-dry      # reproduce the verification table from committed fixtures — zero cost
make pipeline-demo # run the code-review pipeline on a demo target (offline fakes)
```

See the trace UI:

```bash
make export                       # SQLite traces -> ui/public/traces.json
cd ui && npm install && npm run build && npx serve out   # static, no backend
```

Live runs (paid, opt-in) are gated and documented in [docs/writeup.md](docs/writeup.md):

```bash
export ANTHROPIC_API_KEY=sk-ant-...      # routing claim
source your-deepseek-env                  # OSSLLM_API_KEY for the verification claim
QUORUM_EVAL_LIVE=1 make eval-live          # prints a cost estimate before any paid call
```

## Architecture

![architecture](docs/architecture.svg)

- **`core/router.py`** — cost-aware tier selection with a fallback ladder (escalate on
  rate-limit/error) and a concurrency cap. Routing policy is a pure, swappable function.
- **`core/orchestrator.py`** — parallel fan-out, retry-with-backoff, idempotency, and
  graceful degradation: one agent failing never fails the run.
- **`core/tracing.py`** — every call is a span in a run tree, persisted to SQLite.
- **`core/dispatcher.py`** — thin intent classifier that picks the pipeline for a target.
- **`pipelines/code_review/`** — finders fan out over a target; each candidate finding is
  refuted by K perspective-diverse skeptics; only majority-survivors are kept.
- **`evals/`** — labeled benchmarks + a dry-run-by-default harness that reproduces the
  headline numbers.
- **`ui/`** — a static Next.js + Tailwind trace viewer: run list, agent decision tree,
  token/cost timeline, per-tier cost breakdown, failure→recovery markers.

## Design choices

- **One mockable model interface** (`core/model_client.py`) so the whole spine is tested
  with zero paid calls and dry-run evals replay recorded fixtures deterministically.
- **Dry-run by default + a hard cost gate** — live evals need `QUORUM_EVAL_LIVE=1`, print
  an estimate before the first paid call, and refuse runs over `QUORUM_EVAL_MAX_USD`.
- **Fail loud** — missing keys and unpriced models raise with actionable messages; a
  dry-run never silently falls back to a live or empty response.
- **Scope discipline** — one pipeline built deep beats three half-built ones. The
  dispatcher is thin; the `research` pipeline is a registered seam, intentionally not
  built here.

## Repo layout

```
core/        router · orchestrator · tracing · dispatcher · model clients · pricing
pipelines/   code_review/  (finder · verifier · pipeline · prompts · schema)
evals/       benchmark/ (bugs + routing) · fixtures/ · run_evals.py · grade.py · results/
ui/          Next.js static trace viewer
docs/        writeup.md (methodology + ablations) · architecture.svg · assets/
tests/       57 tests, no network
```

Built phase-by-phase — see `git log`. Tech: Python 3.10+ (stdlib + `anthropic` + `httpx`),
SQLite, Next.js 15 + React + Tailwind v4.
