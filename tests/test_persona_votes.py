"""Vote / favorite store methods and ordering."""

from synthpanel.web.store import Store


def _ids(store):
    return [p["id"] for p in store.list_personas()]


def test_vote_changes_score_and_order(tmp_path):
    s = Store(tmp_path / "db.sqlite")
    ids = _ids(s)
    last = ids[-1]
    # Upvote the last persona a few times -> it should rise to the top.
    for _ in range(3):
        s.vote_persona(last, 1)
    assert s.get_persona(last)["votes"] == 3
    assert s.list_personas()[0]["id"] == last


def test_downvote_goes_negative(tmp_path):
    s = Store(tmp_path / "db.sqlite")
    pid = _ids(s)[0]
    s.vote_persona(pid, -1)
    s.vote_persona(pid, -1)
    assert s.get_persona(pid)["votes"] == -2


def test_favorite_toggles_and_floats_to_top(tmp_path):
    s = Store(tmp_path / "db.sqlite")
    ids = _ids(s)
    last = ids[-1]
    s.toggle_favorite(last)
    assert s.get_persona(last)["favorite"] is True
    # Favorites sort above everything, even with zero votes.
    assert s.list_personas()[0]["id"] == last
    s.toggle_favorite(last)
    assert s.get_persona(last)["favorite"] is False
