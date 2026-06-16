from synthpanel.persona.llm_recommender import _to_personas


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
