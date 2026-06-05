import pytest

from core.pricing import PRICING, cost


def test_opus_cost_is_table_driven():
    # 1M input + 1M output at $15/$75 per MTok = $90.00
    assert cost("claude-opus-4-8", 1_000_000, 1_000_000) == pytest.approx(90.0)


def test_partial_million_scales_linearly():
    # 500k in @ $3/MTok + 250k out @ $15/MTok = 1.5 + 3.75
    assert cost("claude-sonnet-4-6", 500_000, 250_000) == pytest.approx(5.25)


def test_deepseek_is_cheapest_per_mtok():
    ds = cost("deepseek-chat", 1_000_000, 0)
    haiku = cost("claude-haiku-4-5-20251001", 1_000_000, 0)
    assert ds < haiku


def test_unknown_model_fails_loud():
    with pytest.raises(KeyError):
        cost("gpt-9-ultra", 100, 100)


def test_pricing_table_has_all_four_tiers():
    for m in ("deepseek-chat", "claude-haiku-4-5-20251001",
              "claude-sonnet-4-6", "claude-opus-4-8"):
        assert m in PRICING
