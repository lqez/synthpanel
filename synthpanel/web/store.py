"""SQLite persistence for settings, projects, and run history.

Single-user local app, so a plain stdlib sqlite3 connection per call is enough.
The DB lives at ~/.synthpanel/synthpanel.db, overridable via SYNTHPANEL_DB for
tests. `settings` holds exactly one row: the last-used provider config, so the
onboarding flow can skip provider setup on subsequent sessions.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def default_db_path() -> Path:
    override = os.environ.get("SYNTHPANEL_DB")
    if override:
        return Path(override)
    return Path.home() / ".synthpanel" / "synthpanel.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def artifacts_dir(self, run_id: int) -> Path:
        """Directory for a run's debugging artifacts (traces/videos), beside the DB."""
        return self.path.parent / "artifacts" / f"run_{run_id}"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    provider TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    language TEXT NOT NULL DEFAULT 'en'
                );
                INSERT OR IGNORE INTO preferences (id, language) VALUES (1, 'en');
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    focus TEXT NOT NULL DEFAULT '',
                    personas_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                );
                """
            )
            # Lightweight migration: add projects.language to older DBs.
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(projects)")}
            if "language" not in cols:
                conn.execute("ALTER TABLE projects ADD COLUMN language TEXT")

    # --- preferences (app-global) ---

    def get_language(self) -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT language FROM preferences WHERE id = 1").fetchone()
        return row["language"] if row else "en"

    def set_language(self, language: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO preferences (id, language) VALUES (1, ?) "
                "ON CONFLICT(id) DO UPDATE SET language = excluded.language",
                (language,),
            )

    # --- settings (last-used provider config) ---

    def get_settings(self) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        if row is None:
            return None
        return {"provider": row["provider"], "config": json.loads(row["config_json"])}

    def save_settings(self, provider: str, config: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO settings (id, provider, config_json, updated_at)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    provider = excluded.provider,
                    config_json = excluded.config_json,
                    updated_at = excluded.updated_at
                """,
                (provider, json.dumps(config), _now()),
            )

    # --- projects ---

    def list_projects(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()
        return [self._project_row(r) for r in rows]

    def get_project(self, project_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return self._project_row(row) if row else None

    def create_project(
        self,
        name: str,
        url: str,
        focus: str,
        personas: list[dict],
        language: str | None = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO projects (name, url, focus, personas_json, language, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, url, focus, json.dumps(personas), language, _now()),
            )
            return int(cur.lastrowid)

    def project_language(self, project: dict) -> str:
        """Effective report language: the project's, falling back to the global default."""
        return project.get("language") or self.get_language()

    @staticmethod
    def _project_row(row: sqlite3.Row) -> dict:
        keys = row.keys()
        return {
            "id": row["id"],
            "name": row["name"],
            "url": row["url"],
            "focus": row["focus"],
            "personas": json.loads(row["personas_json"]),
            "language": row["language"] if "language" in keys else None,
            "created_at": row["created_at"],
        }

    # --- runs ---

    def create_run(self, project_id: int, status: str = "running") -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO runs (project_id, status, created_at) VALUES (?, ?, ?)",
                (project_id, status, _now()),
            )
            return int(cur.lastrowid)

    def finish_run(self, run_id: int, status: str, result: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET status = ?, result_json = ? WHERE id = ?",
                (status, json.dumps(result), run_id),
            )

    def list_runs(self, project_id: int) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM runs WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
        return [self._run_row(r) for r in rows]

    def get_run(self, run_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return self._run_row(row) if row else None

    @staticmethod
    def _run_row(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "status": row["status"],
            "result": json.loads(row["result_json"]),
            "created_at": row["created_at"],
        }
