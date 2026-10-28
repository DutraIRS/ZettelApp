"""Right-hand panel: link suggestions, outgoing links and backlinks."""

from __future__ import annotations

import html

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from zettelapp.core.models import Link, LinkType
from zettelapp.core.suggest import Suggestion
from zettelapp.i18n import _
from zettelapp.ui import icons, theme
from zettelapp.ui.link_style import LIST_ICON, MENU_ICON, type_icon
from zettelapp.ui.widgets import ElidedLabel, label, link_button, tool_button


class _SuggestionRow(QWidget):
    def __init__(self, s: Suggestion, panel: SidePanel):
        super().__init__()
        self.s = s
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 4, 2, 4)
        row.setSpacing(6)
        text = QVBoxLayout()
        text.setSpacing(3)
        title = ElidedLabel(s.title)
        title.setMinimumWidth(60)
        title.setCursor(Qt.CursorShape.PointingHandCursor)
        title.mousePressEvent = lambda _e: panel.openNote.emit(s.note_id)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(round(s.probability * 100))
        bar.setTextVisible(False)
        bar.setFixedHeight(4)
        bar.setAccessibleName(_("Match {p}").format(p=f"{s.probability:.0%}"))
        strength = (
            "strong" if s.probability >= 0.5 else "likely" if s.probability >= 0.25 else "possible"
        )
        meta = label(f"{s.probability:.0%} · {strength}", "caption")
        text.addWidget(title)
        text.addWidget(bar)
        text.addWidget(meta)
        row.addLayout(text, 1)
        link = QToolButton()
        link.setText(_("Link"))
        link.setIcon(icons.icon("link"))
        link.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        link.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        link.setToolTip(_("Link as “Related to”; use the arrow to choose another link type"))
        link.clicked.connect(lambda: panel.acceptSuggestion.emit(s.note_id, "related"))
        menu = QMenu(link)
        for lt in panel.link_types:
            menu.addAction(
                type_icon(lt, MENU_ICON),
                lt.label,
                lambda t=lt.id: panel.acceptSuggestion.emit(s.note_id, t),
            )
        link.setMenu(menu)
        row.addWidget(link)
        row.addWidget(
            tool_button(
                "cancel",
                _("Not related: dismiss and teach the model"),
                lambda: panel.rejectSuggestion.emit(s.note_id),
            )
        )
        self.setToolTip(self._explain())

    def _explain(self) -> str:
        rows = "".join(
            f"<tr><td>{html.escape(_(name))}</td><td align='right'>{'+' if v >= 0 else '−'}{abs(v):.2f}</td></tr>"
            for name, v in self.s.contributions
            if abs(v) >= 0.01
        )
        estimate = _("Naive Bayes estimate: {p}").format(p=f"{self.s.probability:.0%}")
        evidence = _("Evidence (log-likelihood ratio per feature):")
        return (
            f"<b>{html.escape(_('Why this suggestion?'))}</b><br>{html.escape(estimate)}<br>"
            f"<span>{html.escape(evidence)}</span><table>{rows}</table>"
        )


class SidePanel(QWidget):
    openNote = Signal(str)
    acceptSuggestion = Signal(str, str)
    rejectSuggestion = Signal(str)
    addLinkRequested = Signal()
    removeLink = Signal(str, str, str)
    changeLinkType = Signal(str, str, str, str)
    reverseLink = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidePane")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.link_types: list[LinkType] = []
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer.addWidget(scroll)
        content = QWidget()
        content.setObjectName("SidePane")
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 14, 10, 14)
        layout.setSpacing(8)

        head = QHBoxLayout()
        bulb = label()
        bulb.setPixmap(icons.icon("lightbulb", theme.current().accent).pixmap(18, 18))
        head.addWidget(bulb)
        head.addWidget(label(_("Suggested links"), "section"), 1)
        layout.addLayout(head)
        layout.addWidget(
            label(
                _(
                    "Naive Bayes over semantic, Levenshtein and tag similarity. "
                    "Learns from the links you make and dismiss."
                ),
                "caption",
                wrap=True,
            )
        )
        self.status = label("", "caption", wrap=True)
        layout.addWidget(self.status)
        self.suggestions = QVBoxLayout()
        self.suggestions.setSpacing(2)
        layout.addLayout(self.suggestions)

        layout.addSpacing(10)
        links_head = QHBoxLayout()
        links_head.addWidget(label(_("Links"), "section"), 1)
        links_head.addWidget(link_button(_("Add link…"), self.addLinkRequested.emit))
        layout.addLayout(links_head)
        self.outgoing = self._list(_("Outgoing links"))
        layout.addWidget(self.outgoing)
        layout.addWidget(label(_("Backlinks"), "section"))
        self.incoming = self._list(_("Backlinks"))
        layout.addWidget(self.incoming)
        layout.addStretch(1)

    def _list(self, name: str) -> QListWidget:
        w = QListWidget()
        w.setAccessibleName(name)
        w.setIconSize(LIST_ICON)
        w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        w.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        w.customContextMenuRequested.connect(lambda pos, lw=w: self._link_menu(lw, pos))
        w.itemActivated.connect(
            lambda item: self.openNote.emit(item.data(Qt.ItemDataRole.UserRole)[1])
        )
        w.itemClicked.connect(
            lambda item: self.openNote.emit(item.data(Qt.ItemDataRole.UserRole)[1])
        )
        return w

    def set_link_types(self, types: list[LinkType]) -> None:
        self.link_types = types

    def set_busy(self, busy: bool) -> None:
        if busy:
            self.status.setText(_("Analysing…"))

    def set_suggestions(self, items: list[Suggestion], empty_text: str = "") -> None:
        while self.suggestions.count():
            w = self.suggestions.takeAt(0).widget()
            if w:
                w.deleteLater()
        for s in items:
            self.suggestions.addWidget(_SuggestionRow(s, self))
        self.status.setText("" if items else empty_text)

    def set_links(
        self, note_id: str, outgoing: list[tuple[Link, str]], incoming: list[tuple[Link, str]]
    ) -> None:
        types = {lt.id: (i, lt) for i, lt in enumerate(self.link_types)}
        for widget, rows, out in (
            (self.outgoing, outgoing, True),
            (self.incoming, incoming, False),
        ):
            widget.clear()
            for link, title in sorted(
                rows, key=lambda r: (types.get(r[0].type, (99,))[0], r[1].casefold())
            ):
                lt = types.get(link.type, (0, None))[1]
                verb = lt.label_for(out) if lt else link.type
                item = QListWidgetItem(f"{title or 'Untitled'}\n{verb}")
                if lt:
                    item.setIcon(type_icon(lt))
                other = link.dst if out else link.src
                item.setData(Qt.ItemDataRole.UserRole, (link, other))
                item.setToolTip(
                    f"{verb} “{title}”"
                    + ("  " + _("(from a [[link]] in the text)") if link.origin == "inline" else "")
                )
                widget.addItem(item)
            if not rows:
                placeholder = QListWidgetItem(
                    _("No links yet") if out else _("No notes link here yet")
                )
                placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
                widget.addItem(placeholder)
            height = sum(widget.sizeHintForRow(i) for i in range(widget.count())) + 6
            widget.setFixedHeight(min(max(height, 30), 420))

    def _link_menu(self, widget: QListWidget, pos) -> None:
        item = widget.itemAt(pos)
        data = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not data:
            return
        link, other = data
        menu = QMenu(self)
        menu.addAction(icons.icon("open"), _("Open note"), lambda: self.openNote.emit(other))
        change = menu.addMenu(_("Change link type"))
        for lt in self.link_types:
            action = QAction(type_icon(lt, MENU_ICON), lt.label, change)
            action.setCheckable(True)
            action.setChecked(lt.id == link.type)
            action.triggered.connect(
                lambda _unused=False, t=lt.id: self.changeLinkType.emit(
                    link.src, link.dst, link.type, t
                )
            )
            change.addAction(action)
        lt = next((t for t in self.link_types if t.id == link.type), None)
        if lt is not None and lt.directed and link.origin != "inline":
            menu.addAction(
                icons.icon("sync"),
                _("Reverse direction"),
                lambda: self.reverseLink.emit(link.src, link.dst, link.type),
            )
        if link.origin == "inline":
            menu.addAction(_("Remove (edit the [[link]] in the text)")).setEnabled(False)
        else:
            menu.addAction(
                icons.icon("delete"),
                _("Remove link"),
                lambda: self.removeLink.emit(link.src, link.dst, link.type),
            )
        menu.exec(widget.mapToGlobal(pos))
