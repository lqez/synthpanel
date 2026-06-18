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
from synthpanel.persona.tags import TAGS, tags_for


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


# ── Tag-based recommendation from the existing library ─────────────────────────
#
# Rather than have the LLM author a whole panel (slow), it only prioritizes tags
# for the focus (a tiny, fast call); personas are then selected from the library
# locally by how well they match those tags, weighted by priority.

# A balanced, edge-case-aware ordering used when there is no focus signal offline.
_DEFAULT_TAG_PRIORITY: list[str] = [
    "low-tech-literacy",
    "senior",
    "accessibility-needs",
    "mobile-user",
    "first-time-visitor",
    "impatient",
    "slow-network",
    "skeptical",
    "tech-savvy",
    "privacy-conscious",
]

# Focus keyword -> tag hints for the offline/heuristic path. The real LLM handles
# arbitrary (incl. Korean) focus text; this just keeps the offline fallback
# sensible for the most common testing focuses.
_FOCUS_HINTS: list[tuple[tuple[str, ...], list[str]]] = [
    (("접근성", "accessib", "a11y", "screen reader", "스크린", "보조기기"),
     ["accessibility-needs", "screen-reader", "low-vision", "motor-impairment"]),
    (("고령", "노인", "시니어", "senior", "elderly", "어르신"),
     ["senior", "low-tech-literacy"]),
    (("초보", "입문", "처음", "beginner", "novice", "신규"),
     ["low-tech-literacy", "first-time-visitor"]),
    (("모바일", "mobile", "휴대"),
     ["mobile-user"]),
    (("데스크", "desktop", "pc"),
     ["desktop-user"]),
    (("결제", "구매", "체크아웃", "checkout", "payment", "purchase", "가격"),
     ["price-sensitive", "cautious", "impatient"]),
    (("회원가입", "가입", "signup", "sign up", "register", "온보딩", "onboarding"),
     ["first-time-visitor", "privacy-conscious"]),
    (("보안", "개인정보", "privacy", "security", "권한", "permission"),
     ["privacy-conscious", "skeptical", "cautious"]),
    (("속도", "느린", "네트워크", "network", "slow", "로딩"),
     ["slow-network", "impatient"]),
    (("검색", "search", "탐색"),
     ["skimmer", "goal-driven"]),
]


def _heuristic_tags(focus: str) -> list[str]:
    """Rank tags for a focus without an LLM: keyword hints + token overlap."""
    f = (focus or "").lower()
    out: list[str] = []

    def add(tag: str) -> None:
        if tag not in out:
            out.append(tag)

    for needles, tags in _FOCUS_HINTS:
        if any(nd in f for nd in needles):
            for tag in tags:
                add(tag)

    # Generic English token overlap with tag keys/descriptions.
    if f:
        import re

        for key, desc in TAGS:
            words = [w for w in re.findall(r"[a-z]+", f"{key} {desc}") if len(w) > 3]
            if any(w in f for w in words):
                add(key)

    return out or list(_DEFAULT_TAG_PRIORITY)


async def prioritize_tags(focus: str, provider_key: str, config: dict) -> list[str]:
    """Ask the LLM to rank tags for the focus; fall back to a heuristic."""
    fns = {
        "anthropic": "prioritize_with_anthropic",
        "openai": "prioritize_with_openai",
        "ollama": "prioritize_with_ollama",
    }
    fn_name = fns.get(provider_key)
    if fn_name:
        try:
            import importlib
            mod = importlib.import_module("synthpanel.persona.llm_recommender")
            tags = await getattr(mod, fn_name)(focus, config)
            if tags:
                return tags
        except Exception:  # noqa: BLE001 - never hard-fail recommendation
            pass
    return _heuristic_tags(focus)


def select_personas_by_tags(
    library: list[Persona], priority_tags: list[str], n: int
) -> list[Persona]:
    """Pick `n` library personas ranked by weighted prioritized-tag match.

    Earlier tags weigh more. Personas with no matched tag still fill any
    remaining slots in library order, so a full panel is returned when possible.
    """
    n = max(1, n)
    weights = {tag: len(priority_tags) - i for i, tag in enumerate(priority_tags)}
    scored: list[tuple[int, int, Persona]] = []
    for idx, persona in enumerate(library):
        ptags = tags_for(persona)
        score = sum(weight for tag, weight in weights.items() if tag in ptags)
        scored.append((score, idx, persona))
    # Highest score first; original order breaks ties for stable, sensible output.
    scored.sort(key=lambda triple: (-triple[0], triple[1]))
    return [persona for _, _, persona in scored[:n]]


async def recommend_from_library(
    *,
    focus: str,
    n: int,
    library: list[Persona],
    provider_key: str,
    config: dict,
) -> list[Persona]:
    """Recommend `n` personas from the existing library for a testing focus.

    The LLM only prioritizes tags (fast); selection is local. With an empty
    library we synthesize a balanced offline panel so the flow still works.
    """
    if not library:
        return _ensure_personality(heuristic_panel(AppContext(url="", focus=focus), n))
    tags = await prioritize_tags(focus, provider_key, config)
    return select_personas_by_tags(library, tags, n)


def _ensure_personality(personas: list[Persona]) -> list[Persona]:
    """Give each persona a stable randomized personality if it lacks one."""
    from synthpanel.persona.personality import random_personality

    for persona in personas:
        if not persona.personality:
            persona.personality = random_personality(persona, seed=persona.name)
    return personas
