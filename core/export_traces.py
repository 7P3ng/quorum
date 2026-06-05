"""Export the SQLite trace store to a static JSON the UI reads.

Keeping the UI on a committed static file (no DB driver in Node) means it
static-exports, deploys anywhere, and is trivially GIF-recordable.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any

from core.tracing import TraceStore


def _build_tree(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {s["id"]: {**s, "children": []} for s in spans}
    roots: list[dict[str, Any]] = []
    for s in spans:
        node = by_id[s["id"]]
        parent = s.get("parent_id")
        if parent and parent in by_id:
            by_id[parent]["children"].append(node)
        else:
            roots.append(node)
    return roots


def build_payload(store: TraceStore) -> dict[str, Any]:
    runs = store.query_runs()
    detail: dict[str, Any] = {}
    for r in runs:
        spans = store.query(r["run_id"])
        detail[r["run_id"]] = {"spans": spans, "tree": _build_tree(spans)}
    return {"generated_at": time.time(), "runs": runs, "runs_detail": detail}


def export(db_path: str = "traces.db", out_path: str = "ui/public/traces.json") -> str:
    store = TraceStore(db_path)
    try:
        payload = build_payload(store)
    finally:
        store.close()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Export trace store -> JSON for the UI")
    ap.add_argument("--db", default="traces.db")
    ap.add_argument("--out", default="ui/public/traces.json")
    args = ap.parse_args()
    path = export(args.db, args.out)
    print(f"exported traces -> {path}")
