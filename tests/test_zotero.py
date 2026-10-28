import io
import json
import urllib.error

import pytest

from zettelapp.core import zotero
from zettelapp.core.render import NoteRenderer
from zettelapp.core.security import is_zotero_url, normalize_source_url
from zettelapp.core.zotero import (
    ZoteroClient,
    ZoteroError,
    citation_markdown,
    literature_note,
    parse_item,
)

ITEM = {
    "key": "ABCD2345",
    "library": {"type": "user", "id": 0},
    "meta": {"creatorSummary": "Ebbinghaus", "parsedDate": "1885-01-01"},
    "data": {
        "key": "ABCD2345",
        "itemType": "book",
        "title": "Memory: A Contribution to Experimental Psychology",
        "creators": [{"creatorType": "author", "firstName": "Hermann", "lastName": "Ebbinghaus"}],
        "date": "1885",
        "DOI": "https://doi.org/10.1037/10011-000",
        "url": "javascript:alert(1)",
        "abstractNote": "Classic study of forgetting.",
        "publisher": "Teachers College",
        "tags": [{"tag": "Memory Research"}, {"tag": 5}],
    },
}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_opener(payload=None, error=None):
    class Opener:
        def __init__(self):
            self.requests = []

        def open(self, request, timeout=None):
            self.requests.append(request)
            if error:
                raise error
            return FakeResponse(json.dumps(payload).encode())

    return Opener()


def test_parse_item_validates_fields():
    item = parse_item(ITEM)
    assert item.key == "ABCD2345"
    assert item.creators == ["Ebbinghaus, H."]
    assert item.year == "1885"
    assert item.doi == "10.1037/10011-000"
    assert item.url == ""  # javascript: dropped
    assert item.tags == ["memory-research"]
    assert item.short_citation() == "Ebbinghaus (1885)"
    assert "Teachers College" in item.reference()
    assert parse_item({"key": "../../x", "data": {"key": "../../x"}}) is None
    assert parse_item({"data": {"key": "ABCD2345", "itemType": "attachment"}}) is None


def test_citation_and_literature_note():
    item = parse_item(ITEM)
    cite = citation_markdown(item)
    assert cite == "[Ebbinghaus (1885)](zotero://select/library/items/ABCD2345)"
    title, body, tags, url = literature_note(item, pdf_key="PDFK2345")
    assert title.startswith("Memory")
    assert "zotero://open-pdf/library/items/PDFK2345" in body
    assert "https://doi.org/10.1037/10011-000" in body
    assert tags[0] == "literature" and url == "zotero://select/library/items/ABCD2345"
    html = NoteRenderer(lambda _t: None).render(body)
    assert 'href="zotero://select/library/items/ABCD2345"' in html


def test_client_search_and_errors(monkeypatch):
    client = ZoteroClient()
    client._opener = fake_opener([ITEM, {"data": {"key": "bad"}}])
    items = client.search("ebbinghaus")
    assert [i.key for i in items] == ["ABCD2345"]
    url = client._opener.requests[0].full_url
    assert url.startswith("http://127.0.0.1:23119/api/users/0/items/top?") and "q=ebbinghaus" in url
    client._opener = fake_opener(error=urllib.error.HTTPError("u", 403, "Forbidden", {}, None))
    with pytest.raises(ZoteroError, match="Allow other applications"):
        client.search("x")
    client._opener = fake_opener(error=urllib.error.URLError("refused"))
    with pytest.raises(ZoteroError, match="running"):
        client.search("x")


def test_pdf_attachment_lookup():
    client = ZoteroClient()
    client._opener = fake_opener(
        [
            {"data": {"key": "NOTE2345", "itemType": "note"}},
            {"data": {"key": "PDFK2345", "contentType": "application/pdf"}},
        ]
    )
    assert client.pdf_attachment("ABCD2345") == "PDFK2345"
    assert client.pdf_attachment("../evil") is None


def test_zotero_urls_and_source_links(vault):
    assert is_zotero_url(zotero.pdf_url("ABCD2345", page=3))
    assert not is_zotero_url("zotero://select/library/items/abcd2345")  # keys are upper-case
    assert (
        normalize_source_url("zotero://select/library/items/ABCD2345")
        == "zotero://select/library/items/ABCD2345"
    )
    note = vault.create_note("Lit", url="zotero://select/library/items/ABCD2345")
    assert vault.get_note(note.id).url == "zotero://select/library/items/ABCD2345"
    note.url = "zotero://run/calc"
    vault.save_note(note)
    assert vault.get_note(note.id).url == ""
