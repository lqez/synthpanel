from synthpanel.report.pricing import estimate_cost


def test_opus_cost():
    # 1M input @ $5 + 1M output @ $25 = $30.
    assert estimate_cost("claude-opus-4-8", 1_000_000, 1_000_000) == 30.0


def test_haiku_cheaper_than_opus():
    h = estimate_cost("claude-haiku-4-5", 500_000, 500_000)
    o = estimate_cost("claude-opus-4-8", 500_000, 500_000)
    assert 0 < h < o


def test_unknown_model_is_zero():
    assert estimate_cost("mystery-model", 1_000_000, 1_000_000) == 0.0
    assert estimate_cost(None, 10, 10) == 0.0
