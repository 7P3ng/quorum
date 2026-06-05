"""Quorum eval harness — produces the two headline numbers, reproducibly.

SAFETY MODEL (hard gate against autonomous cost blowup):
  * Default DRY-RUN: replays committed fixtures via RecordedClient. ZERO paid
    calls. `make eval-dry` reproduces the exact committed result tables offline.
  * LIVE: requires env QUORUM_EVAL_LIVE=1 AND prints an estimated token/cost
    figure BEFORE the first paid call. Refuses to run if the estimate exceeds
    QUORUM_EVAL_MAX_USD (default $1.00) unless --force is given.

CLAIMS:
  * verify  — adversarial K-skeptic verification cuts the false-positive rate on
              clean code. Runs on DeepSeek (tier-0). Ablation: K sweep {0,1,3,5}.
  * routing — tiered routing holds task success at a fraction of all-Opus cost.
              Needs Anthropic tiers; if ANTHROPIC_API_KEY is absent the harness
              prints the operator reproduce command and skips (never fabricates).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Optional

# allow `python evals/run_evals.py` to import the package without install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.model_client import ModelClient, RecordedClient, prompt_key
from core.router import Router, default_policy
from core.tracing import TraceStore
from core.types import Task, Tier

from pipelines.code_review.finder import find_in_file, DEFAULT_LENSES
from pipelines.code_review.prompts import SKEPTIC_SYSTEM, skeptic_user, parse_verdict_json, persona_for
from evals import grade

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUGS_DIR = os.path.join(ROOT, "evals", "benchmark", "bugs")
ROUTING_DIR = os.path.join(ROOT, "evals", "benchmark", "routing")
FIXTURES_DIR = os.path.join(ROOT, "evals", "fixtures")
RESULTS_DIR = os.path.join(ROOT, "evals", "results")
K_SWEEP = [0, 1, 3, 5]


def _trace_db() -> str:
    """Trace DB path; overridable via QUORUM_TRACE_DB so tests do not pollute it."""
    return os.environ.get("QUORUM_TRACE_DB", os.path.join(ROOT, "traces.db"))
K_MAX = 5


# --------------------------------------------------------------------------- IO
def load_bug_benchmark() -> tuple[dict[str, str], dict]:
    labels = json.load(open(os.path.join(BUGS_DIR, "labels.json")))
    code: dict[str, str] = {}
    for entry in labels["buggy"] + labels["clean"]:
        code[entry["id"]] = open(os.path.join(BUGS_DIR, "files", entry["file"])).read()
    return code, labels


def load_routing_benchmark() -> list[Task]:
    data = json.load(open(os.path.join(ROUTING_DIR, "tasks.json")))
    return [Task(id=t["id"], kind=t["kind"], prompt=t["prompt"],
                 difficulty=t["difficulty"], gold=t["gold"]) for t in data["tasks"]]


# ----------------------------------------------------------------- recording IO
class RecordingClient:
    """Wraps a live client and captures each response into a fixture sink."""

    def __init__(self, inner: ModelClient, sink: dict[str, dict]) -> None:
        self._inner = inner
        self._sink = sink

    def complete(self, *, model, system, messages, max_tokens):
        resp = self._inner.complete(model=model, system=system,
                                    messages=messages, max_tokens=max_tokens)
        self._sink[prompt_key(model, system, messages)] = {
            "text": resp.text, "model": resp.model,
            "input_tokens": resp.input_tokens, "output_tokens": resp.output_tokens,
            "latency_ms": resp.latency_ms, "stop_reason": resp.stop_reason,
        }
        return resp


def _load_fixtures(name: str) -> dict[str, dict]:
    path = os.path.join(FIXTURES_DIR, name)
    if not os.path.exists(path):
        return {}
    return json.load(open(path))


# --------------------------------------------------------------- verification
def _collect_votes(finding, code, router, *, run_id, parent, force_tier) -> list[str]:
    """Run K_MAX persona-diverse skeptics, return their raw verdicts in order."""
    from core.orchestrator import fan_out

    def one(i: int) -> str:
        task = Task(id=f"sk:{finding.file}:{finding.line}:{i}", kind="verify",
                    prompt="", difficulty=2)
        resp = router.call(task, system=SKEPTIC_SYSTEM,
                           prompt=skeptic_user(finding.file, code, finding, persona_for(i)),
                           run_id=run_id, parent=parent, max_tokens=800, force_tier=force_tier)
        parsed = parse_verdict_json(resp.text) or {}
        return "real" if parsed.get("verdict") == "real" else "not_a_bug"

    votes = fan_out(list(range(K_MAX)), one, max_concurrency=K_MAX)
    return [v if v is not None else "not_a_bug" for v in votes]


def _kept_at_k(votes: list[str], k: int) -> bool:
    if k <= 0:
        return True
    sub = votes[:k]
    upheld = sum(1 for v in sub if v == "real")
    return upheld > (len(sub) - upheld)


def collect_verification_raw(router: Router, code: dict, labels: dict,
                             *, force_tier: Tier) -> list[dict]:
    raw = []
    entries = [(e, True) for e in labels["buggy"]] + [(e, False) for e in labels["clean"]]
    for entry, is_buggy in entries:
        sid = entry["id"]
        run_id = router.store.new_run(label=f"verify:{sid}")
        with router.store.span("verify_snippet", run_id=run_id) as root:
            root.set(snippet=sid, buggy=is_buggy)
            cands = find_in_file(sid, code[sid], router, run_id=run_id, parent=root.id,
                                 lenses=DEFAULT_LENSES, force_tier=force_tier)
            cand_recs = []
            for c in cands:
                votes = _collect_votes(c, code[sid], router, run_id=run_id,
                                       parent=root.id, force_tier=force_tier)
                cand_recs.append({"line": c.line, "category": c.category,
                                  "title": c.title, "votes": votes})
        raw.append({"snippet": sid, "buggy": is_buggy,
                    "bug": entry.get("bug"), "candidates": cand_recs})
    return raw


def compute_verification_table(raw: list[dict]) -> dict:
    buggy = [r for r in raw if r["buggy"]]
    clean = [r for r in raw if not r["buggy"]]
    rows = []
    for k in K_SWEEP:
        clean_flags, detect_flags, kept_total = [], [], 0
        for r in clean:
            kept = [c for c in r["candidates"] if _kept_at_k(c["votes"], k)]
            kept_total += len(kept)
            clean_flags.append(len(kept) > 0)
        for r in buggy:
            kept = [c for c in r["candidates"] if _kept_at_k(c["votes"], k)]
            kept_total += len(kept)
            lines = [c["line"] for c in kept]
            detect_flags.append(grade.bug_detected(lines, r["bug"]["line"]) if r["bug"] else False)
        rows.append({"k": k,
                     "fp_rate": round(grade.fp_rate(clean_flags), 4),
                     "recall": round(grade.recall(detect_flags), 4),
                     "kept_findings": kept_total})
    fp0 = next(r["fp_rate"] for r in rows if r["k"] == 0)
    fp3 = next(r["fp_rate"] for r in rows if r["k"] == 3)
    rec0 = next(r["recall"] for r in rows if r["k"] == 0)
    rec3 = next(r["recall"] for r in rows if r["k"] == 3)
    return {"claim": "verification", "model": "deepseek (tier-0)",
            "n_buggy": len(buggy), "n_clean": len(clean),
            "headline": {"fp_at_k0_pct": round(fp0 * 100, 1),
                         "fp_at_k3_pct": round(fp3 * 100, 1),
                         "recall_at_k0_pct": round(rec0 * 100, 1),
                         "recall_at_k3_pct": round(rec3 * 100, 1)},
            "ablation_k_sweep": rows}


def _estimate_verify_cost(n_snippets: int) -> tuple[int, float]:
    # ~1 finder + ~1.5 candidates * K_MAX skeptics per snippet; ~420 in / ~70 out tokens.
    from core.pricing import cost
    calls = n_snippets * (1 + int(round(1.5 * K_MAX)))
    est = calls * cost("deepseek-chat", 420, 70)
    return calls, est


def run_verify(live: bool, max_usd: float, force: bool) -> dict:
    code, labels = load_bug_benchmark()
    n = len(labels["buggy"]) + len(labels["clean"])
    store = TraceStore(_trace_db())

    if live:
        from core.deepseek_client import DeepSeekClient
        calls, est = _estimate_verify_cost(n)
        print(f"[live] verification: ~{calls} DeepSeek calls, estimated cost ~${est:.4f} "
              f"(cap ${max_usd:.2f}).", file=sys.stderr)
        if est > max_usd and not force:
            sys.exit(f"ABORT: estimate ${est:.4f} exceeds cap ${max_usd:.2f}. "
                     f"Re-run with --force or raise QUORUM_EVAL_MAX_USD.")
        sink: dict[str, dict] = {}
        inner = DeepSeekClient()
        client: ModelClient = RecordingClient(inner, sink)
    else:
        fixtures = _load_fixtures("verify_fixtures.json")
        if not fixtures:
            print("[dry-run] no verification fixtures committed yet — run "
                  "`QUORUM_EVAL_LIVE=1 make eval-live` once to populate them.", file=sys.stderr)
            return {}
        # strict=False so we COUNT misses instead of raising — a raised KeyError
        # would be swallowed by the orchestrator's per-agent isolation and silently
        # produce zeros. We fail loud below if any fixture is missing.
        client = RecordedClient(fixtures, strict=False)

    clients = {t: client for t in Tier}      # all tiers share the DeepSeek-backed client
    router = Router(clients, store, max_concurrency=6)
    raw = collect_verification_raw(router, code, labels, force_tier=Tier.DEEPSEEK)

    if not live and isinstance(client, RecordedClient) and client.misses:
        sys.exit(
            f"DRY-RUN ABORT: {client.misses} fixture cache miss(es) "
            f"(hits={client.hits}). Committed fixtures are stale relative to the "
            f"current prompts/router — replaying them would fabricate zeros. "
            f"Re-record with `QUORUM_EVAL_LIVE=1 make eval-live`."
        )

    table = compute_verification_table(raw)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    if live:
        os.makedirs(FIXTURES_DIR, exist_ok=True)
        json.dump(sink, open(os.path.join(FIXTURES_DIR, "verify_fixtures.json"), "w"), indent=2)
        json.dump(raw, open(os.path.join(RESULTS_DIR, "verification_raw.json"), "w"), indent=2)
    json.dump(table, open(os.path.join(RESULTS_DIR, "verification.json"), "w"), indent=2)
    _write_verification_md(table)
    return table


def _write_verification_md(t: dict) -> None:
    h = t["headline"]
    lines = [
        "# Claim 2 — Adversarial verification cuts false positives",
        "",
        f"Model: **{t['model']}** · benchmark: {t['n_buggy']} buggy + {t['n_clean']} clean snippets.",
        "",
        f"**Headline:** K=3 adversarial verification cut the false-positive rate on clean "
        f"code from **{h['fp_at_k0_pct']}% → {h['fp_at_k3_pct']}%** "
        f"(recall on buggy code {h['recall_at_k0_pct']}% → {h['recall_at_k3_pct']}%).",
        "",
        "## Ablation — K sweep",
        "",
        "| K (skeptics) | False-positive rate | Recall | Kept findings |",
        "|---:|---:|---:|---:|",
    ]
    for r in t["ablation_k_sweep"]:
        lines.append(f"| {r['k']} | {r['fp_rate']*100:.1f}% | {r['recall']*100:.1f}% | {r['kept_findings']} |")
    lines += ["", "K=0 = keep every candidate (no verification). Ties / failed skeptics "
              "resolve toward *refute*.", ""]
    open(os.path.join(RESULTS_DIR, "verification.md"), "w").write("\n".join(lines))


# --------------------------------------------------------------------- routing
def run_routing(live: bool, max_usd: float, force: bool) -> dict:
    tasks = load_routing_benchmark()
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    reproduce = ("export ANTHROPIC_API_KEY=sk-ant-... && "
                 "QUORUM_EVAL_LIVE=1 python evals/run_evals.py --claim routing")

    if not (live and has_anthropic):
        msg = {"claim": "routing", "status": "gated",
               "reason": "needs ANTHROPIC_API_KEY + QUORUM_EVAL_LIVE=1 (multi-tier cost spread)",
               "reproduce": reproduce, "n_tasks": len(tasks)}
        os.makedirs(RESULTS_DIR, exist_ok=True)
        json.dump(msg, open(os.path.join(RESULTS_DIR, "routing.json"), "w"), indent=2)
        open(os.path.join(RESULTS_DIR, "routing.md"), "w").write(
            "# Claim 1 — Tiered routing holds quality at lower cost\n\n"
            "Status: **operator-gated** (multi-tier comparison needs Anthropic tiers).\n\n"
            f"Reproduce:\n\n```\n{reproduce}\n```\n")
        print(f"[routing] gated — needs ANTHROPIC_API_KEY. Reproduce: {reproduce}", file=sys.stderr)
        return msg

    # live + anthropic present
    from core.anthropic_client import AnthropicClient
    from core.deepseek_client import DeepSeekClient
    from core.pricing import cost as _cost
    est_calls = len(tasks) * 2
    est = est_calls * _cost("claude-opus-4-8", 120, 60)  # conservative upper bound
    print(f"[live] routing: ~{est_calls} calls, estimated cost ~${est:.4f} (cap ${max_usd:.2f}).",
          file=sys.stderr)
    if est > max_usd and not force:
        sys.exit(f"ABORT: estimate ${est:.4f} exceeds cap ${max_usd:.2f}.")

    store = TraceStore(_trace_db())
    anth = AnthropicClient()
    clients = {Tier.OPUS: anth, Tier.SONNET: anth, Tier.HAIKU: anth, Tier.DEEPSEEK: DeepSeekClient()}
    router = Router(clients, store, max_concurrency=4)

    def grade_task(task, force_tier) -> tuple[bool, float, str]:
        run_id = router.store.new_run(label=f"route:{task.id}:{(force_tier.name if force_tier else 'auto')}")
        resp = router.call(task, system="Answer concisely and exactly as asked.",
                           prompt=task.prompt, run_id=run_id, max_tokens=256, force_tier=force_tier)
        return grade.routing_correct(task.gold, resp.text), resp.cost_usd, (resp.tier.name if resp.tier else "?")

    base_ok = base_cost = tier_ok = tier_cost = 0
    tier_hist: dict[str, int] = {}
    for task in tasks:
        ok_o, c_o, _ = grade_task(task, Tier.OPUS)
        base_ok += ok_o; base_cost += c_o
        ok_t, c_t, tname = grade_task(task, None)  # policy-routed
        tier_ok += ok_t; tier_cost += c_t
        tier_hist[tname] = tier_hist.get(tname, 0) + 1

    n = len(tasks)
    table = {"claim": "routing", "status": "measured", "model": "anthropic tiers + deepseek",
             "n_tasks": n,
             "headline": {
                 "opus_success_pct": round(100 * base_ok / n, 1),
                 "tiered_success_pct": round(100 * tier_ok / n, 1),
                 "quality_retained_pct": round(100 * (tier_ok / base_ok), 1) if base_ok else 0.0,
                 "cost_fraction_pct": round(100 * (tier_cost / base_cost), 1) if base_cost else 0.0,
                 "opus_cost_usd": round(base_cost, 4), "tiered_cost_usd": round(tier_cost, 4)},
             "tier_distribution": tier_hist}
    os.makedirs(RESULTS_DIR, exist_ok=True)
    json.dump(table, open(os.path.join(RESULTS_DIR, "routing.json"), "w"), indent=2)
    h = table["headline"]
    open(os.path.join(RESULTS_DIR, "routing.md"), "w").write(
        "# Claim 1 — Tiered routing holds quality at lower cost\n\n"
        f"Tiered routing held **{h['quality_retained_pct']}%** of single-Opus success "
        f"at **{h['cost_fraction_pct']}%** of the cost across {n} tasks "
        f"(Opus {h['opus_success_pct']}% vs tiered {h['tiered_success_pct']}%).\n\n"
        f"Tier distribution under the policy: {tier_hist}\n")
    return table


# ------------------------------------------------------------------------- main
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Quorum eval harness")
    ap.add_argument("--claim", choices=["verify", "routing", "all"], default="all")
    ap.add_argument("--force", action="store_true", help="bypass the cost cap")
    args = ap.parse_args(argv)

    live = os.environ.get("QUORUM_EVAL_LIVE") == "1"
    max_usd = float(os.environ.get("QUORUM_EVAL_MAX_USD", "1.00"))
    mode = "LIVE (paid)" if live else "dry-run (fixtures, zero cost)"
    print(f"== Quorum evals — mode: {mode} ==", file=sys.stderr)

    if args.claim in ("verify", "all"):
        t = run_verify(live, max_usd, args.force)
        if t:
            h = t["headline"]
            print(f"[verify] FP {h['fp_at_k0_pct']}% -> {h['fp_at_k3_pct']}% "
                  f"(recall {h['recall_at_k0_pct']}% -> {h['recall_at_k3_pct']}%)")
    if args.claim in ("routing", "all"):
        run_routing(live, max_usd, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
