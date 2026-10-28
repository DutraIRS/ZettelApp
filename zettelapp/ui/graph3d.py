"""3D knowledge graph rendered with QPainter: orbit, zoom, depth cues and group halos."""

from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetricsF, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from zettelapp.ui import theme
from zettelapp.ui.graph2d import node_radius
from zettelapp.ui.graph_common import GraphData
from zettelapp.ui.side_panel import type_dash


class Graph3DView(QWidget):
    nodeActivated = Signal(str)
    nodeSelected = Signal(str)
    nodeMenu = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAccessibleName("Knowledge graph in 3D")
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.data = GraphData([], {}, [], {})
        self.points = np.zeros((0, 3))
        self.yaw, self.pitch, self.zoom_level = 0.6, -0.35, 1.0
        self.show_groups = True
        self.show_labels = True
        self.hovered: str | None = None
        self.selected: str | None = None
        self._screen = np.zeros((0, 2))
        self._scale = np.zeros(0)
        self._drag_from: QPointF | None = None
        self._dragged = False
        self._neighbors: dict[str, set[str]] = {}
        self.rotate_timer = QTimer(self, interval=33, timeout=self._spin)

    def set_graph(self, data: GraphData, positions: dict[str, tuple[float, ...]], show_groups: bool,
                  show_labels: bool) -> None:
        self.data = data
        self.show_groups = show_groups
        self.show_labels = show_labels
        pts = np.array([positions.get(i, (0.0, 0.0, 0.0))[:3] for i in data.ids], dtype=float).reshape(-1, 3)
        if len(pts):
            pts -= pts.mean(axis=0)
            radius = np.linalg.norm(pts, axis=1).max()
            pts /= radius if radius > 0 else 1.0
        self.points = pts
        self._index = {node: i for i, node in enumerate(data.ids)}
        self._neighbors = {}
        for l in data.links:
            self._neighbors.setdefault(l.src, set()).add(l.dst)
            self._neighbors.setdefault(l.dst, set()).add(l.src)
        self.update()

    def set_auto_rotate(self, on: bool) -> None:
        if on:
            self.rotate_timer.start()
        else:
            self.rotate_timer.stop()

    def _spin(self) -> None:
        self.yaw += 0.008
        self.update()

    def fit(self) -> None:
        self.zoom_level = 1.0
        self.update()

    def zoom(self, factor: float) -> None:
        self.zoom_level = float(np.clip(self.zoom_level * factor, 0.3, 8.0))
        self.update()

    def focus_node(self, note_id: str) -> None:
        self.selected = note_id
        i = self._index.get(note_id)
        if i is not None:  # turn the camera so the node faces the viewer
            x, y, z = self.points[i]
            self.yaw = -math.atan2(x, z) if (x or z) else self.yaw
            self.pitch = math.atan2(y, math.hypot(x, z))
        self.update()

    # --- projection -----------------------------------------------------------

    def _project(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        rot_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        rot_x = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
        q = self.points @ (rot_x @ rot_y).T
        camera = 3.2
        f = min(self.width(), self.height()) * 0.36 * self.zoom_level
        scale = f * camera / (camera - q[:, 2])
        screen = np.column_stack([self.width() / 2 + q[:, 0] * scale, self.height() / 2 - q[:, 1] * scale])
        depth = (q[:, 2] + 1) / 2  # 0 = far, 1 = near
        return screen, scale, np.clip(depth, 0, 1)

    def paintEvent(self, event) -> None:  # noqa: N802
        t = theme.current()
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        painter.fillRect(self.rect(), t.q("surface"))
        if not len(self.points):
            painter.setPen(t.q("text_muted"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No notes to show")
            return
        screen, scale, depth = self._project()
        self._screen, self._scale = screen, scale
        base = min(self.width(), self.height()) * 0.36 * self.zoom_level

        if self.show_groups:  # soft halos behind each group
            for group, members in self.data.members().items():
                idx = [self._index[m] for m in members if m in self._index]
                if not idx:
                    continue
                centre = screen[idx].mean(axis=0)
                spread = float(np.sqrt(((screen[idx] - centre) ** 2).sum(axis=1).mean())) + base * 0.06
                color = QColor(self.data.group_color(group))
                gradient = QRadialGradient(QPointF(*centre), spread * 1.25)
                inner, outer = QColor(color), QColor(color)
                inner.setAlphaF(0.13)
                outer.setAlphaF(0.0)
                gradient.setColorAt(0, inner)
                gradient.setColorAt(1, outer)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(gradient)
                painter.drawEllipse(QPointF(*centre), spread * 1.25, spread * 1.25)

        focus = self.hovered or self.selected
        neighbors = self._neighbors.get(focus, set()) if focus else set()
        edges = []
        for link in self.data.links:
            a, b = self._index.get(link.src), self._index.get(link.dst)
            if a is not None and b is not None:
                edges.append(((depth[a] + depth[b]) / 2, a, b, link))
        edges.sort(key=lambda e: e[0])
        for d, a, b, link in edges:
            highlighted = focus is not None and focus in (link.src, link.dst)
            color = QColor(t.q("accent") if highlighted else self.data.link_color(link))
            color.setAlphaF(0.9 if highlighted else 0.12 + 0.45 * d)
            entry = self.data.types.get(link.type)
            painter.setPen(QPen(color, 2.0 if highlighted else 1.0 + d, type_dash(entry[0] if entry else 0)))
            painter.drawLine(QPointF(*screen[a]), QPointF(*screen[b]))

        order = np.argsort(depth)
        by_degree = sorted(self.data.ids, key=lambda i: -self.data.degree.get(i, 0))
        labelled = set(by_degree[:25]) if len(self.data.ids) > 60 else set(self.data.ids)
        font = theme.ui_font(8.5)
        metrics = QFontMetricsF(font)
        painter.setFont(font)
        for i in order:
            node = self.data.ids[i]
            d = depth[i]
            r = node_radius(self.data.degree.get(node, 0)) * (0.55 + 0.6 * d) * min(1.6, self.zoom_level ** 0.5)
            color = QColor(self.data.group_color(self.data.group_of.get(node)))
            dim = focus is not None and node != focus and node not in neighbors
            color.setAlphaF((0.35 + 0.65 * d) * (0.3 if dim else 1.0))
            painter.setPen(QPen(t.q("surface"), 1.5))
            painter.setBrush(color)
            p = QPointF(*screen[i])
            painter.drawEllipse(p, r, r)
            if node in (self.selected, self.data.focus):
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(t.q("text"), 1.8))
                painter.drawEllipse(p, r + 4, r + 4)
            if node in (focus,) or node in neighbors or (self.show_labels and node in labelled and d > 0.45):
                painter.setPen(t.q("text") if node == focus else t.q("text_secondary"))
                text = metrics.elidedText(self.data.titles.get(node) or "Untitled", Qt.TextElideMode.ElideRight, 150)
                painter.drawText(QRectF(p.x() - 80, p.y() + r + 2, 160, metrics.height()),
                                 Qt.AlignmentFlag.AlignHCenter, text)
        painter.setPen(t.q("text_muted"))
        painter.drawText(QRectF(10, self.height() - 24, self.width() - 20, 18), Qt.AlignmentFlag.AlignLeft,
                         "Drag to orbit · wheel to zoom · double-click a note to open it")

    # --- interaction ----------------------------------------------------------

    def _node_at(self, pos: QPointF) -> str | None:
        if not len(self._screen):
            return None
        d = np.hypot(self._screen[:, 0] - pos.x(), self._screen[:, 1] - pos.y())
        i = int(np.argmin(d))
        return self.data.ids[i] if d[i] <= 14 + 6 * self.zoom_level ** 0.5 else None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._drag_from = event.position()
        self._dragged = False

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_from is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.position() - self._drag_from
            if abs(delta.x()) + abs(delta.y()) > 2:
                self._dragged = True
            self.yaw += delta.x() * 0.01
            self.pitch = float(np.clip(self.pitch + delta.y() * 0.01, -1.5, 1.5))
            self._drag_from = event.position()
            self.update()
            return
        node = self._node_at(event.position())
        if node != self.hovered:
            self.hovered = node
            self.setToolTip(self.data.titles.get(node, "") if node else "")
            self.setCursor(Qt.CursorShape.PointingHandCursor if node else Qt.CursorShape.OpenHandCursor)
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if not self._dragged and event.button() == Qt.MouseButton.LeftButton:
            node = self._node_at(event.position())
            self.selected = node
            if node:
                self.nodeSelected.emit(node)
            self.update()
        self._drag_from = None

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        node = self._node_at(event.position())
        if node:
            self.nodeActivated.emit(node)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        node = self._node_at(QPointF(event.pos()))
        if node:
            self.nodeMenu.emit(node, event.globalPos())

    def wheelEvent(self, event) -> None:  # noqa: N802
        self.zoom(1.12 if event.angleDelta().y() > 0 else 1 / 1.12)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.hovered = None
        self.update()

    def render_image(self):
        return self.grab().toImage()
