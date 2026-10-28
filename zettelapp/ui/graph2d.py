"""2D knowledge graph: draggable nodes, typed edges and coloured group regions."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFontMetricsF, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsPathItem, QGraphicsScene, QGraphicsView

from zettelapp.ui import theme
from zettelapp.ui.graph_common import MAX_GROUP_COLORS, GraphData, padded_hull
from zettelapp.ui.side_panel import type_dash


def node_radius(degree: int) -> float:
    return 7.0 + min(16.0, math.sqrt(degree) * 3.2)


class NodeItem(QGraphicsObject):
    def __init__(self, view: Graph2DView, note_id: str):
        super().__init__()
        self.view = view
        self.note_id = note_id
        data = view.data
        self.radius = node_radius(data.degree.get(note_id, 0))
        self.color = data.group_color(data.group_of.get(note_id))
        self.title = data.titles.get(note_id) or "Untitled"
        self.pixmap: QPixmap | None = None
        if note_id in data.images:
            px = QPixmap(str(data.images[note_id]))
            if not px.isNull():
                size = int(self.radius * 4)
                self.pixmap = px.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                        Qt.TransformationMode.SmoothTransformation)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                      | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                      | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(self.title)
        self.setZValue(2)
        self.label_visible = True

    def boundingRect(self) -> QRectF:  # noqa: N802
        r = self.radius + 3
        return QRectF(-max(r, 80), -r, max(2 * r, 160), 2 * r + 22)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self.radius + 4, self.radius + 4)  # hit target larger than the mark
        return path

    def paint(self, painter: QPainter, option, widget=None) -> None:
        t = theme.current()
        view = self.view
        dimmed = view.hover_set is not None and self.note_id not in view.hover_set
        painter.setOpacity(0.25 if dimmed else 1.0)
        r = self.radius
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(t.q("surface"), 2))  # surface ring keeps overlapping marks legible
        painter.setBrush(self.color)
        painter.drawEllipse(QPointF(0, 0), r, r)
        if self.pixmap is not None:
            clip = QPainterPath()
            clip.addEllipse(QPointF(0, 0), r - 1.5, r - 1.5)
            painter.save()
            painter.setClipPath(clip)
            painter.drawPixmap(QRectF(-r, -r, 2 * r, 2 * r), self.pixmap, QRectF(self.pixmap.rect()))
            painter.restore()
        if self.note_id in (view.selected, view.data.focus):
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(t.q("text"), 2))
            painter.drawEllipse(QPointF(0, 0), r + 4, r + 4)
        if self.label_visible or self.note_id in (view.hovered, view.selected) or \
                (view.hover_set is not None and self.note_id in view.hover_set):
            painter.setFont(view.label_font)
            painter.setPen(t.q("text") if self.note_id in (view.hovered, view.selected) else t.q("text_secondary"))
            metrics = QFontMetricsF(view.label_font)
            text = metrics.elidedText(self.title, Qt.TextElideMode.ElideRight, 150)
            painter.drawText(QRectF(-80, r + 3, 160, metrics.height()), Qt.AlignmentFlag.AlignHCenter, text)

    def itemChange(self, change, value):  # noqa: N802
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.view.positions[self.note_id] = (self.pos().x(), self.pos().y())
            self.view.schedule_edges()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event) -> None:  # noqa: N802
        self.view.set_hover(self.note_id)

    def hoverLeaveEvent(self, event) -> None:  # noqa: N802
        self.view.set_hover(None)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.view.select(self.note_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self.view.nodeActivated.emit(self.note_id)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        self.view.nodeMenu.emit(self.note_id, event.screenPos())


class Graph2DView(QGraphicsView):
    nodeActivated = Signal(str)
    nodeSelected = Signal(str)
    nodeMenu = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setAccessibleName("Knowledge graph")
        self.data = GraphData([], {}, [], {})
        self.positions: dict[str, tuple[float, float]] = {}
        self.items: dict[str, NodeItem] = {}
        self.edge_items: list[QGraphicsPathItem] = []
        self.hull_items: list[QGraphicsItem] = []
        self.overlay: QGraphicsPathItem | None = None
        self.hovered: str | None = None
        self.selected: str | None = None
        self.hover_set: set[str] | None = None
        self.show_groups = True
        self.show_labels = True
        self.label_font = theme.ui_font(8.5)
        self._neighbors: dict[str, set[str]] = {}
        self._edge_timer = QTimer(self, singleShot=True, interval=16, timeout=self._rebuild_edges)

    def set_graph(self, data: GraphData, positions: dict[str, tuple[float, ...]], show_groups: bool,
                  show_labels: bool) -> None:
        self.data = data
        self.positions = {k: (v[0], v[1]) for k, v in positions.items() if k in set(data.ids)}
        self.show_groups = show_groups
        self.show_labels = show_labels
        self._neighbors = {}
        for l in data.links:
            self._neighbors.setdefault(l.src, set()).add(l.dst)
            self._neighbors.setdefault(l.dst, set()).add(l.src)
        scene = self.scene()
        scene.clear()
        self.items.clear()
        self.edge_items, self.hull_items, self.overlay = [], [], None
        t = theme.current()
        self.setBackgroundBrush(t.q("surface"))
        many = len(data.ids) > 150
        by_degree = sorted(data.ids, key=lambda i: -data.degree.get(i, 0))
        labelled = set(by_degree[:40]) if many else set(data.ids)
        for note_id in data.ids:
            item = NodeItem(self, note_id)
            item.label_visible = show_labels and note_id in labelled
            item.setPos(*self.positions.get(note_id, (0.0, 0.0)))
            scene.addItem(item)
            self.items[note_id] = item
        self._rebuild_edges()
        self.fit()

    def schedule_edges(self) -> None:
        self._edge_timer.start()

    def _rebuild_edges(self) -> None:
        scene = self.scene()
        for item in self.edge_items + self.hull_items:
            scene.removeItem(item)
        self.edge_items, self.hull_items = [], []
        t = theme.current()
        paths: dict[str, QPainterPath] = {}
        for link in self.data.links:
            if link.src not in self.positions or link.dst not in self.positions:
                continue
            a, b = QPointF(*self.positions[link.src]), QPointF(*self.positions[link.dst])
            path = paths.setdefault(link.type, QPainterPath())
            path.moveTo(a)
            path.lineTo(b)
            entry = self.data.types.get(link.type)
            if entry and entry[1].directed:
                self._arrow(path, a, b, node_radius(self.data.degree.get(link.dst, 0)))
        for type_id, path in paths.items():
            entry = self.data.types.get(type_id)
            color = QColor(t.entity(entry[1].color) if entry else t.q("text_muted"))
            color.setAlphaF(0.55)
            item = QGraphicsPathItem(path)
            item.setPen(QPen(color, 1.6, type_dash(entry[0] if entry else 0), Qt.PenCapStyle.RoundCap))
            item.setZValue(1)
            scene.addItem(item)
            self.edge_items.append(item)
        if self.show_groups:
            for group, members in self.data.members().items():
                pts = [self.positions[m] for m in members if m in self.positions]
                if not pts:
                    continue
                region = padded_hull(pts, 34.0)
                fill = QColor(self.data.group_color(group))
                fill.setAlphaF(0.10)  # a wash, never a saturated block
                stroke = QColor(self.data.group_color(group))
                stroke.setAlphaF(0.35)
                hull = QGraphicsPathItem(region)
                hull.setBrush(QBrush(fill))
                hull.setPen(QPen(stroke, 1))
                hull.setZValue(0)
                scene.addItem(hull)
                self.hull_items.append(hull)
                top = region.boundingRect()
                text = scene.addSimpleText(self.data.group_label(group), theme.ui_font(9, theme.QFont.Weight.DemiBold))
                text.setBrush(t.q("text_secondary"))
                text.setPos(top.center().x() - text.boundingRect().width() / 2, top.top() - 20)
                text.setZValue(0)
                self.hull_items.append(text)
        self._update_overlay()

    @staticmethod
    def _arrow(path: QPainterPath, a: QPointF, b: QPointF, r: float) -> None:
        dx, dy = b.x() - a.x(), b.y() - a.y()
        length = math.hypot(dx, dy)
        if length < r * 2 + 4:
            return
        ux, uy = dx / length, dy / length
        tip = QPointF(b.x() - ux * (r + 3), b.y() - uy * (r + 3))
        size = 7.0
        left = QPointF(tip.x() - ux * size - uy * size * 0.55, tip.y() - uy * size + ux * size * 0.55)
        right = QPointF(tip.x() - ux * size + uy * size * 0.55, tip.y() - uy * size - ux * size * 0.55)
        path.moveTo(left)
        path.lineTo(tip)
        path.lineTo(right)

    def set_hover(self, note_id: str | None) -> None:
        self.hovered = note_id
        self.hover_set = None if note_id is None else {note_id} | self._neighbors.get(note_id, set())
        self._update_overlay()
        self.scene().update()

    def _update_overlay(self) -> None:
        if self.overlay is not None:
            self.scene().removeItem(self.overlay)
            self.overlay = None
        focus = self.hovered or self.selected
        if focus is None or focus not in self.positions:
            return
        path = QPainterPath()
        for nb in self._neighbors.get(focus, ()):
            if nb in self.positions:
                path.moveTo(QPointF(*self.positions[focus]))
                path.lineTo(QPointF(*self.positions[nb]))
        self.overlay = QGraphicsPathItem(path)
        self.overlay.setPen(QPen(theme.current().q("accent"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        self.overlay.setZValue(1.5)
        self.scene().addItem(self.overlay)

    def select(self, note_id: str | None) -> None:
        self.selected = note_id
        self._update_overlay()
        self.scene().update()
        if note_id:
            self.nodeSelected.emit(note_id)

    def focus_node(self, note_id: str) -> None:
        item = self.items.get(note_id)
        if item:
            self.select(note_id)
            self.centerOn(item)

    def matching(self, query: str) -> list[str]:
        q = query.casefold().strip()
        return [i for i in self.data.ids if q and q in (self.data.titles.get(i) or "").casefold()]

    def fit(self) -> None:
        rect = self.scene().itemsBoundingRect()
        if rect.isEmpty():
            return
        self.fitInView(rect.adjusted(-40, -40, 40, 40), Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 1.6:
            self.resetTransform()
            self.scale(1.6, 1.6)
            self.centerOn(rect.center())

    def zoom(self, factor: float) -> None:
        self.scale(factor, factor)

    def wheelEvent(self, event) -> None:  # noqa: N802
        self.zoom(1.15 if event.angleDelta().y() > 0 else 1 / 1.15)

    def render_image(self, scale: float = 2.0):
        from PySide6.QtGui import QImage
        rect = self.scene().itemsBoundingRect().adjusted(-30, -30, 30, 30)
        image = QImage(int(rect.width() * scale), int(rect.height() * scale), QImage.Format.Format_ARGB32)
        image.fill(theme.current().q("surface"))
        painter = QPainter(image)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.scene().render(painter, QRectF(image.rect()), rect)
        painter.end()
        return image


__all__ = ["Graph2DView", "MAX_GROUP_COLORS", "node_radius"]
