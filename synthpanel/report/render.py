"""Render a run's results into a Markdown report and a standalone HTML dashboard.

No template engine or extra deps here so reports can be produced anywhere (CLI,
tests, web download). The web app reuses these for /runs/{id}/report.{md,html}.
"""

from __future__ import annotations

import html

from synthpanel.report.aggregate import Aggregate, aggregate
from synthpanel.report.models import SessionResult


def render_markdown(title: str, results: list[SessionResult]) -> str:
    agg = aggregate(results)
    lines = [f"# Usability report — {title}", ""]
    lines += _summary_lines(agg)

    lines += ["", "## Top issues (aggregated)", ""]
    if agg.issues:
        for i, issue in enumerate(agg.issues, 1):
            who = ", ".join(issue.personas)
            lines.append(
                f"{i}. **[{issue.severity.value}]** {issue.title} "
                f"— {issue.count}× ({who})"
            )
    else:
        lines.append("_No bugs reported._")

    for result in results:
        lines += ["", f"## {result.persona_name} — {result.status.value}", ""]
        if result.ux_feedback.strip():
            lines += ["**UX feedback:**", result.ux_feedback.strip(), ""]
        if result.bugs:
            lines.append("**Bugs:**")
            for bug in result.bugs:
                lines.append(f"- [{bug.severity.value}] {bug.title}")
        lines.append("")
        lines.append(f"_Steps: {len(result.steps)}_")
    return "\n".join(lines)


def _summary_lines(agg: Aggregate) -> list[str]:
    return [
        f"- Personas: **{agg.personas}** "
        f"(succeeded {agg.succeeded}, gave up/failed {agg.personas - agg.succeeded})",
        f"- Total bugs: **{agg.total_bugs}** across **{len(agg.issues)}** distinct issues",
    ]


_SEV_COLOR = {"critical": "#c0392b", "major": "#d35400", "minor": "#7f8c8d"}


def render_html(title: str, results: list[SessionResult]) -> str:
    agg = aggregate(results)
    t = html.escape(title)

    issue_rows = "".join(
        f"<tr><td><span class='sev' style='background:{_SEV_COLOR.get(i.severity.value, '#777')}'>"
        f"{i.severity.value}</span></td><td>{html.escape(i.title)}</td>"
        f"<td>{i.count}</td><td>{html.escape(', '.join(i.personas))}</td></tr>"
        for i in agg.issues
    ) or "<tr><td colspan='4'>No bugs reported.</td></tr>"

    sessions = "".join(_session_html(r) for r in results)

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Report — {t}</title>
<style>
 body{{font-family:ui-sans-serif,system-ui,sans-serif;max-width:900px;margin:0 auto;padding:32px;color:#1a1a2e}}
 h1{{font-size:1.6rem}} h2{{font-size:1.15rem;margin-top:28px}}
 table{{width:100%;border-collapse:collapse;margin:12px 0}}
 td,th{{text-align:left;padding:8px 10px;border-bottom:1px solid #eee;vertical-align:top}}
 .sev{{color:#fff;border-radius:6px;padding:2px 8px;font-size:.8rem}}
 .card{{border:1px solid #ececf3;border-radius:12px;padding:16px;margin:14px 0}}
 .muted{{color:#6b7280}}
</style></head><body>
<h1>Usability report — {t}</h1>
<p>Personas: <strong>{agg.personas}</strong> · succeeded {agg.succeeded} ·
   bugs <strong>{agg.total_bugs}</strong> across {len(agg.issues)} issues</p>
<h2>Top issues (aggregated)</h2>
<table><tr><th>Severity</th><th>Issue</th><th>Count</th><th>Personas</th></tr>
{issue_rows}</table>
<h2>Sessions</h2>
{sessions}
</body></html>"""


def _session_html(r: SessionResult) -> str:
    bugs = "".join(
        f"<li><span class='sev' style='background:{_SEV_COLOR.get(b.severity.value, '#777')}'>"
        f"{b.severity.value}</span> {html.escape(b.title)}</li>"
        for b in r.bugs
    )
    feedback = (
        f"<p class='muted'>{html.escape(r.ux_feedback.strip())}</p>"
        if r.ux_feedback.strip()
        else ""
    )
    return (
        f"<div class='card'><strong>{html.escape(r.persona_name)}</strong> — {r.status.value}"
        f"{feedback}"
        f"{('<ul>' + bugs + '</ul>') if bugs else ''}"
        f"<p class='muted'>Steps: {len(r.steps)}</p></div>"
    )
