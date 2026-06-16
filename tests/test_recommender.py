from synthpanel.persona.models import Persona
from synthpanel.persona.recommender import AppContext, heuristic_panel, recommend_personas


def test_heuristic_panel_size_and_uniqueness():
    panel = heuristic_panel(AppContext(url="https://app.test", focus="signup"), 4)
    assert len(panel) == 4
    assert all(isinstance(p, Persona) for p in panel)
    # Names are unique even when templates wrap around.
    big = heuristic_panel(AppContext(url="x"), 9)
    assert len(big) == 9
    assert len({p.name for p in big}) == 9


def test_focus_threaded_into_goals():
    panel = heuristic_panel(AppContext(url="x", focus="complete checkout"), 3)
    assert all("complete checkout" in p.intent.goal for p in panel)


def test_panel_covers_edge_cases():
    panel = heuristic_panel(AppContext(url="x"), 6)
    a11y = [p for p in panel if p.tech.a11y]
    elderly = [p for p in panel if p.demographics.age_band and "65" in p.demographics.age_band]
    assert a11y, "expected at least one accessibility persona"
    assert elderly, "expected at least one elderly persona"


async def test_recommend_falls_back_to_heuristic_for_fake_provider():
    panel = await recommend_personas(
        url="https://app.test", focus="", n=3, provider_key="fake", config={}
    )
    assert len(panel) == 3


async def test_recommend_falls_back_when_anthropic_raises(monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("no network")

    monkeypatch.setattr(
        "synthpanel.persona.llm_recommender.recommend_with_anthropic", boom
    )
    # Should swallow the error and return the heuristic panel, never hard-fail.
    panel = await recommend_personas(
        url="u", focus="checkout", n=2, provider_key="anthropic", config={"api_key": "x"}
    )
    assert len(panel) == 2
    assert all("checkout" in p.intent.goal for p in panel)
