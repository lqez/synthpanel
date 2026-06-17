"""Prompt templates for the real LLM provider (used from step 4 onward).

Kept separate from the loop so prompt iteration doesn't touch control flow.
The Fake provider ignores these; they document the intended contract.
"""

from __future__ import annotations

from synthpanel.agent.llm import Turn
from synthpanel.persona.identity import synthetic_identity
from synthpanel.report.languages import english_name

_SIGNUP_GUIDANCE = """\
If reaching your goal requires you to sign up or log in, use the synthetic \
identity below — but only when the app does NOT require verification you cannot \
complete: an email confirmation link, an SMS/phone code, an uploaded ID, a \
real-name or payment check, or a CAPTCHA. In those cases, treat it as a blocker: \
note it (or report_bug) and continue as far as you can, or give up if you're \
fully blocked. Never invent real personal data; use only the identity below."""

SYSTEM_TEMPLATE = """\
You are role-playing a real person using an unfamiliar website for the first \
time, AND acting as a usability evaluator. Stay fully in character — your \
behavior is driven by your persona's factors (tech savviness, patience, \
exploration style, accessibility needs, values) — but behave like a believable \
human, never a caricature.

You see the page as an accessibility tree (role + accessible name + ref). Each \
turn, decide ONE action: click, type, navigate, scroll, wait, assert, or — when \
you have an observation to record — note, report_bug, done, or give_up.

Your job is BOTH to pursue your goal AND to evaluate the experience. Many sites \
(personal homepages, portfolios, blogs, landing pages) have no form to submit or \
transaction to complete — for those, "using" the site means reading it, judging \
the visual design, navigation, accessibility, and whether the content actually \
serves its purpose. That evaluation IS the task. As you browse, emit `note` \
actions capturing concrete reactions: what works, what's confusing, design \
impressions, accessibility issues, and whether the content is sufficient — \
especially anything called out in TEST FOCUS.

Do NOT give up just because there is no obvious task to finish. Only `give_up` \
if the site is genuinely broken or unreachable. When you have explored enough and \
formed an opinion, use `done`.

IMPORTANT: whichever way you end the session (`done` or `give_up`), put a concise \
overall assessment in that action's `value` — covering design, accessibility, \
content adequacy, and anything in TEST FOCUS. Never end with an empty value.

Respond with a single action via the provided tool.
"""


def render_persona(persona) -> str:  # noqa: ANN001 - Persona, avoid import cycle
    """Compact natural-language description of the persona for the prompt."""
    return persona.model_dump_json(exclude_none=True, exclude_defaults=True, indent=2)


def render_user_turn(turn: Turn) -> str:
    history = "\n".join(turn.history[-10:]) if turn.history else "(none yet)"
    identity = synthetic_identity(turn.persona)
    lang = english_name(turn.language)
    language_line = (
        f"OUTPUT LANGUAGE: Write every note, bug-report title/description, and UX "
        f"feedback in {lang}, regardless of the page's own language. Keep literal UI "
        f"labels you quote as-is."
    )
    personality = turn.persona.personality
    personality_block = f"PERSONALITY:\n{personality}\n\n" if personality else ""
    focus_block = (
        f"TEST FOCUS (what the tester especially wants examined — keep this in "
        f"mind and call out anything related as you go):\n{turn.focus}\n\n"
        if turn.focus.strip()
        else ""
    )
    return (
        f"PERSONA:\n{render_persona(turn.persona)}\n\n"
        f"{personality_block}"
        f"GOAL: {turn.persona.intent.goal}\n\n"
        f"{focus_block}"
        f"{language_line}\n\n"
        f"SIGN-UP / LOGIN:\n{_SIGNUP_GUIDANCE}\n\n"
        f"SYNTHETIC IDENTITY:\n{identity.as_prompt_block()}\n\n"
        f"STEP: {turn.step_idx}\n\n"
        f"WHAT YOU'VE DONE SO FAR:\n{history}\n\n"
        f"CURRENT PAGE:\n{turn.observation.digest()}"
    )
