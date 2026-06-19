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

Your job is to explore the site thoroughly AND evaluate the experience. Interact \
with the site based on your persona's behavioral context — use it to inform HOW \
you navigate and what you prioritize, not as a rigid task you must complete. Many \
sites (personal homepages, portfolios, blogs, landing pages) have no form to \
submit or transaction to complete — for those, reading, judging the visual \
design, navigation, accessibility, and whether the content serves its purpose IS \
the task.

EXPLORE BROADLY: Before concluding, follow navigation links, explore different \
sections, click on interesting items, and try multiple pages. Do not stop after \
visiting just one or two pages. If there are unvisited sections in the navigation \
or links you haven't followed, keep exploring. Aim to visit as many distinct \
pages and features as you reasonably can given your persona's patience level.

As you browse, emit `note` actions capturing concrete reactions: what works, \
what's confusing, design impressions, accessibility issues, and whether the \
content is sufficient — especially anything called out in TEST FOCUS.

Do NOT give up just because there is no obvious task to finish. Only `give_up` \
if the site is genuinely broken or unreachable. Only use `done` after you have \
explored a substantial portion of the site and formed a well-rounded opinion.

IMPORTANT: whichever way you end the session (`done` or `give_up`), put a \
structured Markdown overall assessment in that action's `value` using these sections:

## 총평
(2–3 sentence overall impression of the site)

## 세부 의견
- (one bullet per concrete observation — design, usability, accessibility, content)

## 페이지별 의견
### [페이지 이름 또는 URL]
(brief per-page notes for each page or section you visited)

Never end with an empty value.

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
        f"BEHAVIORAL CONTEXT (informs how this persona interacts, not a mandatory task):\n"
        f"{turn.persona.intent.goal}\n\n"
        f"{focus_block}"
        f"{language_line}\n\n"
        f"SIGN-UP / LOGIN:\n{_SIGNUP_GUIDANCE}\n\n"
        f"SYNTHETIC IDENTITY:\n{identity.as_prompt_block()}\n\n"
        f"STEP: {turn.step_idx}\n\n"
        f"WHAT YOU'VE DONE SO FAR:\n{history}\n\n"
        f"CURRENT PAGE:\n{turn.observation.digest()}"
    )
