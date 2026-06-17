"""Randomized free-text personality for a persona.

The 5-dimension factor model captures *what* a persona is; this adds the
distinctive *how* — quirks, voice, browsing habits, a small backstory — so two
personas with similar factors still behave like different people. The result is
a short paragraph fed to the agent prompt.

Generation is seedable: pass a seed (e.g. the persona name) for a stable
personality, or omit it to re-roll a fresh one.
"""

from __future__ import annotations

import random

from synthpanel.persona.factors import Level
from synthpanel.persona.models import Persona

_QUIRKS = [
    "double-checks every form field before submitting",
    "opens far too many tabs and loses track of them",
    "tries keyboard shortcuts before reaching for the mouse",
    "narrates each step under their breath",
    "screenshots anything that looks broken to complain about later",
    "abandons a flow the moment something feels off",
    "hunts for a search box instead of using the navigation",
    "reads the fine print that everyone else skips",
]
_VOICES = [
    "blunt and to the point",
    "polite but easily flustered",
    "dryly sarcastic when annoyed",
    "chatty and over-enthusiastic",
    "terse, mostly one-word reactions",
    "anxious and full of clarifying questions",
]
_HABITS = [
    "skims fast and clicks the first plausible button",
    "reads every label before committing to anything",
    "leans on browser back when unsure",
    "expects things to work like the last app they used",
    "zooms in to make sure they read small text correctly",
]
_BACKSTORIES = [
    "got burned by a phishing scam last year, so they distrust forms",
    "just migrated from a competitor and keeps comparing",
    "is setting this up on behalf of a less tech-savvy relative",
    "squeezed this in between back-to-back meetings",
    "is only poking around out of idle curiosity",
    "has tried and bounced off this kind of app twice before",
]
_PEEVES = [
    "bristles at surprise pop-ups",
    "resents being forced to create an account",
    "loses patience with slow pages almost instantly",
    "switches off the moment they hit unexplained jargon",
    "hates re-entering data they already provided",
]


def _pick(rng: random.Random, pool: list[str], bias: str | None = None) -> str:
    """Pick from a pool, lightly favoring an entry that contains `bias`."""
    if bias:
        matches = [x for x in pool if bias in x]
        if matches and rng.random() < 0.7:
            return rng.choice(matches)
    return rng.choice(pool)


def random_personality(persona: Persona, *, seed: object | None = None) -> str:
    rng = random.Random(seed)

    # Light nudges from factors so the text stays consistent with the persona.
    peeve_bias = "jargon" if persona.tech.savviness and persona.tech.savviness <= 2 else None
    quirk_bias = "abandons" if persona.psych.patience == Level.LOW else None

    quirk = _pick(rng, _QUIRKS, quirk_bias)
    voice = _pick(rng, _VOICES)
    habit = _pick(rng, _HABITS)
    backstory = _pick(rng, _BACKSTORIES)
    peeve = _pick(rng, _PEEVES, peeve_bias)

    return (
        f"Tends to {quirk}. Comes across as {voice}. When browsing, {habit}. "
        f"For context, {backstory}, and {peeve}."
    )
