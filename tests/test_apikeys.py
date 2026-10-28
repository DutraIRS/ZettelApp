import pytest

from zettelapp.core import apikeys


@pytest.fixture
def store(monkeypatch, tmp_path):
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    saved: dict[str, str] = {}
    monkeypatch.setattr(apikeys, "get_secret", saved.get)
    monkeypatch.setattr(apikeys, "set_secret", lambda n, v: saved.__setitem__(n, v))
    monkeypatch.setattr(apikeys, "delete_secret", lambda n: saved.pop(n, None))
    return saved


def test_several_keys_per_provider_and_switching(store):
    assert not apikeys.has_key("anthropic")
    work = apikeys.add_key("anthropic", "Work", "sk-work")
    home = apikeys.add_key("anthropic", "Home", "sk-home")
    assert [k.label for k in apikeys.list_keys("anthropic")] == ["Work", "Home"]
    assert apikeys.active_secret("anthropic") == "sk-home"  # the newest becomes active
    apikeys.set_active("anthropic", work.id)
    assert apikeys.active_secret("anthropic") == "sk-work"
    assert apikeys.get_key("anthropic", home.id) == "sk-home"
    assert apikeys.list_keys("openai") == []  # other providers are separate


def test_rename_and_delete_pick_a_new_active_key(store):
    a = apikeys.add_key("openai", "A", "k-a")
    b = apikeys.add_key("openai", "B", "k-b")
    apikeys.rename_key("openai", a.id, "  Personal   key ")
    assert apikeys.list_keys("openai")[0].label == "Personal key"
    apikeys.delete_key("openai", b.id)
    assert apikeys.active_id("openai") == a.id
    assert apikeys.active_secret("openai") == "k-a"
    apikeys.delete_key("openai", a.id)
    assert apikeys.active_secret("openai") is None
    assert store == {}  # nothing left behind in the credential store


def test_a_key_saved_before_profiles_existed_is_the_default_one(store):
    store["llm/anthropic"] = "sk-old"
    assert [k.id for k in apikeys.list_keys("anthropic")] == ["default"]
    assert apikeys.active_secret("anthropic") == "sk-old"
    new = apikeys.add_key("anthropic", "Extra", "sk-new", make_active=False)
    assert apikeys.active_secret("anthropic") == "sk-old"
    apikeys.delete_key("anthropic", "default")
    assert [k.id for k in apikeys.list_keys("anthropic")] == [new.id]
    assert "llm/anthropic" not in store


def test_empty_key_is_rejected(store):
    with pytest.raises(ValueError):
        apikeys.add_key("anthropic", "x", "   ")
