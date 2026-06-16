import re

from synthpanel.persona.identity import synthetic_identity
from synthpanel.persona.models import Intent, Persona


def _persona(name):
    return Persona(name=name, intent=Intent(goal="g"))


def test_deterministic():
    a = synthetic_identity(_persona("Alex Carter"))
    b = synthetic_identity(_persona("Alex Carter"))
    assert a == b


def test_distinct_per_persona():
    a = synthetic_identity(_persona("Alex Carter"))
    b = synthetic_identity(_persona("Priya Nair"))
    assert a.email != b.email
    assert a.password != b.password


def test_email_is_ascii_and_reserved_domain():
    ident = synthetic_identity(_persona("Alex Carter"))
    assert ident.email.endswith("@example.com")
    # Local part must be ASCII (valid email), even for the reserved domain.
    ident.email.encode("ascii")
    assert re.fullmatch(r"[a-z0-9.]+@example\.com", ident.email)


def test_non_ascii_name_still_valid_email():
    ident = synthetic_identity(_persona("김순자"))
    # Korean name -> ascii fallback slug, name field keeps the original.
    ident.email.encode("ascii")
    assert ident.full_name == "김순자"
    assert ident.email.endswith("@example.com")


def test_password_complexity():
    pw = synthetic_identity(_persona("Alex Carter")).password
    assert len(pw) >= 12
    assert any(c.isupper() for c in pw)
    assert any(c.islower() for c in pw)
    assert any(c.isdigit() for c in pw)
    assert any(not c.isalnum() for c in pw)
