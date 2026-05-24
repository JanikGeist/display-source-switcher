from src.updater import _is_newer


def test_newer_minor():
    assert _is_newer("0.2.0", "0.1.0")


def test_newer_patch():
    assert _is_newer("0.1.1", "0.1.0")


def test_newer_major():
    assert _is_newer("1.0.0", "0.9.9")


def test_same_version_is_not_newer():
    assert not _is_newer("0.1.0", "0.1.0")


def test_older_version_is_not_newer():
    assert not _is_newer("0.0.9", "0.1.0")


def test_malformed_latest_returns_false():
    assert not _is_newer("not-a-version", "0.1.0")


def test_malformed_current_returns_false():
    assert not _is_newer("0.2.0", "not-a-version")
