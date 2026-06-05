import pytest

from evals.grade import normalize_text, routing_correct, fp_rate, recall, bug_detected


def test_routing_correct_contains():
    assert routing_correct("Paris", "The capital is Paris.")
    assert routing_correct("391", "It is 391")
    assert not routing_correct("391", "I think 392")


def test_routing_correct_whitespace_insensitive_list():
    assert routing_correct("[2, 5, 8]", "Result: [2,5,8]")


def test_routing_correct_word_answer():
    assert routing_correct("same", "They weigh the same.")
    assert not routing_correct("same", "steel is heavier")


def test_fp_rate():
    assert fp_rate([True, False, False, False]) == pytest.approx(0.25)
    assert fp_rate([]) == 0.0


def test_recall():
    assert recall([True, True, False]) == pytest.approx(2 / 3)


def test_bug_detected_tolerance():
    assert bug_detected([3, 7], 4, tol=2)        # 3 within 2 of 4
    assert not bug_detected([10], 4, tol=2)
