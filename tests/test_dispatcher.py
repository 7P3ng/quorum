from core.dispatcher import classify_heuristic, dispatch


def test_code_file_path_routes_to_code_review():
    assert dispatch("src/app/checkout.py").pipeline == "code_review"


def test_diff_routes_to_code_review():
    diff = "diff --git a/x.py b/x.py\n@@ -1,3 +1,4 @@\n+def f():\n"
    assert dispatch(diff).pipeline == "code_review"


def test_bug_request_routes_to_code_review():
    assert dispatch("Please review this PR and find any bugs").pipeline == "code_review"


def test_research_question_routes_to_research_seam():
    r = dispatch("What are the latest papers comparing retrieval methods?")
    assert r.pipeline == "research"
    assert r.available is False     # registered but not built (Phase 7)


def test_code_review_is_available_with_config():
    r = dispatch("auth.py")
    assert r.available is True
    assert r.config["k"] == 3


def test_heuristic_returns_confidence():
    name, conf = classify_heuristic("def f(): return 1")
    assert name == "code_review" and 0.0 < conf <= 1.0
