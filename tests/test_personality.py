from synthpanel.persona.factors import Device, Level
from synthpanel.persona.models import Intent, Persona, Psychographics, TechProfile
from synthpanel.persona.personality import random_personality


def _persona(name="Alex", **kw):
    return Persona(name=name, intent=Intent(goal="g"), **kw)


def test_seeded_is_deterministic():
    p = _persona()
    assert random_personality(p, seed="x") == random_personality(p, seed="x")


def test_unseeded_varies():
    # Extremely unlikely to collide across many unseeded draws.
    p = _persona()
    draws = {random_personality(p) for _ in range(8)}
    assert len(draws) > 1


def test_distinct_seeds_differ():
    p = _persona()
    assert random_personality(p, seed="a") != random_personality(p, seed="b")


def test_non_empty_and_descriptive():
    text = random_personality(_persona(), seed="x")
    assert text.startswith("Tends to ")
    assert len(text) > 40


def test_low_savviness_biases_toward_jargon_peeve():
    low = _persona(tech=TechProfile(savviness=1, device=Device.MOBILE))
    # With the bias, "jargon" should appear across most seeds.
    hits = sum("jargon" in random_personality(low, seed=i) for i in range(20))
    assert hits >= 12


def test_low_patience_biases_toward_abandon_quirk():
    impatient = _persona(psych=Psychographics(patience=Level.LOW))
    hits = sum("abandons" in random_personality(impatient, seed=i) for i in range(20))
    assert hits >= 10
