"""The start-up update check: one small request, never an error, only plain versions."""

import io
import json
import urllib.error

import pytest

from zettelapp.core import updates


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _serve(monkeypatch, body: bytes | Exception):
    seen = []

    def fake_urlopen(request, timeout):
        seen.append((request.full_url, request.get_header("User-agent"), timeout))
        if isinstance(body, Exception):
            raise body
        return _Response(body)

    monkeypatch.setattr(updates.urllib.request, "urlopen", fake_urlopen)
    return seen


def test_versions_compare_numerically():
    assert updates.parse_version("1.10.0") == (1, 10)
    assert updates.parse_version("1.2") == updates.parse_version("1.2.0")
    for bad in ("1.0.0-beta", "v1.0", "", "1..2", "<b>1.0</b>", None, 7):
        assert updates.parse_version(bad) is None
    assert updates.is_newer("1.10.0", "1.9.3")
    assert not updates.is_newer("1.0", "1.0.0")
    assert not updates.is_newer("0.9.9", "1.0.0")
    assert not updates.is_newer("nonsense", "1.0.0")


def test_reads_the_version_from_the_website(monkeypatch):
    seen = _serve(monkeypatch, json.dumps({"name": "ZettelApp", "version": "1.4.2"}).encode())
    assert updates.latest_version() == "1.4.2"
    url, agent, timeout = seen[0]
    assert url == updates.VERSION_URL and url.startswith("https://")
    assert agent.startswith("ZettelApp/") and timeout <= 10


@pytest.mark.parametrize(
    "body",
    [
        urllib.error.URLError("offline"),
        TimeoutError(),
        OSError("blocked"),
        b"not json",
        b"[]",
        json.dumps({"version": "2.0.0-rc1"}).encode(),
        json.dumps({"version": 2}).encode(),
        json.dumps({"version": "9.9.9", "pad": "x" * updates.MAX_RESPONSE_BYTES}).encode(),
    ],
)
def test_any_failure_is_silent(monkeypatch, body):
    _serve(monkeypatch, body)
    assert updates.latest_version() is None
    assert updates.available_update() is None


def test_only_a_newer_version_is_an_update(monkeypatch):
    monkeypatch.setattr(updates, "latest_version", lambda: "999.0.0")
    assert updates.available_update() == "999.0.0"
    monkeypatch.setattr(updates, "latest_version", lambda: updates.__version__)
    assert updates.available_update() is None
