"""Per-persona synthetic identity for autonomous sign-up / login.

When an app gates a persona's goal behind registration or login that needs no
real-name or external verification, the persona uses this identity to register
itself in character. The identity is:

- **deterministic** — same persona always gets the same credentials (reproducible
  runs, and the persona can log back in on a later step),
- **clearly synthetic** — the email uses the RFC-reserved `example.com` domain,
  which never receives mail, so nothing real is created on a mail provider,
- **persona-consistent** — the display name comes from the persona.

It is NOT for apps requiring real identity (email/SMS/ID verification) — those
are blockers the persona reports rather than fakes.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from synthpanel.persona.models import Persona

_SYNTH_DOMAIN = "example.com"  # RFC 2606 reserved — never delivers mail


@dataclass(frozen=True)
class Identity:
    full_name: str
    email: str
    username: str
    password: str

    def as_prompt_block(self) -> str:
        return (
            f"  name: {self.full_name}\n"
            f"  email: {self.email}\n"
            f"  username: {self.username}\n"
            f"  password: {self.password}"
        )


def _ascii_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "", name.lower())
    return slug or "synthuser"


def synthetic_identity(persona: Persona) -> Identity:
    """Derive a deterministic, clearly-synthetic identity for a persona."""
    base = (persona.name or "Test User").strip()
    seed = hashlib.sha256(base.encode("utf-8")).hexdigest()
    slug = _ascii_slug(base)
    return Identity(
        full_name=base,
        email=f"{slug}.{seed[:6]}@{_SYNTH_DOMAIN}",
        username=f"{slug}_{seed[:4]}",
        # Strong + deterministic: upper, lower, digits, symbol, length >= 12.
        password=f"Synth-{seed[6:16]}!",
    )
