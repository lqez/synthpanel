"""The Persona data model: a synthetic user described across 5 factor dimensions.

See PLAN.md section 4. Every sub-model field is optional so that a persona can be
sparsely specified (hand-built) or fully fleshed out (LLM-recommended). Factor
weights tune how strongly a given factor steers the agent's behavior.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from synthpanel.persona.factors import (
    A11yNeed,
    CityTier,
    DecisionSpeed,
    Device,
    Education,
    ExplorationStyle,
    Gender,
    InputPref,
    Level,
    Network,
    TimePressure,
    VisitContext,
)


class Demographics(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    age_band: str | None = None  # e.g. "25-34", "65-74"
    gender: Gender | None = None
    region: str | None = None  # free text: country / city
    city_tier: CityTier | None = None
    primary_language: str | None = None
    education: Education | None = None
    occupation: str | None = None
    income_bracket: str | None = None  # sensitive, optional
    household: str | None = None  # e.g. "single", "family_with_kids"


class TechProfile(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    savviness: int | None = Field(default=None, ge=1, le=5)
    device: Device | None = None
    os: str | None = None
    browser: str | None = None
    network: Network | None = None
    a11y: list[A11yNeed] = Field(default_factory=list)
    similar_app_experience: Level | None = None
    input_preference: InputPref | None = None


class Psychographics(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    patience: Level | None = None
    frustration_tolerance: Level | None = None
    exploration: ExplorationStyle | None = None
    attention_to_detail: Level | None = None
    decision_speed: DecisionSpeed | None = None
    reads_instructions: Level | None = None
    skepticism: Level | None = None
    baseline_mood: str | None = None


class Attitudes(BaseModel):
    """Values & attitudes. Includes sensitive factors — always selectable."""

    model_config = ConfigDict(use_enum_values=True)

    political_engagement: Level | None = None
    political_leaning: str | None = None
    privacy_sensitivity: Level | None = None
    price_sensitivity: Level | None = None
    tech_adoption: str | None = None  # "early_adopter" .. "laggard"
    brand_loyalty: Level | None = None
    social_environmental_values: str | None = None
    religion: str | None = None


class Intent(BaseModel):
    """The scenario: what this persona is trying to accomplish, and how/why."""

    model_config = ConfigDict(use_enum_values=True)

    goal: str = Field(..., description="Job-to-be-done in the app.")
    context: VisitContext | None = None
    time_pressure: TimePressure | None = None
    motivation: Level | None = None
    success_criteria: str | None = None


class Persona(BaseModel):
    """A complete synthetic user. The unit of a usability-test session."""

    model_config = ConfigDict(use_enum_values=True)

    name: str
    archetype: str | None = None
    demographics: Demographics = Field(default_factory=Demographics)
    tech: TechProfile = Field(default_factory=TechProfile)
    psych: Psychographics = Field(default_factory=Psychographics)
    attitudes: Attitudes = Field(default_factory=Attitudes)
    intent: Intent
    # Dotted factor path -> weight (0..1) of how strongly it steers behavior.
    factor_weights: dict[str, float] = Field(default_factory=dict)
