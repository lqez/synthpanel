"""Supported report languages.

The agent writes its notes, bug reports, and UX feedback in the configured
language. Codes are stored; the English name is what the prompt instructs with.
"""

from __future__ import annotations

# code -> English name (used in the prompt) + native label (used in the UI)
LANGUAGES: dict[str, tuple[str, str]] = {
    "en": ("English", "English"),
    "ko": ("Korean", "한국어"),
    "ja": ("Japanese", "日本語"),
    "zh": ("Chinese", "中文"),
    "es": ("Spanish", "Español"),
    "fr": ("French", "Français"),
    "de": ("German", "Deutsch"),
    "pt": ("Portuguese", "Português"),
}

DEFAULT_LANGUAGE = "en"


def normalize(code: str | None) -> str:
    return code if code in LANGUAGES else DEFAULT_LANGUAGE


def english_name(code: str | None) -> str:
    return LANGUAGES[normalize(code)][0]


def native_label(code: str | None) -> str:
    return LANGUAGES[normalize(code)][1]
