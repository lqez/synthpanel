from synthpanel.browser.observer import serialize_a11y_tree


def test_serialize_nested_tree():
    snapshot = {
        "role": "WebArea",
        "name": "Home",
        "children": [
            {"role": "button", "name": "Sign in"},
            {
                "role": "navigation",
                "children": [{"role": "link", "name": "About"}],
            },
        ],
    }
    text = serialize_a11y_tree(snapshot)
    assert 'button "Sign in"' in text
    assert 'link "About"' in text


def test_empty_snapshot():
    assert serialize_a11y_tree(None) == "(empty page)"


def test_truncation():
    big = {"role": "list", "children": [{"role": "listitem", "name": str(i)} for i in range(500)]}
    text = serialize_a11y_tree(big, max_lines=10)
    assert "truncated" in text
