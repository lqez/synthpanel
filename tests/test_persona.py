from synthpanel.persona.loader import load_personas, save_personas
from synthpanel.persona.models import Intent, Persona


def test_persona_minimal_defaults():
    p = Persona(name="Tester", intent=Intent(goal="sign up"))
    assert p.intent.goal == "sign up"
    # Sub-models default to empty, not None.
    assert p.demographics.age_band is None
    assert p.tech.a11y == []
    assert p.factor_weights == {}


def test_library_examples_load():
    from pathlib import Path

    path = Path(__file__).parent.parent / "synthpanel" / "persona" / "library" / "examples.yaml"
    personas = load_personas(path)
    assert len(personas) >= 3
    kim = next((p for p in personas if p.name == "김순자"), None)
    assert kim is not None
    assert kim.tech.savviness == 3


def test_roundtrip_yaml(tmp_path):
    p = Persona(
        name="Roundtrip",
        archetype="x",
        intent=Intent(goal="do a thing"),
        factor_weights={"psych.patience": 0.5},
    )
    out = tmp_path / "p.yaml"
    save_personas([p], out)
    loaded = load_personas(out)
    assert loaded[0].name == "Roundtrip"
    assert loaded[0].factor_weights == {"psych.patience": 0.5}
