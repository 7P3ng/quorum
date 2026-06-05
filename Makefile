.PHONY: help test eval-dry eval-live pipeline-demo export ui-dev ui-build clean

help:
	@echo "Quorum targets:"
	@echo "  make test          - run the unit test suite (no network)"
	@echo "  make eval-dry      - reproduce headline tables from committed fixtures (zero cost)"
	@echo "  make eval-live     - LIVE eval (requires QUORUM_EVAL_LIVE=1 + API keys; prints cost first)"
	@echo "  make pipeline-demo - run the code-review pipeline on the demo target (dry-run fixtures)"
	@echo "  make export        - export the latest trace store to ui/public/traces.json"
	@echo "  make ui-dev        - run the trace UI dev server (auto-picks a free port from 3010)"
	@echo "  make ui-build      - static-export the trace UI to ui/out"

test:
	python3 -m pytest

eval-dry:
	python3 evals/run_evals.py --claim all

eval-live:
	QUORUM_EVAL_LIVE=1 python3 evals/run_evals.py --claim all

pipeline-demo:
	python3 -m pipelines.code_review.pipeline --demo

export:
	python3 -m core.export_traces

ui-dev:
	cd ui && npm run dev

ui-build:
	cd ui && npm run build

clean:
	rm -f *.db traces.db
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
