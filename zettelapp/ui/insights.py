"""Insights: statistics and charts about the vault, drawn with QPainter.

Chart conventions: thin bars (<= 24 px) with 4 px rounded data ends and a
square baseline, hairline grids, direct labels at bar tips, text in text
colours (never the series colour), hover tooltips, and a table view for
every chart.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import date, datetime

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFontMetricsF, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from zettelapp.core.cluster import cluster_notes
from zettelapp.i18n import _, n_
from zettelapp.ui import theme
from zettelapp.ui.widgets import Card, label, tool_button
from zettelapp.ui.workers import run_task

BAR = 18.0  # bar thickness (capped below 24 px)


def _ticks(value: float) -> tuple[float, float]:
    """A clean axis maximum and tick step for counts (e.g. 45 -> (60, 20))."""
    raw = max(1.0, value / 4)
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 5, 10) if raw <= m * magnitude)
    return math.ceil(max(value, 1) / step) * step, step


def _compact(n: float) -> str:
    return f"{n / 1000:.1f}K" if n >= 1000 else f"{n:g}"


def _rounded_bar(rect: QRectF, horizontal: bool, radius: float = 4.0) -> QPainterPath:
    """A bar with a rounded data end and a square baseline."""
    path = QPainterPath()
    r = min(
        radius,
        (rect.height() if horizontal else rect.width()) / 2,
        (rect.width() if horizontal else rect.height()),
    )
    if horizontal:
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right() - r, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + r)
        path.lineTo(rect.right(), rect.bottom() - r)
        path.quadTo(rect.right(), rect.bottom(), rect.right() - r, rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
    else:
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + r)
        path.quadTo(rect.left(), rect.top(), rect.left() + r, rect.top())
        path.lineTo(rect.right() - r, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + r)
        path.lineTo(rect.right(), rect.bottom())
    path.closeSubpath()
    return path


def _counted(unit: str, value: float) -> str:
    """ "5 notes" / "1 link" in the interface language."""
    shown = _compact(value)
    if unit == "notes":
        return n_("{n} note", "{n} notes", int(value)).format(n=shown)
    if unit == "links":
        return n_("{n} link", "{n} links", int(value)).format(n=shown)
    return shown


class BarChart(QWidget):
    """Horizontal bars; each row is (label, value, colour or None, payload)."""

    rowClicked = Signal(object)

    def __init__(self, unit: str = ""):
        super().__init__()
        self.rows: list[tuple[str, float, QColor | None, object]] = []
        self.unit = unit
        self.setMouseTracking(True)
        self.setMinimumHeight(60)

    def set_rows(self, rows) -> None:
        self.rows = rows
        self.setMinimumHeight(int(len(rows) * (BAR + 12) + 16))
        self.update()

    def _geometry(self):
        metrics = QFontMetricsF(theme.ui_font(9))
        label_w = min(
            self.width() * 0.42,
            max((metrics.horizontalAdvance(r[0]) for r in self.rows), default=0) + 8,
        )
        value_w = metrics.horizontalAdvance("00000") + 8
        left = label_w + 8
        width = max(10.0, self.width() - left - value_w)
        return metrics, label_w, left, width

    def paintEvent(self, event) -> None:  # noqa: N802
        t = theme.current()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.rows:
            painter.setPen(t.q("text_muted"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _("Nothing to show yet"))
            return
        metrics, label_w, left, width = self._geometry()
        top_value = max(max(r[1] for r in self.rows), 1)
        painter.setFont(theme.ui_font(9))
        painter.setPen(QPen(t.q("axis"), 1))
        painter.drawLine(QPointF(left, 4), QPointF(left, len(self.rows) * (BAR + 12) + 4))
        for i, (text, value, color, _unused) in enumerate(self.rows):
            y = 8 + i * (BAR + 12)
            painter.setPen(t.q("text_secondary"))
            painter.drawText(
                QRectF(0, y, label_w, BAR),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                metrics.elidedText(text, Qt.TextElideMode.ElideRight, label_w),
            )
            w = width * value / top_value
            painter.fillPath(
                _rounded_bar(QRectF(left, y, max(w, 2), BAR), True), color or t.category(0)
            )
            painter.setPen(t.q("text"))
            painter.drawText(
                QRectF(left + w + 6, y, 80, BAR),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                _compact(value),
            )

    def _row_at(self, pos: QPointF) -> int | None:
        i = int((pos.y() - 8) // (BAR + 12))
        return i if 0 <= i < len(self.rows) else None

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        i = self._row_at(event.position())
        if i is None:
            QToolTip.hideText()
            return
        text, value, _unused, payload = self.rows[i]
        QToolTip.showText(
            event.globalPosition().toPoint(), f"{text}: {_counted(self.unit, value)}", self
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor if payload else Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        i = self._row_at(event.position())
        if i is not None and self.rows[i][3]:
            self.rowClicked.emit(self.rows[i][3])


class ColumnChart(QWidget):
    """Vertical columns over time (single series)."""

    def __init__(self):
        super().__init__()
        self.rows: list[tuple[str, float]] = []
        self.setMouseTracking(True)
        self.setMinimumHeight(200)

    def set_rows(self, rows: list[tuple[str, float]]) -> None:
        self.rows = rows
        self.update()

    def _plot(self) -> QRectF:
        return QRectF(36, 10, max(10, self.width() - 46), max(10, self.height() - 34))

    def paintEvent(self, event) -> None:  # noqa: N802
        t = theme.current()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        plot = self._plot()
        if not self.rows:
            return
        top_value, step = _ticks(max(v for _unused, v in self.rows))
        painter.setFont(theme.ui_font(8.5))
        for k in range(int(round(top_value / step)) + 1):  # hairline grid with clean ticks
            v = step * k
            y = plot.bottom() - plot.height() * v / top_value
            painter.setPen(QPen(t.q("grid" if k else "axis"), 1))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(t.q("text_muted"))
            painter.drawText(
                QRectF(0, y - 8, plot.left() - 6, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                _compact(v),
            )
        slot = plot.width() / len(self.rows)
        width = min(24.0, slot * 0.6)
        step = max(1, int(len(self.rows) / max(1, plot.width() / 56)))
        for i, (name, value) in enumerate(self.rows):
            x = plot.left() + slot * i + (slot - width) / 2
            h = plot.height() * value / top_value
            if value:
                painter.fillPath(
                    _rounded_bar(QRectF(x, plot.bottom() - h, width, h), False), t.category(0)
                )
            if i % step == 0:
                painter.setPen(t.q("text_muted"))
                painter.drawText(
                    QRectF(x - 20, plot.bottom() + 4, width + 40, 16),
                    Qt.AlignmentFlag.AlignHCenter,
                    name,
                )
        _unused, last = self.rows[-1]  # label the most recent value only
        x = plot.left() + slot * (len(self.rows) - 1) + slot / 2
        painter.setPen(t.q("text"))
        painter.drawText(
            QRectF(x - 30, plot.bottom() - plot.height() * last / top_value - 18, 60, 16),
            Qt.AlignmentFlag.AlignHCenter,
            _compact(last),
        )

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        plot = self._plot()
        if not self.rows or not plot.contains(event.position()):
            QToolTip.hideText()
            return
        i = min(
            len(self.rows) - 1,
            int((event.position().x() - plot.left()) / (plot.width() / len(self.rows))),
        )
        name, value = self.rows[i]
        QToolTip.showText(event.globalPosition().toPoint(), f"{name}: {int(value)} notes", self)


class ChartCard(Card):
    """A titled chart with a toggle to show the same data as a table."""

    def __init__(self, title: str, chart: QWidget, subtitle: str = ""):
        super().__init__()
        head = QHBoxLayout()
        head.addWidget(label(title, "section"), 1)
        self.toggle = tool_button("bullets", _("Show as table"), self._toggle, checkable=True)
        head.addWidget(self.toggle)
        self.body.addLayout(head)
        if subtitle:
            self.body.addWidget(label(subtitle, "caption", wrap=True))
        self.stack = QStackedWidget()
        self.chart = chart
        self.table = QTableWidget(0, 2)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.stack.addWidget(chart)
        self.stack.addWidget(self.table)
        self.body.addWidget(self.stack, 1)

    def set_table(self, headers: list[str], rows: list[tuple]) -> None:
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))
        self.table.resizeColumnToContents(0)

    def _toggle(self) -> None:
        self.stack.setCurrentIndex(1 if self.toggle.isChecked() else 0)


class StatTile(Card):
    def __init__(self, title: str):
        super().__init__(margins=14, spacing=2)
        self.value = label("–", "hero")
        self.caption = label(title, "secondary")
        self.body.addWidget(self.caption)
        self.body.addWidget(self.value)
        self.detail = label("", "caption")
        self.body.addWidget(self.detail)

    def set(self, value: str, detail: str = "") -> None:
        self.value.setText(value)
        self.detail.setText(detail)


class InsightsPage(QWidget):
    openNote = Signal(str)

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setObjectName("Page")
        self._request = 0
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)
        content = QWidget()
        content.setObjectName("Page")
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 18, 24, 24)
        layout.setSpacing(14)
        head = QHBoxLayout()
        head.addWidget(label(_("Insights"), "title"), 1)
        head.addWidget(tool_button("refresh", _("Refresh"), self.refresh, text=_("Refresh")))
        layout.addLayout(head)
        tiles = QHBoxLayout()
        tiles.setSpacing(12)
        self.tiles = {
            key: StatTile(text)
            for key, text in (
                ("notes", _("Notes")),
                ("links", _("Links")),
                ("tags", _("Tags")),
                ("orphans", _("Unlinked notes")),
                ("cards", _("Flashcards")),
                ("due", _("Due for review")),
            )
        }
        for tile in self.tiles.values():
            tiles.addWidget(tile)
        layout.addLayout(tiles)
        grid = QGridLayout()
        grid.setSpacing(12)
        self.timeline = ColumnChart()
        self.timeline_card = ChartCard(
            _("Notes added per month"), self.timeline, _("The last 12 months")
        )
        self.tags_chart = BarChart("notes")
        self.tags_card = ChartCard(_("Top tags"), self.tags_chart)
        self.types_chart = BarChart("links")
        self.types_card = ChartCard(_("Links by type"), self.types_chart)
        self.hubs_chart = BarChart("links")
        self.hubs_chart.rowClicked.connect(lambda note_id: self.openNote.emit(str(note_id)))
        self.hubs_card = ChartCard(
            _("Most connected notes"), self.hubs_chart, _("Click a bar to open the note")
        )
        self.clusters_chart = BarChart("notes")
        self.clusters_card = ChartCard(
            _("Topics (k-means clusters)"),
            self.clusters_chart,
            _("Notes grouped by meaning (LSA embeddings); k chosen by silhouette score"),
        )
        grid.addWidget(self.timeline_card, 0, 0, 1, 2)
        grid.addWidget(self.tags_card, 1, 0)
        grid.addWidget(self.types_card, 1, 1)
        grid.addWidget(self.hubs_card, 2, 0)
        grid.addWidget(self.clusters_card, 2, 1)
        layout.addLayout(grid)
        layout.addStretch(1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        self._request += 1
        request = self._request
        vault = self.window.vault
        if vault is None:
            return
        t = theme.current()
        notes = vault.all_notes()
        links = vault.all_links()
        degree: Counter[str] = Counter()
        for l in links:
            degree[l.src] += 1
            degree[l.dst] += 1
        tags = vault.all_tags()
        cards = vault.cards_for_notes()
        due = vault.due_cards()
        orphans = [n for n in notes if not degree.get(n.id)]
        self.tiles["notes"].set(
            f"{len(notes):,}", _("{n} in Trash").format(n=vault.count_notes(deleted=True))
        )
        self.tiles["links"].set(
            f"{len(links):,}",
            _("{n} per note").format(n=f"{2 * len(links) / len(notes):.1f}") if notes else "",
        )
        self.tiles["tags"].set(f"{len(tags):,}")
        self.tiles["orphans"].set(
            f"{len(orphans):,}",
            _("Link them to grow your network") if orphans else _("Every note is linked"),
        )
        self.tiles["cards"].set(f"{len(cards):,}")
        self.tiles["due"].set(f"{len(due):,}", _("cards today"))

        today = date.today()
        months = []
        y, m = today.year, today.month
        for _unused in range(12):
            months.append((y, m))
            y, m = (y, m - 1) if m > 1 else (y - 1, 12)
        months.reverse()
        per_month: Counter[tuple[int, int]] = Counter()
        for n in notes:
            try:
                when = datetime.fromisoformat(n.created).astimezone()
            except ValueError:
                continue
            per_month[(when.year, when.month)] += 1
        rows = [(date(yy, mm, 1).strftime("%b"), per_month[(yy, mm)]) for yy, mm in months]
        self.timeline.set_rows(rows)
        self.timeline_card.set_table(
            ["Month", "Notes"],
            [(date(yy, mm, 1).strftime("%B %Y"), per_month[(yy, mm)]) for yy, mm in months],
        )

        top_tags = sorted(tags, key=lambda x: -x[1])[:10]
        self.tags_chart.set_rows([(f"#{name}", n, None, None) for name, n in top_tags])
        self.tags_card.set_table([_("Tag"), _("Notes")], [(f"#{name}", n) for name, n in top_tags])

        types = vault.link_type_map()
        by_type = Counter(l.type for l in links)
        self.types_chart.set_rows(
            [
                (
                    types[k].label if k in types else k,
                    v,
                    t.entity(types[k].color) if k in types else None,
                    None,
                )
                for k, v in by_type.most_common()
            ]
        )
        self.types_card.set_table(
            [_("Link type"), _("Links")],
            [(types[k].label if k in types else k, v) for k, v in by_type.most_common()],
        )

        titles = {n.id: n.display_title for n in notes}
        hubs = degree.most_common(10)
        self.hubs_chart.set_rows([(titles.get(i, i), d, None, i) for i, d in hubs])
        self.hubs_card.set_table([_("Note"), _("Links")], [(titles.get(i, i), d) for i, d in hubs])

        def done(result) -> None:
            if request != self._request:
                return
            if result is None:
                self.clusters_chart.set_rows([])
                return
            sizes = Counter(result.labels.tolist())
            rows = [
                (
                    f"{c + 1}: " + ", ".join(result.keywords.get(c, [])[:3]),
                    sizes[c],
                    t.category(c) if c < 8 else None,
                    None,
                )
                for c in sorted(sizes)
            ]
            self.clusters_chart.set_rows(rows)
            self.clusters_card.set_table([_("Cluster"), _("Notes")], [(r[0], r[1]) for r in rows])

        run_task(cluster_notes, notes, "kmeans", None, on_done=done)
