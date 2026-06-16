"""Prompt templates for the real LLM provider (used from step 4 onward).

Kept separate from the loop so prompt iteration doesn't touch control flow.
The Fake provider ignores these; they document the intended contract.
"""

from __future__ import annotations

from synthpanel.agent.llm import Turn
from synthpanel.persona.identity import synthetic_identity

_SIGNUP_GUIDANCE = """\
If reaching your goal requires you to sign up or log in, use the synthetic \
identity below — but only when the app does NOT require verification you cannot \
complete: an email confirmation link, an SMS/phone code, an uploaded ID, a \
real-name or payment check, or a CAPTCHA. In those cases, treat it as a blocker: \
note it (or report_bug) and continue as far as you can, or give up if you're \
fully blocked. Never invent real personal data; use only the identity below."""

SYSTEM_TEMPLATE = """\
You are role-playing a real person using an unfamiliar web app for the first \
time. Stay fully in character. Your behavior must be driven by your persona's \
factors — tech savviness, patience, exploration style, accessibility needs, and \
values — but behave like a believable human, never a caricature or stereotype.

You see the page as an accessibility tree (role + accessible name + ref). Decide \
ONE next action that moves you toward your goal, or report a bug / give up / \
declare done. Prefer the smallest realistic action. If something is broken, \
confusing, or slow, a low-patience persona reacts accordingly.

Respond with a single action via the provided tool.
"""


def render_persona(persona) -> str:  # noqa: ANN001 - Persona, avoid import cycle
    """Compact natural-language description of the persona for the prompt."""
    return persona.model_dump_json(exclude_none=True, exclude_defaults=True, indent=2)


def render_user_turn(turn: Turn) -> str:
    history = "\n".join(turn.history[-10:]) if turn.history else "(none yet)"
    identity = synthetic_identity(turn.persona)
    return (
        f"PERSONA:\n{render_persona(turn.persona)}\n\n"
        f"GOAL: {turn.persona.intent.goal}\n\n"
        f"SIGN-UP / LOGIN:\n{_SIGNUP_GUIDANCE}\n\n"
        f"SYNTHETIC IDENTITY:\n{identity.as_prompt_block()}\n\n"
        f"STEP: {turn.step_idx}\n\n"
        f"WHAT YOU'VE DONE SO FAR:\n{history}\n\n"
        f"CURRENT PAGE:\n{turn.observation.digest()}"
    )
