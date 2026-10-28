"""Mind map editor attached to a note."""

from __future__ import annotations

import copy

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFontMetricsF, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QLineEdit,
    QMenu,
)

from zettelapp.core.models import (
    MAX_MINDMAP_DEPTH,
    MAX_MINDMAP_NODES,
    mindmap_nodes,
    new_mindmap_node,
)
from zettelapp.ui import icons, theme

H_GAP = 56
V_GAP = 12
PAD_X, PAD_Y = 14, 8


def _find(root: dict, node_id: str) -> tuple[dict | None, dict | None]:
    """(node, parent) for *node_id*."""
    stack = [(root, None)]
    while stack:
        node, parent = stack.pop()
        if node["id"] == node_id:
            return node, parent
        stack.extend((c, node) for c in node.get("children", []))
    return None, None


class _NodeItem(QGraphicsItem):
    def __init__(self, view: MindMapView, node: dict, depth: int, branch: int, rect: QRectF):
        super().__init__()
        self.view, self.node, self.depth, self.branch, self.rect = view, node, depth, branch, rect
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(
            "Linked note: double-click the link icon area or use the context menu to open it"
            if node.get("note")
            else ""
        )

    def boundingRect(self) -> QRectF:  # noqa: N802
        return self.rect.adjusted(-3, -3, 3, 3)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        t = theme.current()
        color = t.q("accent") if self.depth == 0 else t.category(self.branch % len(t.categorical))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = self.node["id"] == self.view.selected_id
        if self.depth == 0:
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            text_color = t.q("on_accent")
        else:
            fill = QColor(color)
            fill.setAlpha(40 if self.depth == 1 else 0)
            base = t.q("surface")
            painter.setBrush(fill if self.depth == 1 else base)
            painter.setPen(QPen(color, 2 if self.depth == 1 else 1.4))
            text_color = t.q("text")
        painter.drawRoundedRect(self.rect, 8, 8)
        if selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(t.q("text"), 1.5, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self.rect.adjusted(-3, -3, 3, 3), 10, 10)
        painter.setPen(text_color)
        font = self.view.node_font(self.depth)
        painter.setFont(font)
        text_rect = self.rect.adjusted(PAD_X, 0, -PAD_X, 0)
        if self.node.get("note"):
            text_rect.setRight(text_rect.right() - 18)
            painter.setFont(icons.glyph_font(12))
            painter.drawText(
                QRectF(text_rect.right() + 4, self.rect.top(), 16, self.rect.height()),
                Qt.AlignmentFlag.AlignCenter,
                icons.glyph("link"),
            )
            painter.setFont(font)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.node.get("text") or "…",
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.view.select(self.node["id"])
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self.view.edit(self.node["id"])


class MindMapView(QGraphicsView):
    changed = Signal(object)  # the mind map dict, or None when cleared
    openNote = Signal(str)
    linkNoteRequested = Signal(str)  # mind map node id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setAccessibleName("Mind map")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.root: dict | None = None
        self.selected_id: str | None = None
        self.items: dict[str, _NodeItem] = {}
        self._editor: QLineEdit | None = None

    # --- data ---------------------------------------------------------------

    def set_mindmap(self, root: dict | None) -> None:
        self.root = copy.deepcopy(root) if root else None
        self.selected_id = self.root["id"] if self.root else None
        self.rebuild()
        self.fit()

    def ensure_root(self, title: str) -> None:
        if self.root is None:
            self.root = new_mindmap_node(title or "Central idea")
            self.selected_id = self.root["id"]
            self._emit()

    def _emit(self) -> None:
        self.rebuild()
        self.changed.emit(copy.deepcopy(self.root) if self.root else None)

    def node_font(self, depth: int):
        size = 12.5 if depth == 0 else 10.5 if depth == 1 else 9.5
        weight = theme.QFont.Weight.DemiBold if depth <= 1 else theme.QFont.Weight.Normal
        return theme.ui_font(size, weight)

    # --- layout -------------------------------------------------------------

    def rebuild(self) -> None:
        scene = self.scene()
        scene.clear()
        self.items.clear()
        t = theme.current()
        self.setBackgroundBrush(t.q("surface"))
        if self.root is None:
            text = scene.addText("No mind map yet. Click “Add mind map” or press Tab to start one.")
            text.setDefaultTextColor(t.q("text_muted"))
            text.setFont(theme.ui_font(10))
            return
        sizes: dict[str, QRectF] = {}
        col_width: dict[int, float] = {}
        for node, depth in mindmap_nodes(self.root):
            metrics = QFontMetricsF(self.node_font(depth))
            w = (
                min(260.0, metrics.horizontalAdvance(node.get("text") or "…"))
                + 2 * PAD_X
                + (18 if node.get("note") else 0)
            )
            h = metrics.height() + 2 * PAD_Y
            sizes[node["id"]] = QRectF(0, 0, w, h)
            col_width[depth] = max(col_width.get(depth, 0), w)
        col_x = {0: 0.0}
        for depth in sorted(col_width)[1:]:
            col_x[depth] = col_x[depth - 1] + col_width[depth - 1] + H_GAP

        positions: dict[str, QPointF] = {}
        cursor = [0.0]

        def place(node: dict, depth: int) -> tuple[float, float]:
            children = node.get("children", [])
            rect = sizes[node["id"]]
            if not children:
                top = cursor[0]
                cursor[0] += rect.height() + V_GAP
                positions[node["id"]] = QPointF(col_x[depth], top)
                return top, top + rect.height()
            spans = [place(c, depth + 1) for c in children]
            mid = (spans[0][0] + spans[-1][1]) / 2
            top = mid - rect.height() / 2
            positions[node["id"]] = QPointF(col_x[depth], top)
            return min(top, spans[0][0]), max(top + rect.height(), spans[-1][1])

        place(self.root, 0)
        branch_of: dict[str, int] = {}
        for i, child in enumerate(self.root.get("children", [])):
            for node, _ in mindmap_nodes(child):
                branch_of[node["id"]] = i

        def draw(node: dict, depth: int) -> None:
            rect = sizes[node["id"]].translated(positions[node["id"]])
            for child in node.get("children", []):
                crect = sizes[child["id"]].translated(positions[child["id"]])
                start = QPointF(rect.right(), rect.center().y())
                end = QPointF(crect.left(), crect.center().y())
                path = QPainterPath(start)
                dx = (end.x() - start.x()) * 0.5
                path.cubicTo(start + QPointF(dx, 0), end - QPointF(dx, 0), end)
                edge = QGraphicsPathItem(path)
                color = t.category(branch_of.get(child["id"], 0) % len(t.categorical))
                edge.setPen(
                    QPen(
                        color,
                        2.2 if depth == 0 else 1.6,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap,
                    )
                )
                edge.setZValue(-1)
                scene.addItem(edge)
                draw(child, depth + 1)
            item = _NodeItem(self, node, depth, branch_of.get(node["id"], 0), rect)
            scene.addItem(item)
            self.items[node["id"]] = item

        draw(self.root, 0)
        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))

    def fit(self) -> None:
        rect = self.scene().itemsBoundingRect()
        if rect.isEmpty():
            return
        self.fitInView(rect.adjusted(-30, -30, 30, 30), Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 1.2:
            self.resetTransform()
            self.centerOn(rect.center())

    # --- editing ------------------------------------------------------------

    def select(self, node_id: str | None) -> None:
        self.selected_id = node_id
        self.scene().update()

    def _count(self) -> int:
        return sum(1 for _ in mindmap_nodes(self.root)) if self.root else 0

    def add_child(self) -> None:
        if self.root is None:
            self.ensure_root("Central idea")
            return
        if self._count() >= MAX_MINDMAP_NODES:
            return
        node, _ = _find(self.root, self.selected_id or self.root["id"])
        node = node or self.root
        depth = next(depth for candidate, depth in mindmap_nodes(self.root) if candidate is node)
        if depth >= MAX_MINDMAP_DEPTH:
            return
        child = new_mindmap_node("New idea")
        node.setdefault("children", []).append(child)
        self.selected_id = child["id"]
        self._emit()
        self.edit(child["id"])

    def add_sibling(self) -> None:
        if self.root is None or self.selected_id in (None, self.root["id"]):
            self.add_child()
            return
        if self._count() >= MAX_MINDMAP_NODES:
            return
        node, parent = _find(self.root, self.selected_id)
        if parent is None:
            return
        sibling = new_mindmap_node("New idea")
        parent["children"].insert(parent["children"].index(node) + 1, sibling)
        self.selected_id = sibling["id"]
        self._emit()
        self.edit(sibling["id"])

    def delete_selected(self) -> None:
        if self.root is None or self.selected_id is None:
            return
        if self.selected_id == self.root["id"]:
            self.root = None
            self.selected_id = None
            self._emit()
            return
        node, parent = _find(self.root, self.selected_id)
        if parent is not None:
            index = parent["children"].index(node)
            parent["children"].remove(node)
            siblings = parent["children"]
            self.selected_id = (
                siblings[min(index, len(siblings) - 1)]["id"] if siblings else parent["id"]
            )
            self._emit()

    def edit(self, node_id: str) -> None:
        item = self.items.get(node_id)
        if item is None:
            return
        self.select(node_id)
        self.ensureVisible(item.rect)
        rect = self.mapFromScene(item.rect).boundingRect()
        editor = QLineEdit(self.viewport())
        editor.setText(item.node.get("text", ""))
        editor.selectAll()
        editor.setGeometry(rect.adjusted(2, 2, -2, -2).united(rect.adjusted(0, 0, 120, 0)))
        editor.setStyleSheet("QLineEdit { padding: 2px 6px; }")
        editor.show()
        editor.setFocus()
        self._editor = editor

        def commit() -> None:
            if self._editor is not editor:
                return
            self._editor = None
            item.node["text"] = editor.text().strip()[:500]
            editor.deleteLater()
            self._emit()
            self.setFocus()

        editor.editingFinished.connect(commit)

    def set_node_note(self, node_id: str, note_id: str | None, title: str | None = None) -> None:
        if self.root is None:
            return
        node, _ = _find(self.root, node_id)
        if node is None:
            return
        if note_id:
            node["note"] = note_id
            if title and (not node.get("text") or node.get("text") == "New idea"):
                node["text"] = title
        else:
            node.pop("note", None)
        self._emit()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_Tab:
            self.add_child()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.add_sibling()
        elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
        elif key == Qt.Key.Key_F2 and self.selected_id:
            self.edit(self.selected_id)
        elif (
            key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down) and self.root
        ):
            self._navigate(key)
        else:
            super().keyPressEvent(event)

    def focusNextPrevChild(self, forward: bool) -> bool:  # noqa: N802 - keep Tab for "add child"
        return False

    def _navigate(self, key) -> None:
        node, parent = _find(self.root, self.selected_id or self.root["id"])
        if node is None:
            return
        if key == Qt.Key.Key_Left and parent:
            self.select(parent["id"])
        elif key == Qt.Key.Key_Right and node.get("children"):
            self.select(node["children"][0]["id"])
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_Down) and parent:
            siblings = parent["children"]
            i = siblings.index(node) + (-1 if key == Qt.Key.Key_Up else 1)
            if 0 <= i < len(siblings):
                self.select(siblings[i]["id"])

    def wheelEvent(self, event) -> None:  # noqa: N802
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        item = self.itemAt(event.pos())
        while item is not None and not isinstance(item, _NodeItem):
            item = item.parentItem()
        menu = QMenu(self)
        if isinstance(item, _NodeItem):
            self.select(item.node["id"])
            menu.addAction(icons.icon("add"), "Add child\tTab", self.add_child)
            menu.addAction("Add sibling\tEnter", self.add_sibling)
            menu.addAction(icons.icon("edit"), "Rename\tF2", lambda: self.edit(item.node["id"]))
            menu.addSeparator()
            menu.addAction(
                icons.icon("link"),
                "Link to note…",
                lambda: self.linkNoteRequested.emit(item.node["id"]),
            )
            if item.node.get("note"):
                menu.addAction("Open linked note", lambda: self.openNote.emit(item.node["note"]))
                menu.addAction(
                    "Remove note link", lambda: self.set_node_note(item.node["id"], None)
                )
            menu.addSeparator()
            menu.addAction(icons.icon("delete"), "Delete\tDel", self.delete_selected)
        else:
            menu.addAction(icons.icon("add"), "Add idea", self.add_child)
            menu.addAction(icons.icon("fit"), "Fit to window", self.fit)
        menu.exec(event.globalPos())

    # --- export -------------------------------------------------------------

    def render_image(self, scale: float = 2.0) -> QImage:
        rect = self.scene().itemsBoundingRect().adjusted(-24, -24, 24, 24)
        image = QImage(
            int(rect.width() * scale), int(rect.height() * scale), QImage.Format.Format_ARGB32
        )
        image.fill(theme.current().q("surface"))
        painter = QPainter(image)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )
        self.scene().render(painter, QRectF(image.rect()), rect)
        painter.end()
        return image

    def render_svg(self, path: str) -> None:
        from PySide6.QtSvg import QSvgGenerator

        rect = self.scene().itemsBoundingRect().adjusted(-24, -24, 24, 24)
        generator = QSvgGenerator()
        generator.setFileName(path)
        generator.setSize(rect.size().toSize())
        generator.setViewBox(QRectF(0, 0, rect.width(), rect.height()))
        generator.setTitle("Mind map")
        painter = QPainter(generator)
        self.scene().render(painter, QRectF(0, 0, rect.width(), rect.height()), rect)
        painter.end()


def actions_for(view: MindMapView, parent) -> list[QAction]:
    return [
        QAction(icons.icon("add"), "Add child", parent, triggered=view.add_child),
        QAction("Add sibling", parent, triggered=view.add_sibling),
        QAction(icons.icon("delete"), "Delete", parent, triggered=view.delete_selected),
    ]
