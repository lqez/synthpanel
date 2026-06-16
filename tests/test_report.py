from synthpanel.report.aggregate import aggregate
from synthpanel.report.models import (
    BugReport,
    SessionResult,
    SessionStatus,
    Severity,
)
from synthpanel.report.render import render_html, render_markdown


def _results():
    return [
        SessionResult(
            persona_name="A",
            status=SessionStatus.GAVE_UP,
            bugs=[
                BugReport(title="Login button does nothing", severity=Severity.CRITICAL),
                BugReport(title="Slow page load", severity=Severity.MINOR),
            ],
            ux_feedback="Confusing nav.",
        ),
        SessionResult(
            persona_name="B",
            status=SessionStatus.SUCCESS,
            bugs=[BugReport(title="login button does nothing  ", severity=Severity.MAJOR)],
        ),
    ]


def test_aggregate_clusters_and_prioritizes():
    agg = aggregate(_results())
    assert agg.total_bugs == 3
    assert agg.personas == 2
    assert agg.succeeded == 1
    # The two login-button bugs (different casing/whitespace) cluster into one.
    top = agg.issues[0]
    assert top.count == 2
    assert top.severity is Severity.CRITICAL  # worst severity wins
    assert set(top.personas) == {"A", "B"}
    # Distinct issues = 2 (login cluster + slow load).
    assert len(agg.issues) == 2


def test_markdown_contains_summary_and_issues():
    md = render_markdown("My App", _results())
    assert "# Usability report — My App" in md
    assert "Login button does nothing" in md
    assert "Confusing nav." in md


def test_html_is_standalone_and_escaped():
    results = _results()
    results[0].bugs[0].title = "Break <script>alert(1)</script>"
    out = render_html("App", results)
    assert out.startswith("<!doctype html>")
    assert "<script>alert(1)" not in out  # escaped
    assert "&lt;script&gt;" in out
