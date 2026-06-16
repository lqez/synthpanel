from synthpanel.web.store import Store


def _store(tmp_path):
    return Store(tmp_path / "db.sqlite")


def test_settings_roundtrip_single_row(tmp_path):
    s = _store(tmp_path)
    assert s.get_settings() is None
    s.save_settings("anthropic", {"api_key": "k", "model": "claude-opus-4-8"})
    got = s.get_settings()
    assert got["provider"] == "anthropic"
    assert got["config"]["model"] == "claude-opus-4-8"
    # Saving again upserts the single row, not a second one.
    s.save_settings("fake", {})
    assert s.get_settings()["provider"] == "fake"


def test_project_and_run_lifecycle(tmp_path):
    s = _store(tmp_path)
    assert s.list_projects() == []
    pid = s.create_project("App", "https://app.test", "checkout flow", [{"name": "김순자"}])
    project = s.get_project(pid)
    assert project["url"] == "https://app.test"
    assert project["personas"][0]["name"] == "김순자"

    rid = s.create_run(pid)
    assert s.get_run(rid)["status"] == "running"
    s.finish_run(rid, "done", {"summary": {"bugs": 2}})
    runs = s.list_runs(pid)
    assert len(runs) == 1
    assert runs[0]["status"] == "done"
    assert runs[0]["result"]["summary"]["bugs"] == 2
