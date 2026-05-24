import json
import logging
import urllib.error
import urllib.request
from typing import NamedTuple


class UpdateInfo(NamedTuple):
    version: str
    url: str


def check_for_update() -> UpdateInfo | None:
    """Query GitHub Releases for a newer version. Returns UpdateInfo or None.

    All errors are swallowed and logged at DEBUG — a failed update check
    should never surface to the user.
    """
    from .version import __version__, GITHUB_REPO

    if not GITHUB_REPO:
        logging.debug("Update check skipped: GITHUB_REPO not configured")
        return None

    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        req = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"ScreenSwitchWidget/{__version__}",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        logging.debug("Update check failed: %s", exc)
        return None

    tag = data.get("tag_name", "").lstrip("v")
    if not tag or not _is_newer(tag, __version__):
        return None

    return UpdateInfo(version=tag, url=data.get("html_url", ""))


def _is_newer(latest: str, current: str) -> bool:
    try:
        return _parse(latest) > _parse(current)
    except (ValueError, TypeError):
        return False


def _parse(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.split("."))
