from synthpanel.web.store import Store


def _store(tmp_path):
    return Store(tmp_path / "db.sqlite")


def test_seeded_from_library_on_first_init(tmp_path):
    s = _store(tmp_path)
    personas = s.list_personas()
    assert len(personas) >= 3
    assert any(p["name"] == "김순자" for p in personas)
    assert all(p["source"] == "library" for p in personas)


def test_seed_runs_once(tmp_path):
    db = tmp_path / "db.sqlite"
    s1 = Store(db)
    count = len(s1.list_personas())
    s2 = Store(db)  # re-open: must not re-seed
    assert len(s2.list_personas()) == count


def test_create_get_delete(tmp_path):
    s = _store(tmp_path)
    pid = s.create_persona(
        {"name": "Custom", "archetype": "x", "intent": {"goal": "do x"}}, source="custom"
    )
    got = s.get_persona(pid)
    assert got["name"] == "Custom"
    assert got["data"]["intent"]["goal"] == "do x"
    assert got["source"] == "custom"

    s.delete_persona(pid)
    assert s.get_persona(pid) is None


def test_ensure_persona_dedupes_by_name(tmp_path):
    s = _store(tmp_path)
    before = len(s.list_personas())
    a = s.ensure_persona({"name": "Dup", "intent": {"goal": "g"}})
    b = s.ensure_persona({"name": "Dup", "intent": {"goal": "different"}})
    assert a == b  # same id, not a second row
    assert len(s.list_personas()) == before + 1
