"""Aggregate per-session results into prioritized cross-persona issues.

A lightweight clustering: bugs are grouped by a normalized title, ranked by
severity then frequency, so issues hit by many personas surface first. (An
embedding-based clustering can replace the normalizer later without changing the
interface.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from synthpanel.report.models import SessionResult, Severity

_SEVERITY_RANK = {Severity.CRITICAL: 0, Severity.MAJOR: 1, Severity.MINOR: 2}


def _normalize(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


@dataclass
class IssueCluster:
    title: str
    severity: Severity
    count: int = 0
    personas: list[str] = field(default_factory=list)


@dataclass
class Aggregate:
    issues: list[IssueCluster]
    total_bugs: int
    personas: int
    succeeded: int


def aggregate(results: list[SessionResult]) -> Aggregate:
    clusters: dict[str, IssueCluster] = {}
    total = 0
    for result in results:
        for bug in result.bugs:
            total += 1
            key = _normalize(bug.title)
            cluster = clusters.get(key)
            if cluster is None:
                cluster = IssueCluster(title=bug.title, severity=bug.severity)
                clusters[key] = cluster
            cluster.count += 1
            # Keep the worst severity seen for this issue.
            if _SEVERITY_RANK[bug.severity] < _SEVERITY_RANK[cluster.severity]:
                cluster.severity = bug.severity
            who = bug.persona_name or result.persona_name
            if who and who not in cluster.personas:
                cluster.personas.append(who)

    issues = sorted(
        clusters.values(),
        key=lambda c: (_SEVERITY_RANK[c.severity], -c.count, c.title),
    )
    succeeded = sum(1 for r in results if r.status.value == "success")
    return Aggregate(
        issues=issues, total_bugs=total, personas=len(results), succeeded=succeeded
    )
