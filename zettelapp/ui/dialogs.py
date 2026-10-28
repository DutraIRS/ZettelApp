"""Dialogs: link picker, flashcards, export, about and keyboard shortcuts."""

from __future__ import annotations

import platform
from collections.abc import Callable
from datetime import date
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from zettelapp import APP_NAME, DOCS_URL, HOMEPAGE_URL, REPO_URL, SPONSOR_URL, __version__
from zettelapp.core.export import FORMATS, FORMATS_BY_KEY
from zettelapp.core.models import Flashcard, LinkType
from zettelapp.core.storage import Vault
from zettelapp.core.textutil import fold
from zettelapp.i18n import N_, _
from zettelapp.paths import documents_dir, resource_path
from zettelapp.ui import icons, theme
from zettelapp.ui.widgets import ScopePicker, SearchBox, label


def _buttons(dialog: QDialog, ok_text: str | None = None) -> QDialogButtonBox:
    box = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    ok = box.button(QDialogButtonBox.StandardButton.Ok)
    ok.setText(ok_text or _("OK"))
    ok.setProperty("accent", True)
    ok.setDefault(True)
    box.accepted.connect(dialog.accept)
    box.rejected.connect(dialog.reject)
    return box


class LinkPickerDialog(QDialog):
    """Pick a note (searching by title or content) and a link type."""

    def __init__(
        self,
        vault: Vault,
        exclude: set[str],
        parent=None,
        title: str = N_("Link to note"),
        show_types: bool = True,
        initial_type: str = "related",
    ):
        super().__init__(parent)
        self.vault = vault
        self.setWindowTitle(_(title))
        self.resize(520, 520)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        self.search = SearchBox(_("Search notes by title or text"))
        layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.setAccessibleName(_("Notes"))
        layout.addWidget(self.list, 1)
        self.type_combo = QComboBox()
        self.type_combo.setAccessibleName(_("Link type"))
        for lt in vault.link_types():
            self.type_combo.addItem(self._swatch(lt), lt.label, lt.id)
        self.type_combo.setCurrentIndex(max(0, self.type_combo.findData(initial_type)))
        if show_types:
            row = QHBoxLayout()
            row.addWidget(label(_("Link type"), "secondary"))
            row.addWidget(self.type_combo, 1)
            layout.addLayout(row)
        layout.addWidget(_buttons(self, "Link"))
        self.titles = {i: t for i, t in vault.titles().items() if i not in exclude}
        self.search.textChanged.connect(self._refresh)
        self.list.itemDoubleClicked.connect(lambda _unused: self.accept())
        self._refresh()
        self.search.setFocus()

    @staticmethod
    def _swatch(lt: LinkType):
        from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

        px = QPixmap(14, 14)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(theme.current().entity(lt.color) if lt.color else QColor("#888"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 2, 10, 10)
        p.end()
        return QIcon(px)

    def _refresh(self) -> None:
        query = self.search.text().strip()
        if query:
            ids = [i for i in self.vault.search(query) if i in self.titles][:200]
            # Title matches first, then full-text matches.
            ids.sort(key=lambda i: fold(query) not in fold(self.titles[i]))
        else:
            ids = sorted(self.titles, key=lambda i: fold(self.titles[i]))[:500]
        self.list.clear()
        for note_id in ids:
            item = QListWidgetItem(icons.icon("document"), self.titles[note_id] or "Untitled")
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            item.setToolTip(note_id)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def selected(self) -> tuple[str, str] | None:
        item = self.list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole), self.type_combo.currentData()


class CardDialog(QDialog):
    def __init__(self, card: Flashcard, parent=None):
        super().__init__(parent)
        self.card = card
        self.setWindowTitle(_("Edit flashcard") if card.id else _("New flashcard"))
        self.resize(520, 420)
        form = QFormLayout(self)
        self.kind = QComboBox()
        self.kind.addItem(_("Question and answer"), "basic")
        self.kind.addItem(_("Cloze deletion  {{c1::hidden text}}"), "cloze")
        self.kind.setCurrentIndex(1 if card.kind == "cloze" else 0)
        self.front = QPlainTextEdit(card.front)
        self.back = QPlainTextEdit(card.back)
        self.front.setAccessibleName(_("Front"))
        self.back.setAccessibleName(_("Back"))
        form.addRow(_("Type"), self.kind)
        form.addRow(_("Front"), self.front)
        self.back_label = QLabel(_("Back"))
        form.addRow(self.back_label, self.back)
        hint = label(
            _(
                "Markdown, [[links]] and images work on both sides. Cloze cards hide each "
                "{{c1::…}} in turn."
            ),
            "caption",
            wrap=True,
        )
        form.addRow(hint)
        form.addRow(_buttons(self, "Save"))
        self.kind.currentIndexChanged.connect(self._update)
        self._update()

    def _update(self) -> None:
        cloze = self.kind.currentData() == "cloze"
        self.back_label.setText(_("Extra (optional)") if cloze else _("Back"))

    def accept(self) -> None:
        if not self.front.toPlainText().strip():
            self.front.setFocus()
            return
        self.card.kind = self.kind.currentData()
        self.card.front = self.front.toPlainText().strip()
        self.card.back = self.back.toPlainText().strip()
        super().accept()


class ExportDialog(QDialog):
    """Choose what to export (collection, subgraph or tag) and the format."""

    def __init__(
        self,
        vault: Vault,
        current_note: str | None,
        resolve_scope: Callable,
        parent=None,
        initial_scope: str = "all",
    ):
        super().__init__(parent)
        self.vault = vault
        self.resolve_scope = resolve_scope
        self.setWindowTitle(_("Export"))
        self.resize(560, 480)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(label(_("What to export"), "section"))
        self.scope = ScopePicker(allow_current=current_note is not None)
        self.scope.set_tags(vault.all_tags())
        self.scope.set_mode(initial_scope)
        layout.addWidget(self.scope)
        self.summary = label("", "secondary")
        layout.addWidget(self.summary)
        layout.addWidget(label(_("Format"), "section"))
        self.group = QButtonGroup(self)
        for i, fmt in enumerate(FORMATS):
            radio = QRadioButton(f"{fmt.label} ({fmt.extension})")
            radio.setToolTip(fmt.description)
            radio.setProperty("fmt", fmt.key)
            self.group.addButton(radio, i)
            layout.addWidget(radio)
            if i == 0:
                radio.setChecked(True)
        self.description = label("", "caption", wrap=True)
        layout.addWidget(self.description)
        layout.addStretch(1)
        layout.addWidget(_buttons(self, _("Export…")))
        self.scope.changed.connect(self._update)
        self.group.buttonToggled.connect(lambda *_unused: self._update())
        self._update()

    def fmt(self) -> str:
        return self.group.checkedButton().property("fmt")

    def note_ids(self) -> set[str]:
        return self.resolve_scope(*self.scope.value())

    def _update(self) -> None:
        ids = self.note_ids()
        links = sum(1 for l in self.vault.all_links() if l.src in ids and l.dst in ids)
        cards = len(self.vault.cards_for_notes(ids))
        self.summary.setText(
            _("{len} notes · {links} links · {cards} flashcards").format(
                len=len(ids), links=links, cards=cards
            )
        )
        self.description.setText(FORMATS_BY_KEY[self.fmt()].description)

    def destination(self) -> Path | None:
        fmt = FORMATS_BY_KEY[self.fmt()]
        mode, depth, tag = self.scope.value()
        suffix = {"all": "", "subgraph": " subgraph", "tag": f" {tag}"}.get(mode, "")
        name = f"{self.vault.name}{suffix} {date.today():%Y-%m-%d}{fmt.extension}"
        path, _unused = QFileDialog.getSaveFileName(
            self, _("Export"), str(documents_dir() / name), fmt.file_filter
        )
        return Path(path) if path else None


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("About {APP_NAME}").format(APP_NAME=APP_NAME))
        self.setFixedWidth(460)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        head = QHBoxLayout()
        logo = QLabel()
        logo_path = resource_path("icon-256.png")
        if logo_path.exists():
            from PySide6.QtGui import QPixmap

            logo.setPixmap(
                QPixmap(str(logo_path)).scaled(
                    QSize(64, 64),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        head.addWidget(logo)
        names = QVBoxLayout()
        names.addWidget(label(APP_NAME, "title"))
        names.addWidget(label(_("Version {version__}").format(version__=__version__), "secondary"))
        head.addLayout(names, 1)
        layout.addLayout(head)
        text = QLabel(
            _(
                'A Zettelkasten for Windows: atomic notes, typed links, mind maps, flashcards and a knowledge graph, with link suggestions that learn from you.<br><br><a href="{HOMEPAGE_URL}">Website</a> · <a href="{DOCS_URL}">Documentation</a> · <a href="{REPO_URL}">Source code</a><br><br>ZettelApp is free. If it helps you, please consider a donation.<br><br>Released into the public domain (The Unlicense). Built with Qt for Python (LGPLv3), NumPy, RapidFuzz, genanki, markdown-it-py, PyYAML and the Anthropic SDK; see THIRD_PARTY_NOTICES.md for licences.<br><br><span>Python {python_version} · {system} {release}</span>'
            ).format(
                HOMEPAGE_URL=HOMEPAGE_URL,
                DOCS_URL=DOCS_URL,
                REPO_URL=REPO_URL,
                python_version=platform.python_version(),
                system=platform.system(),
                release=platform.release(),
            )
        )
        text.setWordWrap(True)
        text.setOpenExternalLinks(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(text)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        donate = QPushButton(_("Donate on Ko-fi"))
        donate.setIcon(icons.icon("heart", theme.current().on_accent))
        donate.setProperty("accent", True)
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(SPONSOR_URL)))
        box.addButton(donate, QDialogButtonBox.ButtonRole.ActionRole)
        box.rejected.connect(self.reject)
        box.accepted.connect(self.accept)
        layout.addWidget(box)


SHORTCUTS = [
    (
        N_("Notes"),
        [
            (N_("New note"), "Ctrl+N"),
            (N_("Find notes"), "Ctrl+F"),
            (N_("Link to note"), "Ctrl+K"),
            (N_("Insert image"), "Ctrl+Shift+I"),
            (N_("Add flashcard"), "Ctrl+Shift+F"),
            (N_("Cite a Zotero reference"), N_("Insert ▸ Zotero Reference")),
            (N_("Toggle edit / preview"), "Ctrl+E"),
            (N_("Move note to Trash"), "Ctrl+Delete"),
            (N_("Bold / italic"), "Ctrl+B / Ctrl+I"),
        ],
    ),
    (
        N_("Navigate"),
        [
            (N_("Notes"), "Ctrl+1"),
            (N_("Graph"), "Ctrl+2"),
            (N_("Insights"), "Ctrl+3"),
            (N_("Review"), "Ctrl+4"),
            (N_("Ask your notes"), "Ctrl+5"),
            (N_("Full screen"), "F11"),
        ],
    ),
    (
        N_("Files"),
        [
            (N_("Open vault"), "Ctrl+O"),
            (N_("Export"), "Ctrl+Shift+E"),
            (N_("Options"), "Ctrl+,"),
            (N_("Help"), "F1"),
            (N_("Exit"), "Alt+F4"),
        ],
    ),
    (
        N_("Mind map"),
        [
            (N_("Add child"), N_("Tab")),
            (N_("Add sibling"), N_("Enter")),
            (N_("Rename"), "F2"),
            ("Delete", N_("Del")),
            (N_("Move selection"), N_("Arrow keys")),
        ],
    ),
    (
        N_("Review"),
        [(N_("Show answer"), N_("Space")), (N_("Again / Hard / Good / Easy"), "1 / 2 / 3 / 4")],
    ),
]


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Keyboard shortcuts"))
        self.resize(460, 560)
        layout = QVBoxLayout(self)
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels([_("Action"), _("Shortcut")])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.horizontalHeader().setStretchLastSection(True)
        for group, rows in SHORTCUTS:
            r = table.rowCount()
            table.insertRow(r)
            head = QTableWidgetItem(_(group))
            font = head.font()
            font.setBold(True)
            head.setFont(font)
            table.setItem(r, 0, head)
            for action, keys in rows:
                r = table.rowCount()
                table.insertRow(r)
                table.setItem(r, 0, QTableWidgetItem("    " + _(action)))
                table.setItem(r, 1, QTableWidgetItem(_(keys)))
        table.resizeColumnToContents(0)
        layout.addWidget(table)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        box.rejected.connect(self.reject)
        layout.addWidget(box)


class TextPromptDialog(QDialog):
    """A small dialog with one line edit (used for web links and new tags)."""

    def __init__(
        self, title: str, prompt: str, text: str = "", parent=None, ok_text: str | None = None
    ):
        super().__init__(parent)
        self.setWindowTitle(_(title))
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.addWidget(label(prompt, "secondary", wrap=True))
        self.edit = QLineEdit(text)
        layout.addWidget(self.edit)
        layout.addWidget(_buttons(self, ok_text))

    def value(self) -> str:
        return self.edit.text().strip()
