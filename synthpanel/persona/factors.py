"""Enumerations and controlled vocabularies for the 5-dimension persona model.

These keep auto-generated and hand-built personas consistent and validatable.
Each enum maps to a factor described in PLAN.md section 4.
"""

from __future__ import annotations

from enum import Enum


class Gender(str, Enum):
    FEMALE = "F"
    MALE = "M"
    NONBINARY = "nonbinary"
    UNDISCLOSED = "undisclosed"


class CityTier(str, Enum):
    METRO = "metro"          # 대도시
    SMALL_CITY = "small_city"  # 소도시
    RURAL = "rural"          # 농촌


class Education(str, Enum):
    NONE = "none"
    PRIMARY = "primary"
    HIGHSCHOOL = "highschool"
    COLLEGE = "college"
    GRADUATE = "graduate"


class Device(str, Enum):
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"


class Network(str, Enum):
    FAST = "fast"
    SLOW_4G = "slow_4g"
    THROTTLED_3G = "3g_throttled"


class A11yNeed(str, Enum):
    SCREEN_READER = "screen_reader"
    LOW_VISION = "low_vision"
    LARGE_TEXT = "large_text"
    COLOR_BLIND = "color_blind"
    MOTOR = "motor"


class InputPref(str, Enum):
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    TOUCH = "touch"


class Level(str, Enum):
    """Generic low/medium/high scale reused across psychographic factors."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExplorationStyle(str, Enum):
    SKIMMER = "skimmer"        # 훑기형
    METHODICAL = "methodical"  # 꼼꼼형
    GOAL_DRIVEN = "goal_driven"  # 목표지향형


class DecisionSpeed(str, Enum):
    IMPULSIVE = "impulsive"
    DELIBERATE = "deliberate"


class VisitContext(str, Enum):
    FIRST_VISIT = "first_visit"
    RETURNING = "returning"
    FROM_AD = "from_ad"
    REFERRED = "referred"


class TimePressure(str, Enum):
    RELAXED = "relaxed"
    NORMAL = "normal"
    RUSHED = "rushed"


# Factors considered sensitive. Always selectable (per product decision), but
# callers may want to surface a confirmation or exclude them from defaults.
SENSITIVE_FACTORS: frozenset[str] = frozenset(
    {
        "attitudes.political_engagement",
        "attitudes.political_leaning",
        "demographics.income_bracket",
        "attitudes.religion",
    }
)
