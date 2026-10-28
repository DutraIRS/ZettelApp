"""The note list: search, tag filter, sorting and the Trash."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QAbstractListModel, QModelIndex, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QFontMetrics, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QListView,
    QMenu,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from zettelapp.core.storage import Vault
from zettelapp.core.textutil import fold, snippet
from zettelapp.i18n import _, n_
from zettelapp.ui import icons, theme
from zettelapp.ui.widgets import SearchBox, accent_button, label, tool_button

ROW_HEIGHT = 78


class NoteListModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.rows: list[dict] = []

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return row["title"]
        if role == Qt.ItemDataRole.UserRole:
            return row
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return f"{row['title']}. {row['snippet']}"
        return None

    def set_rows(self, rows: list[dict]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class NoteDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index) -> QSize:  # noqa: N802
        return QSize(200, ROW_HEIGHT)

    def paint(self, painter: QPainter, option, index) -> None:
        t = theme.current()
        row = index.data(Qt.ItemDataRole.UserRole)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect).adjusted(6, 2, -6, -2)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if selected or hovered:
            path = QPainterPath()
            path.addRoundedRect(rect, 6, 6)
            painter.fillPath(path, t.q("accent_subtle") if selected else t.q("hover"))
        if selected:  # the Windows 11 selection "pill"
            pill = QPainterPath()
            pill.addRoundedRect(QRectF(rect.left(), rect.center().y() - 9, 3, 18), 1.5, 1.5)
            painter.fillPath(pill, t.q("accent"))
        inner = rect.adjusted(14, 9, -10, -8)
        title_font = theme.ui_font(10.5, theme.QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(t.q("text"))
        metrics = QFontMetrics(title_font)
        date = row["date"]
        date_font = theme.ui_font(8.5)
        date_width = QFontMetrics(date_font).horizontalAdvance(date)
        title = metrics.elidedText(
            row["title"], Qt.TextElideMode.ElideRight, int(inner.width() - date_width - 10)
        )
        painter.drawText(
            QRectF(inner.left(), inner.top(), inner.width(), metrics.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            title,
        )
        painter.setFont(date_font)
        painter.setPen(t.q("text_muted"))
        painter.drawText(
            QRectF(inner.left(), inner.top(), inner.width(), metrics.height()),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            date,
        )
        body_font = theme.ui_font(9)
        painter.setFont(body_font)
        painter.setPen(t.q("text_secondary"))
        body_metrics = QFontMetrics(body_font)
        text = body_metrics.elidedText(
            row["snippet"] or _("No text"), Qt.TextElideMode.ElideRight, int(inner.width())
        )
        painter.drawText(
            QRectF(
                inner.left(),
                inner.top() + metrics.height() + 3,
                inner.width(),
                body_metrics.height(),
            ),
            Qt.AlignmentFlag.AlignLeft,
            text,
        )
        extras = []
        if row["tags"]:
            extras.append("  ".join("#" + tag for tag in row["tags"][:4]))
        if row["links"]:
            extras.append(n_("{n} link", "{n} links", row["links"]).format(n=row["links"]))
        if row["cards"]:
            extras.append(n_("{n} card", "{n} cards", row["cards"]).format(n=row["cards"]))
        painter.setFont(date_font)
        painter.setPen(t.q("text_muted"))
        foot = QFontMetrics(date_font).elidedText(
            "  ·  ".join(extras), Qt.TextElideMode.ElideRight, int(inner.width())
        )
        painter.drawText(
            QRectF(
                inner.left(),
                inner.bottom() - QFontMetrics(date_font).height(),
                inner.width(),
                QFontMetrics(date_font).height(),
            ),
            Qt.AlignmentFlag.AlignLeft,
            foot,
        )
        painter.restore()


def _short_date(iso: str) -> str:
    try:
        when = datetime.fromisoformat(iso).astimezone()
    except ValueError:
        return ""
    now = datetime.now().astimezone()
    if when.date() == now.date():
        return when.strftime("%H:%M")
    if when.year == now.year:
        return when.strftime("%d %b")
    return when.strftime("%d %b %Y")


class NoteListPanel(QWidget):
    noteSelected = Signal(str)
    newNoteRequested = Signal()
    linkToCurrent = Signal(str, str)
    showInGraph = Signal(str)
    exportFrom = Signal(str)
    trashRequested = Signal(str)
    restoreRequested = Signal(str)
    purgeRequested = Signal(str)
    emptyTrashRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ListPane")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.vault: Vault | None = None
        self.trash_mode = False
        self.link_types: list = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 6, 8)
        layout.setSpacing(8)
        head = QHBoxLayout()
        head.setContentsMargins(6, 0, 4, 0)
        self.heading = label(_("Notes"), "heading")
        head.addWidget(self.heading)
        self.count = label("", "caption")
        head.addWidget(self.count, 1)
        self.new_button = accent_button(_("New"), self.newNoteRequested.emit, "add")
        self.new_button.setToolTip(_("New note (Ctrl+N)"))
        head.addWidget(self.new_button)
        layout.addLayout(head)
        self.search = SearchBox(_("Search notes (Ctrl+F) · tag:name filters"))
        layout.addWidget(self.search)
        filters = QHBoxLayout()
        self.tag_filter = QComboBox()
        self.tag_filter.setAccessibleName(_("Filter by tag"))
        self.sort = QComboBox()
        self.sort.setAccessibleName(_("Sort notes"))
        for text, key in (
            (_("Last edited"), "modified"),
            (_("Created"), "created"),
            (_("Title"), "title"),
            (_("Most linked"), "links"),
        ):
            self.sort.addItem(text, key)
        filters.addWidget(self.tag_filter, 1)
        filters.addWidget(self.sort)
        layout.addLayout(filters)
        self.model = NoteListModel()
        self.view = QListView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(NoteDelegate(self.view))
        self.view.setMouseTracking(True)
        self.view.setUniformItemSizes(True)
        self.view.setAccessibleName(_("Notes"))
        self.view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._menu)
        self.view.selectionModel().currentChanged.connect(self._current_changed)
        layout.addWidget(self.view, 1)
        foot = QHBoxLayout()
        self.trash_button = tool_button(
            "trash", _("Show the Trash"), self.toggle_trash, checkable=True, text=_("Trash")
        )
        foot.addWidget(self.trash_button)
        foot.addStretch(1)
        self.empty_trash = tool_button(
            "delete",
            _("Permanently delete everything in the Trash"),
            self.emptyTrashRequested.emit,
            text=_("Empty Trash"),
        )
        self.empty_trash.setVisible(False)
        foot.addWidget(self.empty_trash)
        layout.addLayout(foot)
        self._timer = QTimer(self, singleShot=True, interval=180, timeout=self.refresh)
        self.search.textChanged.connect(lambda _unused: self._timer.start())
        self.tag_filter.currentIndexChanged.connect(lambda _unused: self.refresh())
        self.sort.currentIndexChanged.connect(lambda _unused: self.refresh())

    def set_vault(self, vault: Vault | None) -> None:
        self.vault = vault
        self.refresh_tags()
        self.refresh()

    def refresh_tags(self) -> None:
        current = self.tag_filter.currentData()
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem(icons.icon("tag"), _("All tags"), None)
        if self.vault:
            for tag, n in self.vault.all_tags():
                self.tag_filter.addItem(f"#{tag}  ({n})", tag)
        self.tag_filter.setCurrentIndex(max(0, self.tag_filter.findData(current)))
        self.tag_filter.blockSignals(False)

    def toggle_trash(self) -> None:
        self.trash_mode = self.trash_button.isChecked()
        self.heading.setText(_("Trash") if self.trash_mode else _("Notes"))
        self.new_button.setVisible(not self.trash_mode)
        self.empty_trash.setVisible(self.trash_mode)
        self.refresh()

    def refresh(self) -> None:
        if self.vault is None:
            self.model.set_rows([])
            return
        selected = self.current_id()
        query = self.search.text().strip()
        tag = self.tag_filter.currentData()
        if tag:
            query += f" tag:{tag}"
        notes = {
            n.id: n
            for n in self.vault.all_notes(include_deleted=True)
            if n.deleted == self.trash_mode
        }
        if query.strip():
            ids = [
                i for i in self.vault.search(query, include_deleted=self.trash_mode) if i in notes
            ]
        else:
            ids = list(notes)
        degree: dict[str, int] = {}
        for l in self.vault.all_links():
            degree[l.src] = degree.get(l.src, 0) + 1
            degree[l.dst] = degree.get(l.dst, 0) + 1
        cards = self.vault.card_counts()
        key = self.sort.currentData()
        if not query.strip() or key != "modified":
            sorters = {
                "modified": lambda i: notes[i].modified,
                "created": lambda i: notes[i].created,
                "title": lambda i: fold(notes[i].display_title),
                "links": lambda i: degree.get(i, 0),
            }
            ids.sort(key=sorters[key], reverse=key in ("modified", "created", "links"))
        rows = [
            {
                "id": i,
                "title": notes[i].display_title,
                "snippet": snippet(notes[i].body, 160),
                "date": _short_date(notes[i].modified),
                "tags": notes[i].tags,
                "links": degree.get(i, 0),
                "cards": cards.get(i, 0),
            }
            for i in ids
        ]
        self.model.set_rows(rows)
        total = len(notes)
        self.count.setText(f"{len(rows)} of {total}" if len(rows) != total else f"{total}")
        if selected:
            self.select(selected, emit=False)

    def current_id(self) -> str | None:
        index = self.view.currentIndex()
        return index.data(Qt.ItemDataRole.UserRole)["id"] if index.isValid() else None

    def select(self, note_id: str | None, emit: bool = True) -> None:
        for row, data in enumerate(self.model.rows):
            if data["id"] == note_id:
                index = self.model.index(row)
                self.view.selectionModel().blockSignals(not emit)
                self.view.setCurrentIndex(index)
                self.view.selectionModel().blockSignals(False)
                self.view.scrollTo(index)
                self.view.viewport().update()
                return
        self.view.clearSelection()

    def _current_changed(self, current, _previous) -> None:
        if current.isValid():
            self.noteSelected.emit(current.data(Qt.ItemDataRole.UserRole)["id"])

    def _menu(self, pos) -> None:
        index = self.view.indexAt(pos)
        if not index.isValid():
            return
        note_id = index.data(Qt.ItemDataRole.UserRole)["id"]
        menu = QMenu(self)
        if self.trash_mode:
            menu.addAction(
                icons.icon("restore"), _("Restore"), lambda: self.restoreRequested.emit(note_id)
            )
            menu.addAction(
                icons.icon("delete"),
                _("Delete permanently…"),
                lambda: self.purgeRequested.emit(note_id),
            )
        else:
            menu.addAction(icons.icon("open"), _("Open"), lambda: self.noteSelected.emit(note_id))
            link_menu = menu.addMenu(icons.icon("link"), _("Link from the open note as"))
            for lt in self.link_types:
                link_menu.addAction(lt.label, lambda t=lt.id: self.linkToCurrent.emit(note_id, t))
            menu.addAction(
                icons.icon("graph"), _("Show in graph"), lambda: self.showInGraph.emit(note_id)
            )
            menu.addAction(
                icons.icon("export"),
                _("Export with linked notes…"),
                lambda: self.exportFrom.emit(note_id),
            )
            menu.addSeparator()
            menu.addAction(
                icons.icon("delete"), _("Move to Trash"), lambda: self.trashRequested.emit(note_id)
            )
        menu.exec(self.view.viewport().mapToGlobal(pos))
