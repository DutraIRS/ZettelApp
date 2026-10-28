"""Anki integration: .apkg export (genanki) and live sync through AnkiConnect.

Every card carries its note's Zettel id and a zettelapp:// link, so clicking
the source on a card in Anki opens the note in ZettelApp. Model, deck and
note GUIDs are stable, so exporting again updates cards instead of
duplicating them.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from zettelapp.core.models import Flashcard, Note
from zettelapp.core.render import NoteRenderer
from zettelapp.core.security import app_url, is_valid_asset_name

BASIC_MODEL_ID = 1_733_870_101
CLOZE_MODEL_ID = 1_733_870_102
BASIC_MODEL_NAME = "ZettelApp Basic"
CLOZE_MODEL_NAME = "ZettelApp Cloze"
DEFAULT_DECK = "ZettelApp"

CARD_CSS = """
.card { font-family: "Segoe UI", system-ui, sans-serif; font-size: 20px; line-height: 1.5;
        color: #1b1b1b; background: #fafafa; text-align: left; max-width: 46em; margin: 0 auto; }
.nightMode.card, .night_mode .card { color: #f3f3f3; background: #202020; }
img { max-width: 100%; border-radius: 6px; }
code, pre { font-family: Consolas, monospace; font-size: 0.9em; }
pre { padding: 0.6em; border-radius: 6px; background: rgba(127,127,127,.12); overflow-x: auto; }
.cloze { font-weight: 600; color: #0f6cbd; }
.nightMode .cloze { color: #62b3ff; }
.source { margin-top: 1.5em; font-size: 0.7em; opacity: 0.7; }
.source a { color: inherit; }
hr#answer { border: none; border-top: 1px solid rgba(127,127,127,.35); margin: 1em 0; }
"""

FIELDS = ["Front", "Back", "Source", "ZettelID", "CardKey"]
CLOZE_FIELDS = ["Text", "Extra", "Source", "ZettelID", "CardKey"]
BASIC_TEMPLATE = {
    "name": "Card 1",
    "qfmt": "{{Front}}",
    "afmt": '{{FrontSide}}<hr id="answer">{{Back}}<div class="source">{{Source}}</div>',
}
CLOZE_TEMPLATE = {
    "name": "Cloze",
    "qfmt": "{{cloze:Text}}",
    "afmt": '{{cloze:Text}}<br>{{Extra}}<div class="source">{{Source}}</div>',
}

_SRC_RE = re.compile(r'<img src="([^"]+)"')


@dataclass
class CardPayload:
    card: Flashcard
    model: str
    fields: dict[str, str]
    tags: list[str]
    media: list[str]


def deck_id(name: str) -> int:
    return int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16) | (1 << 31)


def card_key(vault_id: str, card: Flashcard) -> str:
    return f"{vault_id[:12]}-{card.id}"


def anki_tag(tag: str) -> str:
    return re.sub(r"\s+", "_", tag.replace("/", "::"))


def build_payloads(cards: Sequence[Flashcard], notes: dict[str, Note], vault_id: str,
                   renderer: NoteRenderer) -> list[CardPayload]:
    payloads = []
    for card in cards:
        note = notes.get(card.note_id)
        if note is None:
            continue
        source = f'<a href="{html.escape(app_url(note.id), quote=True)}">{html.escape(note.display_title)}</a>'
        front_html = renderer.render(card.front)
        if card.kind == "cloze":
            model = CLOZE_MODEL_NAME
            fields = {"Text": front_html, "Extra": renderer.render(card.back) if card.back else ""}
        else:
            model = BASIC_MODEL_NAME
            fields = {"Front": front_html, "Back": renderer.render(card.back)}
        fields.update({"Source": source, "ZettelID": note.id, "CardKey": card_key(vault_id, card)})
        media = sorted({m for v in fields.values() for m in _SRC_RE.findall(v) if is_valid_asset_name(m)})
        tags = ["zettelapp"] + [anki_tag(t) for t in note.tags]
        payloads.append(CardPayload(card, model, fields, tags, media))
    return payloads


def anki_renderer(resolve: Callable[[str], str | None], title_of: Callable[[str], str]) -> NoteRenderer:
    """Renderer whose note links open ZettelApp and whose images are Anki media files."""
    return NoteRenderer(resolve, title_of, note_href=app_url, asset_href=lambda name: name,
                        allow_new_note_links=False, keep_cloze=True)


# --- .apkg export -------------------------------------------------------------

def write_apkg(payloads: Sequence[CardPayload], dest: Path, deck_name: str,
               asset_path: Callable[[str], Path | None], vault_id: str) -> int:
    import genanki

    basic = genanki.Model(BASIC_MODEL_ID, BASIC_MODEL_NAME, fields=[{"name": f} for f in FIELDS],
                          templates=[BASIC_TEMPLATE], css=CARD_CSS)
    cloze = genanki.Model(CLOZE_MODEL_ID, CLOZE_MODEL_NAME, fields=[{"name": f} for f in CLOZE_FIELDS],
                          templates=[CLOZE_TEMPLATE], css=CARD_CSS, model_type=genanki.Model.CLOZE)
    deck = genanki.Deck(deck_id(deck_name), deck_name)
    media_files: set[str] = set()
    for p in payloads:
        model = cloze if p.model == CLOZE_MODEL_NAME else basic
        order = CLOZE_FIELDS if p.model == CLOZE_MODEL_NAME else FIELDS
        deck.add_note(genanki.Note(
            model=model,
            fields=[p.fields.get(f, "") for f in order],
            tags=p.tags,
            guid=genanki.guid_for("zettelapp", vault_id, p.card.id),
        ))
        for name in p.media:
            path = asset_path(name)
            if path is not None:
                media_files.add(str(path))
    package = genanki.Package(deck)
    package.media_files = sorted(media_files)
    package.write_to_file(str(dest))
    return len(payloads)


# --- AnkiConnect --------------------------------------------------------------

class AnkiConnectError(RuntimeError):
    pass


@dataclass
class SyncReport:
    added: int = 0
    updated: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class AnkiConnect:
    """Minimal AnkiConnect client. Only talks to the local machine."""

    def __init__(self, port: int = 8765, timeout: float = 8.0):
        if not 1 <= int(port) <= 65535:
            raise ValueError("Invalid port")
        self.url = f"http://127.0.0.1:{int(port)}"
        self.timeout = timeout
        # No proxy: requests must never leave this computer.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def invoke(self, action: str, **params):
        payload = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
        request = urllib.request.Request(self.url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                data = json.loads(response.read(20_000_000).decode("utf-8"))
        except (urllib.error.URLError, OSError) as exc:
            raise AnkiConnectError(
                "Could not reach Anki. Make sure Anki is running with the AnkiConnect add-on installed.") from exc
        except ValueError as exc:
            raise AnkiConnectError("Anki sent an unexpected response.") from exc
        if not isinstance(data, dict) or "result" not in data or "error" not in data:
            raise AnkiConnectError("Anki sent an unexpected response.")
        if data["error"]:
            raise AnkiConnectError(str(data["error"]))
        return data["result"]

    def version(self) -> int:
        return int(self.invoke("version"))

    def ensure_models(self) -> None:
        names = set(self.invoke("modelNames"))
        if BASIC_MODEL_NAME not in names:
            self.invoke("createModel", modelName=BASIC_MODEL_NAME, inOrderFields=FIELDS, css=CARD_CSS,
                        isCloze=False, cardTemplates=[{"Name": BASIC_TEMPLATE["name"], "Front": BASIC_TEMPLATE["qfmt"],
                                                       "Back": BASIC_TEMPLATE["afmt"]}])
        if CLOZE_MODEL_NAME not in names:
            self.invoke("createModel", modelName=CLOZE_MODEL_NAME, inOrderFields=CLOZE_FIELDS, css=CARD_CSS,
                        isCloze=True, cardTemplates=[{"Name": CLOZE_TEMPLATE["name"], "Front": CLOZE_TEMPLATE["qfmt"],
                                                      "Back": CLOZE_TEMPLATE["afmt"]}])

    def browse(self, query: str) -> None:
        self.invoke("guiBrowse", query=query)

    def sync(self, payloads: Sequence[CardPayload], deck_name: str,
             asset_path: Callable[[str], Path | None],
             remember_id: Callable[[int, int | None], None],
             progress: Callable[[int, int], None] | None = None) -> SyncReport:
        report = SyncReport()
        self.invoke("createDeck", deck=deck_name)
        self.ensure_models()
        known = [p.card.anki_note_id for p in payloads if p.card.anki_note_id]
        alive = set()
        if known:
            for info in self.invoke("notesInfo", notes=known):
                if isinstance(info, dict) and info.get("noteId"):
                    alive.add(int(info["noteId"]))
        stored_media: set[str] = set()
        for n, p in enumerate(payloads, 1):
            try:
                for name in p.media:
                    path = asset_path(name)
                    if path is not None and name not in stored_media:
                        self.invoke("storeMediaFile", filename=name,
                                    data=base64.b64encode(path.read_bytes()).decode("ascii"))
                        stored_media.add(name)
                anki_id = p.card.anki_note_id
                if anki_id is None or anki_id not in alive:
                    found = self.invoke("findNotes", query=f"CardKey:{p.fields['CardKey']}")
                    anki_id = int(found[0]) if found else None
                if anki_id is not None:
                    self.invoke("updateNoteFields", note={"id": anki_id, "fields": p.fields})
                    self.invoke("addTags", notes=[anki_id], tags=" ".join(p.tags))
                    report.updated += 1
                else:
                    anki_id = int(self.invoke("addNote", note={
                        "deckName": deck_name, "modelName": p.model, "fields": p.fields, "tags": p.tags,
                        "options": {"allowDuplicate": False, "duplicateScope": "deck"},
                    }))
                    report.added += 1
                if anki_id != p.card.anki_note_id:
                    remember_id(p.card.id, anki_id)
            except AnkiConnectError as exc:
                report.failed += 1
                if len(report.errors) < 20:
                    report.errors.append(f"{p.fields.get('ZettelID')}: {exc}")
            if progress:
                progress(n, len(payloads))
        return report
