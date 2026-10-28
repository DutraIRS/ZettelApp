"""Search the Zotero library and cite an item or start a literature note."""

from __future__ import annotations

import html

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
)

from zettelapp import settings
from zettelapp.core.zotero import ZoteroClient, ZoteroItem
from zettelapp.i18n import _, n_
from zettelapp.ui import icons
from zettelapp.ui.widgets import SearchBox, label
from zettelapp.ui.workers import run_task


class ZoteroDialog(QDialog):
    """Returns the chosen item and action ("cite" or "note") via ``result_item``/``action``."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Zotero reference"))
        self.resize(780, 520)
        self.client = ZoteroClient(settings.get(settings.ZOTERO_PORT))
        self.result_item: ZoteroItem | None = None
        self.action = ""
        self.pdf_key: str | None = None
        self._request = 0
        layout = QVBoxLayout(self)
        self.search = SearchBox(_("Search Zotero by title, author or year"))
        layout.addWidget(self.search)
        self.state = label("", "caption", wrap=True)
        layout.addWidget(self.state)
        split = QSplitter(Qt.Orientation.Horizontal)
        self.results = QListWidget()
        self.results.setAccessibleName(_("Zotero items"))
        self.results.setWordWrap(True)
        self.details = QTextBrowser()
        self.details.setOpenLinks(False)
        split.addWidget(self.results)
        split.addWidget(self.details)
        split.setSizes([420, 340])
        layout.addWidget(split, 1)
        buttons = QDialogButtonBox()
        self.cite_button = QPushButton(_("Insert citation"))
        self.cite_button.setIcon(icons.icon("link"))
        self.cite_button.setProperty("accent", True)
        self.note_button = QPushButton(_("New literature note"))
        self.note_button.setIcon(icons.icon("add"))
        buttons.addButton(self.cite_button, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(self.note_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        self.cite_button.clicked.connect(lambda: self._finish("cite"))
        self.note_button.clicked.connect(lambda: self._finish("note"))
        row = QHBoxLayout()
        row.addWidget(
            label(
                _(
                    "Needs Zotero 7+ running, with Settings ▸ Advanced ▸ “Allow other applications on this "
                    "computer to communicate with Zotero” turned on."
                ),
                "caption",
                wrap=True,
            ),
            1,
        )
        row.addWidget(buttons)
        layout.addLayout(row)
        self._timer = QTimer(self, singleShot=True, interval=300, timeout=self._run_search)
        self.search.textChanged.connect(lambda _unused: self._timer.start())
        self.results.currentItemChanged.connect(self._show_details)
        self.results.itemDoubleClicked.connect(lambda _unused: self._finish("cite"))
        self._enable(False)
        self._run_search()

    def _enable(self, on: bool) -> None:
        self.cite_button.setEnabled(on)
        self.note_button.setEnabled(on)

    def _run_search(self) -> None:
        self._request += 1
        request = self._request
        query = self.search.text()
        self.state.setText(_("Searching Zotero…"))

        def done(items: list[ZoteroItem]) -> None:
            if request != self._request:
                return
            self.results.clear()
            for item in items:
                entry = QListWidgetItem(
                    icons.icon("document"), f"{item.short_citation()}\n{item.title}"
                )
                entry.setData(Qt.ItemDataRole.UserRole, item)
                self.results.addItem(entry)
            self.state.setText(
                (
                    n_("{n} item", "{n} items", len(items))
                    if query.strip()
                    else n_(
                        "{n} item (most recently modified)",
                        "{n} items (most recently modified)",
                        len(items),
                    )
                ).format(n=len(items))
            )
            if items:
                self.results.setCurrentRow(0)
            else:
                self._enable(False)

        def failed(message: str) -> None:
            if request == self._request:
                self.results.clear()
                self.state.setText(message)
                self._enable(False)

        run_task(self.client.search, query, on_done=done, on_error=failed)

    def _show_details(self, current, _previous) -> None:
        item: ZoteroItem | None = current.data(Qt.ItemDataRole.UserRole) if current else None
        self._enable(item is not None)
        if item is None:
            self.details.clear()
            return
        esc = html.escape
        rows = [
            f"<h3>{esc(item.title)}</h3>",
            f"<p>{esc('; '.join(item.creators) or _('Unknown author'))}"
            f" · {esc(item.year or _('n.d.'))}</p>",
        ]
        if item.publication:
            rows.append(f"<p><i>{esc(item.publication)}</i></p>")
        if item.doi:
            rows.append(f"<p>DOI {esc(item.doi)}</p>")
        if item.abstract:
            rows.append(
                f"<p>{esc(item.abstract[:900])}{'…' if len(item.abstract) > 900 else ''}</p>"
            )
        if item.tags:
            rows.append("<p>" + " ".join(f"#{esc(t)}" for t in item.tags[:12]) + "</p>")
        self.details.setHtml("".join(rows))

    def _finish(self, action: str) -> None:
        current = self.results.currentItem()
        if current is None:
            return
        self.result_item = current.data(Qt.ItemDataRole.UserRole)
        self.action = action
        if action != "note":
            self.accept()
            return

        self._enable(False)
        self.state.setText(_("Finding a PDF attachment…"))

        def done(pdf_key: str | None) -> None:
            self.pdf_key = pdf_key
            self.accept()

        def failed(_message: str) -> None:
            self.pdf_key = None
            self.accept()

        run_task(
            self.client.pdf_attachment,
            self.result_item.key,
            on_done=done,
            on_error=failed,
        )
