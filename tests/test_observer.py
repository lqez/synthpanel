from synthpanel.browser.observer import format_aria_snapshot

# A representative aria_snapshot() string (Playwright's modern accessibility API).
_SNAPSHOT = """- heading "Home" [level=1]
- button "Sign in"
- navigation:
  - link "About"
- textbox "Email\""""


def test_passes_through_snapshot_text():
    text = format_aria_snapshot(_SNAPSHOT)
    assert 'button "Sign in"' in text
    assert 'link "About"' in text
    assert 'textbox "Email"' in text


def test_empty_snapshot():
    assert format_aria_snapshot(None) == "(empty page)"
    assert format_aria_snapshot("   ") == "(empty page)"


def test_truncation():
    big = "\n".join(f'- listitem "{i}"' for i in range(500))
    text = format_aria_snapshot(big, max_lines=10)
    assert "truncated" in text
    assert len(text.splitlines()) == 11  # 10 lines + the truncation marker
