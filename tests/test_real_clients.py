import pytest


def test_anthropic_fails_loud_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from core.anthropic_client import AnthropicClient
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        AnthropicClient()


def test_deepseek_fails_loud_without_key(monkeypatch):
    monkeypatch.delenv("OSSLLM_API_KEY", raising=False)
    from core.deepseek_client import DeepSeekClient
    with pytest.raises(RuntimeError, match="OSSLLM_API_KEY"):
        DeepSeekClient()
