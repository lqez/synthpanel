from synthpanel.agent.llm import Turn
from synthpanel.agent.prompts import render_user_turn
from synthpanel.persona.identity import synthetic_identity
from synthpanel.persona.models import Intent, Persona
from synthpanel.report.models import Observation


def test_user_turn_includes_identity_and_signup_guidance():
    persona = Persona(name="Alex Carter", intent=Intent(goal="reach the dashboard"))
    turn = Turn(
        persona=persona,
        observation=Observation(url="https://app.test", title="App"),
        history=[],
        step_idx=0,
    )
    text = render_user_turn(turn)

    ident = synthetic_identity(persona)
    assert ident.email in text
    # Guidance must spell out the verification blockers and the give-up path.
    assert "verification" in text
    assert "give up" in text or "give_up" in text
    assert "SYNTHETIC IDENTITY" in text
