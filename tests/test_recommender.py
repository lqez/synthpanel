from synthpanel.persona.factors import Device, Network
from synthpanel.persona.models import Demographics, Intent, Persona, TechProfile
from synthpanel.persona.recommender import (
    AppContext,
    _heuristic_tags,
    heuristic_panel,
    recommend_from_library,
    recommend_personas,
    select_personas_by_tags,
)


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


# ── Tag-based library recommendation ───────────────────────────────────────────


def _senior():
    return Persona(
        name="senior",
        demographics=Demographics(age_band="70"),
        tech=TechProfile(savviness=2, network=Network.THROTTLED_3G),
        intent=Intent(goal="g"),
    )


def _power_user():
    return Persona(
        name="power",
        tech=TechProfile(savviness=5, device=Device.DESKTOP, network=Network.FAST),
        intent=Intent(goal="g"),
    )


def test_select_personas_ranks_by_priority_tags():
    library = [_power_user(), _senior()]
    out = select_personas_by_tags(library, ["senior", "low-tech-literacy"], 2)
    assert out[0].name == "senior"  # matches the top-priority tags


def test_select_personas_returns_n_even_without_matches():
    library = [Persona(name=str(i), intent=Intent(goal="g")) for i in range(5)]
    out = select_personas_by_tags(library, ["senior"], 3)
    assert len(out) == 3


def test_heuristic_tags_maps_korean_focus_keywords():
    tags = _heuristic_tags("접근성 검토")
    assert tags[0] == "accessibility-needs"
    assert "screen-reader" in tags


def test_heuristic_tags_falls_back_to_default_priority():
    assert _heuristic_tags("") == _heuristic_tags("")  # deterministic
    assert _heuristic_tags("")  # non-empty edge-case-aware default


async def test_recommend_from_library_selects_with_fake_provider():
    library = [_senior(), _power_user(), Persona(name="z", intent=Intent(goal="g"))]
    out = await recommend_from_library(
        focus="고령 사용자 접근성", n=2, library=library, provider_key="fake", config={}
    )
    assert len(out) == 2
    assert out[0].name == "senior"  # heuristic prioritizes senior/accessibility tags


async def test_recommend_from_library_empty_library_synthesizes_panel():
    out = await recommend_from_library(
        focus="checkout", n=3, library=[], provider_key="fake", config={}
    )
    assert len(out) == 3
