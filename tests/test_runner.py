"""Runner orchestration glue, with the Playwright launch stubbed out."""

from __future__ import annotations

from synthpanel.report.models import BugReport, SessionResult, SessionStatus
from synthpanel.web import runner


async def test_wraps_launch_errors_and_uses_default_persona(monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("launch failed")

    monkeypatch.setattr(runner, "_run_with_playwright", boom)
    result = await runner.execute_run(
        {"url": "https://app.test", "personas": [], "focus": "signup"},
        {"provider": "fake", "config": {}},
    )
    assert "launch failed" in result["error"]
    # An empty panel falls back to a single default persona.
    assert result["summary"]["personas"] == 1


async def test_success_summary_counts_bugs_and_successes(monkeypatch):
    async def fake_run(url, personas, provider, **kwargs):
        return [
            SessionResult(
                persona_name="A",
                status=SessionStatus.SUCCESS,
                bugs=[BugReport(title="b1"), BugReport(title="b2")],
            ),
            SessionResult(persona_name="B", status=SessionStatus.GAVE_UP),
        ]

    monkeypatch.setattr(runner, "_run_with_playwright", fake_run)
    result = await runner.execute_run(
        {"url": "u", "personas": [{"name": "A", "intent": {"goal": "g"}}]},
        {"provider": "fake", "config": {}},
    )
    assert result["summary"]["bugs"] == 2
    assert result["summary"]["succeeded"] == 1
    assert result["summary"]["personas"] == 2
    # Fake provider has no usage; cost defaults to 0.
    assert result["summary"]["cost_usd"] == 0.0
    assert len(result["sessions"]) == 2
