"""Recommend a balanced panel of personas for an app under test.

Given the target URL and a free-text focus, propose N personas spanning the
realistic audience plus deliberate edge cases (low tech literacy, elderly,
accessibility needs, slow networks). Works offline via a heuristic panel; with
the Anthropic provider it asks the model and falls back to the heuristic on any
error, so the flow never hard-fails.
"""

from __future__ import annotations

from dataclasses import dataclass

from synthpanel.persona.factors import (
    A11yNeed,
    CityTier,
    Device,
    ExplorationStyle,
    Gender,
    Level,
    Network,
)
from synthpanel.persona.models import (
    Attitudes,
    Demographics,
    Intent,
    Persona,
    Psychographics,
    TechProfile,
)


@dataclass(frozen=True)
class AppContext:
    url: str
    focus: str = ""


# Ordered archetype templates: realistic core first, edge cases after, so that
# small panels still cover the most likely users and large panels add breadth.
_TEMPLATES: list[dict] = [
    {
        "name": "Maya Chen",
        "archetype": "Goal-driven power user",
        "tech": TechProfile(savviness=5, device=Device.DESKTOP, network=Network.FAST),
        "psych": Psychographics(patience=Level.LOW, exploration=ExplorationStyle.GOAL_DRIVEN),
        "demographics": Demographics(age_band="25-34", gender=Gender.FEMALE, city_tier=CityTier.METRO),
    },
    {
        "name": "Tom Becker",
        "archetype": "Cautious first-time visitor",
        "tech": TechProfile(savviness=3, device=Device.DESKTOP, network=Network.FAST),
        "psych": Psychographics(patience=Level.MEDIUM, exploration=ExplorationStyle.METHODICAL, skepticism=Level.HIGH),
        "attitudes": Attitudes(privacy_sensitivity=Level.HIGH),
        "demographics": Demographics(age_band="35-44", gender=Gender.MALE),
    },
    {
        "name": "박순자",
        "archetype": "디지털 입문 고령 사용자",
        "tech": TechProfile(savviness=2, device=Device.MOBILE, network=Network.THROTTLED_3G, a11y=[A11yNeed.LARGE_TEXT]),
        "psych": Psychographics(patience=Level.LOW, exploration=ExplorationStyle.METHODICAL, reads_instructions=Level.HIGH),
        "demographics": Demographics(age_band="65-74", gender=Gender.FEMALE, city_tier=CityTier.METRO),
    },
    {
        "name": "Aisha Khan",
        "archetype": "Screen-reader user",
        "tech": TechProfile(savviness=4, device=Device.DESKTOP, a11y=[A11yNeed.SCREEN_READER]),
        "psych": Psychographics(patience=Level.MEDIUM, attention_to_detail=Level.HIGH),
        "demographics": Demographics(age_band="30-39", gender=Gender.FEMALE),
    },
    {
        "name": "Diego Ramos",
        "archetype": "Mobile user on a slow network",
        "tech": TechProfile(savviness=3, device=Device.MOBILE, network=Network.SLOW_4G),
        "psych": Psychographics(patience=Level.LOW, exploration=ExplorationStyle.SKIMMER),
        "demographics": Demographics(age_band="18-24", gender=Gender.MALE, city_tier=CityTier.SMALL_CITY),
    },
    {
        "name": "Helen Park",
        "archetype": "Price-sensitive comparison shopper",
        "tech": TechProfile(savviness=3, device=Device.MOBILE),
        "psych": Psychographics(patience=Level.MEDIUM, attention_to_detail=Level.HIGH),
        "attitudes": Attitudes(price_sensitivity=Level.HIGH, brand_loyalty=Level.LOW),
        "demographics": Demographics(age_band="40-49", gender=Gender.FEMALE),
    },
]


def _goal_for(focus: str, archetype: str) -> str:
    if focus:
        return f"{focus} (as a {archetype})"
    return f"Explore the app and reach its main feature (as a {archetype})"


def heuristic_panel(context: AppContext, n: int) -> list[Persona]:
    """A deterministic, offline balanced panel of `n` personas."""
    n = max(1, n)
    out: list[Persona] = []
    for i in range(n):
        t = _TEMPLATES[i % len(_TEMPLATES)]
        suffix = "" if i < len(_TEMPLATES) else f" #{i // len(_TEMPLATES) + 1}"
        out.append(
            Persona(
                name=t["name"] + suffix,
                archetype=t["archetype"],
                demographics=t.get("demographics", Demographics()),
                tech=t.get("tech", TechProfile()),
                psych=t.get("psych", Psychographics()),
                attitudes=t.get("attitudes", Attitudes()),
                intent=Intent(goal=_goal_for(context.focus, t["archetype"])),
            )
        )
    return out


async def recommend_personas(
    *,
    url: str,
    focus: str,
    n: int,
    provider_key: str,
    config: dict,
) -> list[Persona]:
    """Recommend `n` personas, using the LLM when available, else heuristic."""
    context = AppContext(url=url, focus=focus)
    personas: list[Persona] = []
    _llm: dict = {
        "anthropic": "recommend_with_anthropic",
        "openai": "recommend_with_openai",
        "ollama": "recommend_with_ollama",
    }
    fn_name = _llm.get(provider_key)
    if fn_name:
        try:
            import importlib
            mod = importlib.import_module("synthpanel.persona.llm_recommender")
            personas = await getattr(mod, fn_name)(context, n, config)
        except Exception:  # noqa: BLE001 - never hard-fail recommendation
            personas = []
    if not personas:
        personas = heuristic_panel(context, n)
    return _ensure_personality(personas)


def _ensure_personality(personas: list[Persona]) -> list[Persona]:
    """Give each persona a stable randomized personality if it lacks one."""
    from synthpanel.persona.personality import random_personality

    for persona in personas:
        if not persona.personality:
            persona.personality = random_personality(persona, seed=persona.name)
    return personas
