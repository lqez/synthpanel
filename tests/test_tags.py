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
from synthpanel.persona.tags import TAG_KEYS, tags_for


def test_tags_for_derives_expected_tags_from_attributes():
    persona = Persona(
        name="할머니",
        demographics=Demographics(age_band="65-74", gender=Gender.FEMALE, city_tier=CityTier.METRO),
        tech=TechProfile(
            savviness=2, device=Device.MOBILE, network=Network.THROTTLED_3G, a11y=[A11yNeed.SCREEN_READER]
        ),
        psych=Psychographics(patience=Level.LOW, exploration=ExplorationStyle.METHODICAL),
        attitudes=Attitudes(privacy_sensitivity=Level.HIGH),
        intent=Intent(goal="g"),
    )
    derived = tags_for(persona)
    assert {
        "low-tech-literacy",
        "mobile-user",
        "slow-network",
        "accessibility-needs",
        "screen-reader",
        "senior",
        "urban",
        "methodical",
        "impatient",
        "privacy-conscious",
        "cautious",
        "female",
    } <= derived


def test_tags_for_power_user_profile():
    persona = Persona(
        name="고수",
        tech=TechProfile(savviness=5, device=Device.DESKTOP, network=Network.FAST),
        intent=Intent(goal="g"),
    )
    derived = tags_for(persona)
    assert {"tech-savvy", "power-user", "desktop-user", "fast-network"} <= derived


def test_tags_for_only_yields_known_vocabulary():
    persona = Persona(
        name="x",
        demographics=Demographics(age_band="18-24"),
        tech=TechProfile(savviness=3),
        intent=Intent(goal="g"),
    )
    assert tags_for(persona) <= set(TAG_KEYS)


def test_tags_for_sparse_persona_is_empty():
    # A persona with no distinguishing factors derives no tags (rather than guesses).
    assert tags_for(Persona(name="blank", intent=Intent(goal="g"))) == set()
