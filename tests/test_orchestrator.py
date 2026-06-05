import threading
import time

import pytest

from core.orchestrator import fan_out, memoize, pipeline, retry


def test_fan_out_preserves_order():
    assert fan_out([1, 2, 3], lambda x: x * 2, max_concurrency=3) == [2, 4, 6]


def test_fan_out_graceful_degradation():
    def fn(x):
        if x == 2:
            raise RuntimeError("boom")
        return x

    assert fan_out([1, 2, 3], fn, max_concurrency=3) == [1, None, 3]


def test_fan_out_respects_concurrency_cap():
    cur = {"n": 0, "max": 0}
    lock = threading.Lock()

    def fn(x):
        with lock:
            cur["n"] += 1
            cur["max"] = max(cur["max"], cur["n"])
        time.sleep(0.02)
        with lock:
            cur["n"] -= 1
        return x

    fan_out(list(range(6)), fn, max_concurrency=2)
    assert cur["max"] <= 2


def test_retry_succeeds_after_transient_failures():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("transient")
        return "ok"

    assert retry(fn, attempts=3, backoff=0.0) == "ok"
    assert calls["n"] == 3


def test_retry_exhausts_and_raises():
    def fn():
        raise ValueError("always")

    with pytest.raises(ValueError):
        retry(fn, attempts=2, backoff=0.0)


def test_memoize_calls_once_per_key():
    calls = {"n": 0}

    @memoize(key=lambda x: x)
    def f(x):
        calls["n"] += 1
        return x * 10

    assert f(5) == 50
    assert f(5) == 50
    assert calls["n"] == 1


def test_pipeline_threads_value_through_stages():
    assert pipeline(3, lambda x: x + 1, lambda x: x * 2) == 8
