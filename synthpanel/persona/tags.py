"""Fixed tag taxonomy for personas, plus attribute-derived tagging.

A small, stable vocabulary (~45 tags) describing persona traits. Tags are
*derived* from a persona's structured factors, so every persona — seeded,
hand-built, or LLM-generated — gets a consistent set with no extra storage.

Recommendation builds on this: instead of asking an LLM to author a whole panel
(slow, even on a flagship model), we ask it only to *prioritize tags* for a
testing focus — a handful of short strings — and then select matching library
personas locally. See recommender.recommend_from_library.
"""

from __future__ import annotations

import re

from synthpanel.persona.models import Persona

# (key, human description). Order is stable; the keys are the contract shown to
# the LLM, so keep them human-readable and append-only where possible.
TAGS: list[tuple[str, str]] = [
    # Tech literacy
    ("low-tech-literacy", "struggles with technology; needs simple, guided flows"),
    ("tech-savvy", "comfortable and quick with software"),
    ("power-user", "expert who expects speed, shortcuts, and dense UIs"),
    # Device
    ("mobile-user", "primarily on a phone"),
    ("desktop-user", "primarily on a desktop or laptop"),
    ("tablet-user", "primarily on a tablet"),
    # Network
    ("slow-network", "on a slow or throttled connection"),
    ("fast-network", "on a fast, reliable connection"),
    # Accessibility
    ("accessibility-needs", "has some accessibility requirement"),
    ("screen-reader", "navigates with a screen reader"),
    ("low-vision", "low vision; needs large text or high contrast"),
    ("color-blind", "color vision deficiency"),
    ("motor-impairment", "limited motor control; relies on keyboard/large targets"),
    # Age
    ("teen", "teenager"),
    ("young-adult", "roughly 18-29 years old"),
    ("middle-aged", "roughly 30-54 years old"),
    ("senior", "55+; often less digitally native"),
    # Location
    ("urban", "lives in a major metro area"),
    ("small-town", "lives in a smaller city or town"),
    ("rural", "lives in a rural area"),
    # Exploration style
    ("goal-driven", "heads straight for the task at hand"),
    ("methodical", "reads carefully and proceeds step by step"),
    ("skimmer", "skims and clicks the first plausible thing"),
    # Patience and decisions
    ("impatient", "low patience; bails quickly"),
    ("patient", "willing to persevere through friction"),
    ("impulsive", "decides fast, on a hunch"),
    ("deliberate", "weighs options before acting"),
    ("low-frustration-tolerance", "frustrates and gives up easily"),
    # Attention and trust
    ("detail-oriented", "notices small details and inconsistencies"),
    ("skeptical", "distrustful; questions claims and prompts"),
    ("reads-instructions", "actually reads labels and help text"),
    ("cautious", "careful and risk-averse; double-checks"),
    # Attitudes
    ("privacy-conscious", "sensitive about data, tracking, and permissions"),
    ("price-sensitive", "very focused on cost and deals"),
    ("brand-loyal", "sticks with brands they already trust"),
    ("brand-agnostic", "no brand allegiance; switches easily"),
    ("early-adopter", "eagerly tries new products and features"),
    ("laggard", "slow to adopt; prefers the familiar"),
    # Intent and visit context
    ("first-time-visitor", "new to the app"),
    ("returning-user", "has used the app before"),
    ("from-ad", "arrived via an advertisement"),
    ("time-pressured", "in a hurry to finish"),
    # Gender
    ("female", "female"),
    ("male", "male"),
    ("nonbinary", "non-binary or undisclosed gender"),
]

TAG_KEYS: list[str] = [key for key, _ in TAGS]


def _age_low(age_band: str | None) -> int | None:
    """The lower bound of a free-text age band like '25-34' or '65+'."""
    if not age_band:
        return None
    m = re.search(r"\d+", age_band)
    return int(m.group()) if m else None


def tags_for(persona: Persona) -> set[str]:
    """Derive the tag set a persona matches from its structured factors.

    Sub-models use ``use_enum_values=True``, so enum fields read back as their
    plain string values (e.g. ``tech.device == 'mobile'``).
    """
    out: set[str] = set()
    tech, psych, att = persona.tech, persona.psych, persona.attitudes
    demo, intent = persona.demographics, persona.intent

    # Tech literacy
    sav = tech.savviness
    if sav is not None:
        if sav <= 2:
            out.add("low-tech-literacy")
        if sav >= 4:
            out.add("tech-savvy")
        if sav >= 5:
            out.add("power-user")

    # Device
    if tech.device == "mobile":
        out.add("mobile-user")
    elif tech.device == "desktop":
        out.add("desktop-user")
    elif tech.device == "tablet":
        out.add("tablet-user")

    # Network
    if tech.network in ("slow_4g", "3g_throttled"):
        out.add("slow-network")
    elif tech.network == "fast":
        out.add("fast-network")

    # Accessibility (a11y is a list of enum values)
    a11y = set(tech.a11y or [])
    if a11y:
        out.add("accessibility-needs")
        if "screen_reader" in a11y:
            out.add("screen-reader")
        if a11y & {"low_vision", "large_text"}:
            out.add("low-vision")
        if "color_blind" in a11y:
            out.add("color-blind")
        if "motor" in a11y:
            out.add("motor-impairment")

    # Age band
    age = _age_low(demo.age_band)
    if age is not None:
        if age < 20:
            out.add("teen")
        elif age < 30:
            out.add("young-adult")
        elif age < 55:
            out.add("middle-aged")
        else:
            out.add("senior")

    # Location
    if demo.city_tier == "metro":
        out.add("urban")
    elif demo.city_tier == "small_city":
        out.add("small-town")
    elif demo.city_tier == "rural":
        out.add("rural")

    # Exploration style
    if psych.exploration == "goal_driven":
        out.add("goal-driven")
    elif psych.exploration == "methodical":
        out.add("methodical")
    elif psych.exploration == "skimmer":
        out.add("skimmer")

    # Patience and decisions
    if psych.patience == "low":
        out.add("impatient")
    elif psych.patience == "high":
        out.add("patient")
    if psych.decision_speed == "impulsive":
        out.add("impulsive")
    elif psych.decision_speed == "deliberate":
        out.add("deliberate")
    if psych.frustration_tolerance == "low":
        out.add("low-frustration-tolerance")

    # Attention and trust
    if psych.attention_to_detail == "high":
        out.add("detail-oriented")
    if psych.skepticism == "high":
        out.add("skeptical")
        out.add("cautious")
    if psych.reads_instructions == "high":
        out.add("reads-instructions")

    # Attitudes
    if att.privacy_sensitivity == "high":
        out.add("privacy-conscious")
        out.add("cautious")
    if att.price_sensitivity == "high":
        out.add("price-sensitive")
    if att.brand_loyalty == "high":
        out.add("brand-loyal")
    elif att.brand_loyalty == "low":
        out.add("brand-agnostic")
    adoption = (att.tech_adoption or "").lower()
    if "early" in adoption:
        out.add("early-adopter")
    if "laggard" in adoption or "late" in adoption:
        out.add("laggard")

    # Intent and visit context
    if intent.context == "first_visit":
        out.add("first-time-visitor")
    elif intent.context == "returning":
        out.add("returning-user")
    elif intent.context == "from_ad":
        out.add("from-ad")
    if intent.time_pressure == "rushed":
        out.add("time-pressured")

    # Gender
    if demo.gender == "F":
        out.add("female")
    elif demo.gender == "M":
        out.add("male")
    elif demo.gender in ("nonbinary", "undisclosed"):
        out.add("nonbinary")

    return out
