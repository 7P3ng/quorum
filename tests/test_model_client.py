import pytest

from core.model_client import (
    FakeClient, RecordedClient, prompt_key, estimate_tokens,
)


def _msgs(text):
    return [{"role": "user", "content": text}]


def test_prompt_key_is_deterministic_and_content_sensitive():
    k1 = prompt_key("m", "sys", _msgs("hello"))
    k2 = prompt_key("m", "sys", _msgs("hello"))
    k3 = prompt_key("m", "sys", _msgs("world"))
    assert k1 == k2
    assert k1 != k3
    assert len(k1) == 64  # sha256 hex


def test_fake_client_returns_text_and_priced_response():
    fc = FakeClient(lambda model, system, messages, max_tokens: "the answer is 42")
    r = fc.complete(model="claude-haiku-4-5-20251001", system="s",
                    messages=_msgs("q"), max_tokens=64)
    assert r.text == "the answer is 42"
    assert r.input_tokens > 0 and r.output_tokens > 0
    assert r.cost_usd > 0
    assert r.model == "claude-haiku-4-5-20251001"


def test_fake_client_responder_sees_inputs():
    seen = {}

    def responder(model, system, messages, max_tokens):
        seen.update(model=model, system=system, n=len(messages), mt=max_tokens)
        return "ok"

    FakeClient(responder).complete(model="deepseek-chat", system="S",
                                   messages=_msgs("hi"), max_tokens=7)
    assert seen == {"model": "deepseek-chat", "system": "S", "n": 1, "mt": 7}


def test_recorded_client_replays_by_key():
    key = prompt_key("deepseek-chat", "s", _msgs("q"))
    fixtures = {key: {"text": "recorded!", "input_tokens": 10, "output_tokens": 4}}
    rc = RecordedClient(fixtures)
    r = rc.complete(model="deepseek-chat", system="s", messages=_msgs("q"), max_tokens=99)
    assert r.text == "recorded!"
    assert r.input_tokens == 10 and r.output_tokens == 4
    assert r.cost_usd == pytest.approx((10 / 1e6) * 0.27 + (4 / 1e6) * 1.10)


def test_recorded_client_strict_missing_fails_loud():
    rc = RecordedClient({}, strict=True)
    with pytest.raises(KeyError):
        rc.complete(model="deepseek-chat", system="s", messages=_msgs("q"), max_tokens=1)


def test_estimate_tokens_monotonic():
    assert estimate_tokens("short") < estimate_tokens("a much longer string here ok")
