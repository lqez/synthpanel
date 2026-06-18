from synthpanel.persona.llm_recommender import _recommend_model, _to_personas


def test_recommend_model_defaults_to_fast_model_per_provider():
    # The lightweight recommend task should not borrow the heavy agent model,
    # even when one is configured for the browser agent.
    assert _recommend_model({"model": "claude-opus-4-8"}, "anthropic") == "claude-haiku-4-5-20251001"
    assert _recommend_model({"model": "gpt-4o"}, "openai") == "gpt-4o-mini"


def test_recommend_model_explicit_override_wins():
    cfg = {"model": "gpt-4o", "recommend_model": "gpt-4o"}
    assert _recommend_model(cfg, "openai") == "gpt-4o"


def test_recommend_model_ollama_reuses_pulled_model():
    # Ollama only has the models the user has pulled, so reuse the configured one.
    assert _recommend_model({"model": "qwen2.5"}, "ollama") == "qwen2.5"
    assert _recommend_model({}, "ollama") == "llama3.1"


def test_maps_valid_entries_and_defaults_goal():
    out = _to_personas(
        [
            {"name": "A", "goal": "complete signup", "tech": {"savviness": 4}},
            {"name": "B"},  # missing goal -> default goal, still valid
        ]
    )
    assert [p.name for p in out] == ["A", "B"]
    assert out[0].intent.goal == "complete signup"
    assert out[0].tech.savviness == 4
    assert out[1].intent.goal  # defaulted, non-empty


def test_skips_malformed_entries():
    out = _to_personas(
        [
            {"name": "Good", "goal": "x"},
            {"goal": "no name"},  # missing required name
            {"name": "BadTech", "goal": "y", "tech": "not-a-dict"},  # wrong type
        ]
    )
    assert [p.name for p in out] == ["Good"]
