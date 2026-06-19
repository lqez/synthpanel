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

Your job is to explore the site AND evaluate the experience. Interact with the \
site based on your NAVIGATION STYLE and BEHAVIORAL CONTEXT — both are provided \
each turn. Many sites (personal homepages, portfolios, blogs, landing pages) \
have no form to submit or transaction to complete — for those, reading, judging \
the visual design, navigation, accessibility, and whether the content serves its \
purpose IS the task.

As you browse, emit `note` actions capturing concrete reactions: what works, \
what's confusing, design impressions, accessibility issues, and whether the \
content is sufficient — especially anything called out in TEST FOCUS.

Do NOT give up just because there is no obvious task to finish. Only `give_up` \
if the site is genuinely broken or unreachable. Use `done` when your NAVIGATION \
STYLE's stopping condition is met.

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


def _navigation_style_block(persona) -> str:  # noqa: ANN001 - Persona, avoid import cycle
    """Derive vivid, character-specific navigation instructions from persona factors.

    Uses psych.exploration as the primary signal, then modifies by patience,
    attention_to_detail, decision_speed, tech.savviness, age, and time_pressure.
    Returns a structured instruction block for inclusion in the user turn prompt.
    """
    psych = persona.psych
    tech = persona.tech
    demo = persona.demographics
    intent = persona.intent

    # Factor values — strings after use_enum_values=True, or None
    style = psych.exploration        # "skimmer" / "methodical" / "goal_driven"
    patience = psych.patience        # "low" / "medium" / "high"
    attention = psych.attention_to_detail
    speed = psych.decision_speed     # "impulsive" / "deliberate"
    reads = psych.reads_instructions
    frustration = psych.frustration_tolerance
    savvy = tech.savviness or 3
    age = demo.age_band or ""
    time_press = intent.time_pressure  # "rushed" / "normal" / "relaxed"

    young = any(b in age for b in ("18-24", "25-34", "13-17"))
    senior = any(b in age for b in ("55-64", "65-74", "75+"))
    rushed = time_press == "rushed"
    relaxed = time_press == "relaxed"
    patient = patience == "high"
    impatient = patience == "low"
    impulsive = speed == "impulsive"
    deliberate = speed == "deliberate"
    reads_a_lot = reads == "high"
    skips_text = reads == "low"
    detail_focused = attention == "high"
    low_frustration = frustration == "low"
    high_frustration = frustration == "high"
    power_user = savvy >= 4
    novice = savvy <= 2

    # ── Breadth score → pages-to-visit range ────────────────────────────────
    bscore = 5
    if style == "skimmer":       bscore += 3
    elif style == "methodical":  bscore += 1
    elif style == "goal_driven": bscore -= 3
    if patient or relaxed:       bscore += 2
    if impatient or rushed:      bscore -= 2
    if power_user:               bscore += 1
    if young:                    bscore += 2
    if senior:                   bscore -= 1
    bscore = max(2, min(11, bscore))
    pages_lo, pages_hi = max(2, bscore - 2), bscore + 3

    # ── Reading depth score → how much text is consumed per page ────────────
    dscore = 5
    if style == "methodical":              dscore += 3
    elif style == "skimmer":               dscore -= 2
    if reads_a_lot or detail_focused:      dscore += 2
    if skips_text:                         dscore -= 2
    if deliberate:                         dscore += 1
    if impulsive or rushed:                dscore -= 2
    if senior:                             dscore += 2
    if young:                              dscore -= 1
    if novice:                             dscore += 1   # novices read cautiously
    dscore = max(1, min(10, dscore))

    if dscore >= 8:
        reading = "every paragraph, heading, label, tooltip, and footnote — you miss nothing"
    elif dscore >= 6:
        reading = "full paragraphs in relevant sections, headlines everywhere else"
    elif dscore >= 4:
        reading = "headings and the first sentence or two per section"
    else:
        reading = "mostly headings and prominent visuals — body text gets skipped"

    # ── Link curiosity score → which links get followed ─────────────────────
    cscore = 5
    if style == "skimmer":       cscore += 3
    elif style == "goal_driven": cscore -= 3
    if young:                    cscore += 2
    if power_user:               cscore += 1
    if rushed or impatient:      cscore -= 2
    if deliberate:               cscore -= 1
    if senior or novice:         cscore -= 1
    cscore = max(1, min(10, cscore))

    if cscore >= 8:
        links = "follow anything that looks interesting or surprising — tangents are welcome"
    elif cscore >= 6:
        links = "follow most nav links and things that catch your eye; skip only clearly off-topic content"
    elif cscore >= 4:
        links = "follow links that seem directly relevant; skip 'About', 'Blog', marketing sections"
    else:
        links = "follow only the most relevant link or two — you're not here to browse"

    # ── Primary character line ───────────────────────────────────────────────
    if style == "skimmer":
        if young and (not rushed):
            char = (
                "You browse like you're scrolling a social feed — fast, curious, "
                "clicking whatever catches your eye. You bounce between sections without "
                "following a strict order, driven by visual interest more than logic."
            )
        elif rushed or impatient:
            char = (
                "You move at high speed: scroll, scan, click, move on. "
                "You give each page a few seconds of attention before deciding "
                "whether it's worth stopping."
            )
        else:
            char = (
                "You skim rather than read, following visual cues and headlines. "
                "If something looks interesting you click it; if not, you scroll past."
            )
        pattern = "breadth-first — visit many pages quickly, in whatever order feels natural"

    elif style == "methodical":
        if senior or reads_a_lot:
            char = (
                "You're careful and systematic. Before clicking anything, you read the "
                "entire visible section. You work top-to-bottom, left-to-right, and "
                "don't skip sections."
            )
        elif rushed:
            char = (
                "You're naturally methodical but under time pressure, so you're moving "
                "faster than you'd like. You skim in a structured order — top to bottom — "
                "rather than jumping around."
            )
        else:
            char = (
                "You explore in a deliberate order: read the page, understand each section's "
                "purpose, then decide where to click next. You don't jump around."
            )
        pattern = "depth-first — fewer pages but each one read thoroughly before moving on"

    elif style == "goal_driven":
        if power_user:
            char = (
                "You move efficiently and purposefully. You scan for the relevant feature, "
                "ignore decorative content, and act decisively."
            )
        elif novice:
            char = (
                "You know what you need but aren't sure where to find it. "
                "You follow the most obvious path and may backtrack if you get lost."
            )
        elif rushed or impatient:
            char = (
                "You're focused and impatient. Get in, do the thing, get out. "
                "Anything irrelevant is noise."
            )
        else:
            char = (
                "You're purpose-driven: scan for what you need, read just enough to act, "
                "don't explore for its own sake."
            )
        pattern = "goal-driven — focused path, minimal wandering"

    else:
        # No exploration style set — derive from other signals
        if young and (relaxed or patient):
            char = (
                "You browse freely with no fixed agenda, following whatever seems "
                "interesting or relevant."
            )
            pattern = "loose breadth-first — follow curiosity"
        elif senior or novice:
            char = (
                "You explore carefully, sticking to the main navigation and reading "
                "sections before clicking."
            )
            pattern = "cautious depth-first — don't stray too far"
        else:
            char = (
                "You explore at a moderate pace, following the most relevant links "
                "and reading enough to form a clear opinion."
            )
            pattern = "balanced — moderate breadth and depth"

    # ── Stopping condition ───────────────────────────────────────────────────
    if style == "goal_driven":
        stop = (
            "once you've accomplished your primary purpose or concluded the site "
            "can't help you — don't linger"
        )
    elif style == "methodical":
        stop = (
            "only after visiting all main sections and forming a complete picture. "
            "If there are clearly unvisited nav links, keep going"
        )
    else:
        if impatient or rushed:
            stop = "when your gut feeling is solid — don't linger once you've formed an impression"
        elif patient or relaxed:
            stop = (
                "only after a thorough exploration — don't wrap up while interesting "
                "sections remain unvisited"
            )
        else:
            stop = "once you've seen the main pages and formed a well-rounded opinion"

    # ── Frustration / persistence note ──────────────────────────────────────
    if low_frustration or (impatient and rushed):
        friction = (
            "Frustration threshold is LOW — confusion, slow pages, or unclear labels "
            "get noted immediately. If friction piles up, bail and explain why."
        )
    elif high_frustration or (patient and deliberate):
        friction = (
            "You're patient and persistent — try several approaches before giving up "
            "on a confusing section. Note problems but push through them."
        )
    else:
        friction = (
            "If you hit a dead end, back up and try another path before giving up."
        )

    return (
        f"NAVIGATION STYLE:\n"
        f"{char}\n\n"
        f"  Pattern    : {pattern}\n"
        f"  Pages      : visit {pages_lo}–{pages_hi} distinct pages/sections before concluding\n"
        f"  Reading    : {reading}\n"
        f"  Links      : {links}\n"
        f"  Stop when  : {stop}\n"
        f"  Friction   : {friction}"
    )


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
    nav_style = _navigation_style_block(turn.persona)
    return (
        f"PERSONA:\n{render_persona(turn.persona)}\n\n"
        f"{personality_block}"
        f"BEHAVIORAL CONTEXT (informs how this persona interacts, not a mandatory task):\n"
        f"{turn.persona.intent.goal}\n\n"
        f"{nav_style}\n\n"
        f"{focus_block}"
        f"{language_line}\n\n"
        f"SIGN-UP / LOGIN:\n{_SIGNUP_GUIDANCE}\n\n"
        f"SYNTHETIC IDENTITY:\n{identity.as_prompt_block()}\n\n"
        f"STEP: {turn.step_idx}\n\n"
        f"WHAT YOU'VE DONE SO FAR:\n{history}\n\n"
        f"CURRENT PAGE:\n{turn.observation.digest()}"
    )
