"""Graph page: 2D/3D views, colouring by tag or cluster, grouping and legend."""

from __future__ import annotations

from collections import Counter

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QSpinBox,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from zettelapp.core.cluster import cluster_notes
from zettelapp.core.graph import force_layout, subgraph
from zettelapp.i18n import _, n_
from zettelapp.ui import icons, theme
from zettelapp.ui.graph2d import Graph2DView
from zettelapp.ui.graph3d import Graph3DView
from zettelapp.ui.graph_common import MAX_GROUP_COLORS, GraphData
from zettelapp.ui.link_style import LIST_ICON, MENU_ICON, type_icon
from zettelapp.ui.widgets import FlowLayout, SearchBox, label, tool_button
from zettelapp.ui.workers import run_task

# Layouts and clusterings kept for switching views quickly. Editing a note changes their keys
# (the vault's generation), so without a limit they would pile up for the whole session.
CACHE_SIZE = 8


def _remember(cache: dict, key: tuple, value) -> None:
    cache[key] = value
    while len(cache) > CACHE_SIZE:
        del cache[next(iter(cache))]  # the oldest


def _dot(color: QColor) -> QIcon:
    px = QPixmap(28, 28)
    px.setDevicePixelRatio(2)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(color)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 10, 10)
    p.end()
    return QIcon(px)


class GraphPage(QWidget):
    openNote = Signal(str)
    nodeMenuRequested = Signal(str, object)
    exportRequested = Signal(set)
    status = Signal(str)

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setObjectName("Page")
        self.focus_id: str | None = None
        self._layouts: dict[tuple, dict] = {}
        self._clusters: dict[tuple, object] = {}
        self._request = 0
        self.hidden_types: set[str] = set()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # The controls wrap onto a second line in a narrow window or a wordy language, rather
        # than making the whole main window that wide.
        bar = FlowLayout(spacing=14)

        def group(*widgets: QWidget) -> None:
            box = QWidget()
            row = QHBoxLayout(box)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            for widget in widgets:
                row.addWidget(widget)
            bar.addWidget(box)

        group(label(_("Graph"), "heading"))
        self.scope_group = QButtonGroup(self)
        for i, (text, tip) in enumerate(
            (
                (_("All notes"), _("Show the whole collection")),
                (_("Local"), _("Show the open note and its neighbourhood")),
            )
        ):
            b = QToolButton()
            b.setText(text)
            b.setToolTip(tip)
            b.setCheckable(True)
            self.scope_group.addButton(b, i)
        self.scope_group.button(0).setChecked(True)
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 5)
        self.depth_spin.setValue(2)
        self.depth_spin.setPrefix(_("Depth "))
        self.depth_spin.setToolTip(_("Links away from the open note"))
        group(*self.scope_group.buttons(), self.depth_spin)
        self.dim_group = QButtonGroup(self)
        for i, (text, tip) in enumerate((("2D", _("2D view")), ("3D", _("3D view")))):
            b = QToolButton()
            b.setText(text)
            b.setCheckable(True)
            b.setToolTip(tip)
            self.dim_group.addButton(b, i)
        self.dim_group.button(0).setChecked(True)
        group(*self.dim_group.buttons())
        self.color_by = QComboBox()
        self.color_by.setAccessibleName(_("Colour by"))
        self.color_by.addItem(icons.icon("tag"), _("Tags"), "tag")
        self.color_by.addItem(icons.icon("cluster"), _("Clusters: k-means"), "kmeans")
        self.color_by.addItem(icons.icon("cluster"), _("Clusters: hierarchical"), "hierarchical")
        self.color_by.addItem(_("Nothing"), "none")
        self.k = QSpinBox()
        self.k.setRange(0, 20)
        self.k.setSpecialValueText(_("Auto k"))
        self.k.setPrefix("k = ")
        self.k.setToolTip(_("Number of clusters. Auto picks k with the best silhouette score."))
        group(label(_("Colour by"), "secondary"), self.color_by, self.k)
        self.group_box = QCheckBox(_("Group"))
        self.group_box.setChecked(True)
        self.group_box.setToolTip(
            _("Pull notes of the same group together and shade each group's area")
        )
        self.labels_box = QCheckBox(_("Labels"))
        self.labels_box.setChecked(True)
        self.types_button = QToolButton()
        self.types_button.setIcon(icons.icon("filter"))
        self.types_button.setText(_("Link types"))
        self.types_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.types_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.types_menu = QMenu(self.types_button)
        self.types_button.setMenu(self.types_menu)
        group(self.group_box, self.labels_box, self.types_button)
        self.search = SearchBox(_("Find in graph"))
        self.search.setFixedWidth(200)
        self.search.returnPressed.connect(self._find)
        group(self.search)
        layout.addLayout(bar)

        body = QHBoxLayout()
        body.setSpacing(12)
        canvas = QWidget()
        canvas.setObjectName("Card")
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(1, 1, 1, 1)
        self.stack = QStackedWidget()
        self.view2d = Graph2DView()
        self.view3d = Graph3DView()
        for view in (self.view2d, self.view3d):
            view.nodeActivated.connect(self.openNote)
            view.nodeMenu.connect(self.nodeMenuRequested)
            view.nodeSelected.connect(self._selected)
        self.stack.addWidget(self.view2d)
        self.stack.addWidget(self.view3d)
        canvas_layout.addWidget(self.stack)
        tools = QHBoxLayout()
        tools.setContentsMargins(8, 4, 8, 6)
        self.info = label("", "caption")
        tools.addWidget(self.info, 1)
        self.spin = tool_button("rotate", _("Rotate automatically (3D)"), checkable=True)
        self.spin.toggled.connect(self.view3d.set_auto_rotate)
        tools.addWidget(self.spin)
        tools.addWidget(tool_button("zoom_out", _("Zoom out"), lambda: self._view().zoom(1 / 1.25)))
        tools.addWidget(tool_button("zoom_in", _("Zoom in"), lambda: self._view().zoom(1.25)))
        tools.addWidget(tool_button("fit", _("Fit to window"), lambda: self._view().fit()))
        tools.addWidget(tool_button("refresh", _("Recompute layout"), self.relayout))
        tools.addWidget(tool_button("image", _("Save as image…"), self.save_image))
        tools.addWidget(
            tool_button(
                "export",
                _("Export these notes…"),
                lambda: self.exportRequested.emit(set(self._ids)),
            )
        )
        canvas_layout.addLayout(tools)
        body.addWidget(canvas, 1)

        legend = QWidget()
        legend.setObjectName("Card")
        legend.setFixedWidth(250)
        legend_layout = QVBoxLayout(legend)
        legend_layout.setContentsMargins(12, 12, 12, 12)
        self.legend_title = label(_("Groups"), "section")
        legend_layout.addWidget(self.legend_title)
        self.legend = QListWidget()
        self.legend.setAccessibleName(_("Groups legend"))
        self.legend.setWordWrap(True)
        self.legend.setIconSize(QSize(14, 14))
        self.legend.itemClicked.connect(self._legend_clicked)
        legend_layout.addWidget(self.legend, 2)
        legend_layout.addWidget(label(_("Link types"), "section"))
        self.type_legend = QListWidget()
        self.type_legend.setAccessibleName(_("Link types legend"))
        self.type_legend.setIconSize(LIST_ICON)
        legend_layout.addWidget(self.type_legend, 1)
        self.quality = label("", "caption", wrap=True)
        legend_layout.addWidget(self.quality)
        body.addWidget(legend)
        layout.addLayout(body, 1)

        self.scope_group.idClicked.connect(lambda _unused: self.refresh())
        self.dim_group.idClicked.connect(self._dims_changed)
        self.depth_spin.valueChanged.connect(
            lambda _unused: self.refresh() if self.scope_group.checkedId() == 1 else None
        )
        self.color_by.currentIndexChanged.connect(lambda _unused: self.refresh())
        self.k.valueChanged.connect(lambda _unused: self.refresh())
        self.group_box.toggled.connect(lambda _unused: self.refresh())
        self.labels_box.toggled.connect(
            lambda _unused: self.refresh()
        )  # layout comes from the cache
        self._ids: list[str] = []
        self._dims_changed(0)

    def _view(self):
        return self.view3d if self.dim_group.checkedId() == 1 else self.view2d

    def _dims_changed(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.spin.setVisible(index == 1)
        if index == 0:
            self.spin.setChecked(False)
        self.refresh()

    def show_local(self, note_id: str | None) -> None:
        self.focus_id = note_id
        if note_id:
            self.scope_group.button(1).setChecked(True)
        self.refresh()

    def set_focus_note(self, note_id: str | None) -> None:
        self.focus_id = note_id

    def relayout(self) -> None:
        self._layouts.clear()
        self._clusters.clear()
        self.refresh()

    def invalidate(self) -> None:
        self._layouts.clear()
        self._clusters.clear()

    # --- data --------------------------------------------------------------

    def _rebuild_types_menu(self, types) -> None:
        self.types_menu.clear()
        for lt in types:
            action = QAction(type_icon(lt, MENU_ICON), lt.label, self.types_menu)
            action.setCheckable(True)
            action.setChecked(lt.id not in self.hidden_types)
            action.toggled.connect(lambda on, t=lt.id: self._toggle_type(t, on))
            self.types_menu.addAction(action)

    def _toggle_type(self, type_id: str, on: bool) -> None:
        (self.hidden_types.discard if on else self.hidden_types.add)(type_id)
        self.invalidate()
        self.refresh()

    def refresh(self) -> None:
        vault = self.window.vault
        if vault is None or not self.isVisible():
            return
        types = vault.link_types()
        self._rebuild_types_menu(types)
        type_map = {lt.id: lt for lt in types}
        notes = {n.id: n for n in vault.all_notes()}
        links = [l for l in vault.all_links() if l.type not in self.hidden_types]
        local = self.scope_group.checkedId() == 1 and self.focus_id in notes
        ids = (
            sorted(subgraph([self.focus_id], links, self.depth_spin.value()))
            if local
            else sorted(notes)
        )
        id_set = set(ids)
        links = [l for l in links if l.src in id_set and l.dst in id_set]
        self._ids = ids
        degree: Counter[str] = Counter()
        for l in links:
            degree[l.src] += 1
            degree[l.dst] += 1
        images = {}
        for i in ids:
            if notes[i].image:
                path = vault.asset_path(notes[i].image)
                if path:
                    images[i] = path
        data = GraphData(
            ids,
            {i: notes[i].display_title for i in ids},
            links,
            dict(degree),
            images=images,
            types=type_map,
            focus=self.focus_id if local else None,
        )
        mode = self.color_by.currentData()
        dims = 3 if self.dim_group.checkedId() == 1 else 2
        grouping = self.group_box.isChecked() and mode != "none"
        self._request += 1
        request = self._request
        self.info.setText(_("Computing layout…"))
        self.status.emit(_("Computing graph layout…"))

        tag_counts = Counter(t for i in ids for t in notes[i].tags)
        note_payload = [notes[i] for i in ids]
        cluster_key = (mode, self.k.value(), tuple(ids), vault.generation)
        layout_key = (
            dims,
            grouping,
            mode,
            self.k.value(),
            tuple(ids),
            tuple(sorted(self.hidden_types)),
            vault.generation,
            tuple((link.src, link.dst, link.type) for link in links),
        )
        cached_clusters = self._clusters.get(cluster_key)
        cached_layout = self._layouts.get(layout_key)

        def work():
            group_of: dict[str, int | None] = {}
            names: list[str] = []
            quality = ""
            cluster_result = None
            if mode == "tag":
                top = [t for t, _unused in tag_counts.most_common()]
                rank = {t: r for r, t in enumerate(top)}
                for i in ids:
                    tags = notes[i].tags
                    group_of[i] = min((rank[t] for t in tags), default=None) if tags else None
                names = [f"#{t}" for t in top]
                quality = _("Each note takes the colour of its most common tag.")
            elif mode in ("kmeans", "hierarchical"):
                cluster_result = cached_clusters or cluster_notes(
                    note_payload, mode, self.k.value() or None
                )
                if cluster_result is not None:
                    label_of = cluster_result.label_of()
                    group_of = {i: label_of.get(i) for i in ids}
                    names = [
                        _("Cluster {n}: {keywords}").format(
                            n=c + 1, keywords=", ".join(cluster_result.keywords.get(c, [])[:3])
                        )
                        for c in range(cluster_result.k)
                    ]
                    k = cluster_result.k
                    quality = (
                        n_(
                            "{n} cluster by k-means clustering of LSA embeddings.",
                            "{n} clusters by k-means clustering of LSA embeddings.",
                            k,
                        )
                        if cluster_result.method == "kmeans"
                        else n_(
                            "{n} cluster by average-linkage hierarchical clustering of LSA embeddings.",
                            "{n} clusters by average-linkage hierarchical clustering of LSA embeddings.",
                            k,
                        )
                    ).format(n=k)
                    if cluster_result.silhouette is not None:
                        quality += " " + _(
                            "Silhouette score {score} (higher is better, max 1)."
                        ).format(score=f"{cluster_result.silhouette:.2f}")
            positions = cached_layout or force_layout(
                ids,
                [(l.src, l.dst) for l in links],
                dims=dims,
                groups={i: g for i, g in group_of.items() if g is not None and g < MAX_GROUP_COLORS}
                if grouping
                else None,
                group_strength=0.5 if grouping else 0.0,
            )
            return group_of, names, quality, positions, cluster_result

        def done(result) -> None:
            if request != self._request:
                return
            group_of, names, quality, positions, cluster_result = result
            if mode in ("kmeans", "hierarchical"):
                _remember(self._clusters, cluster_key, cluster_result)
            _remember(self._layouts, layout_key, positions)
            data.group_of = group_of
            data.group_names = names
            self._view().set_graph(data, positions, grouping, self.labels_box.isChecked())
            self._fill_legend(data, types)
            self.quality.setText(quality)
            info = [
                n_("{n} note", "{n} notes", len(ids)).format(n=len(ids)),
                n_("{n} link", "{n} links", len(links)).format(n=len(links)),
            ]
            if local:
                info.append(_("local graph"))
            self.info.setText(" · ".join(info))
            self.status.emit("")

        run_task(
            work,
            on_done=done,
            on_error=lambda msg: self.info.setText(
                _("Could not draw the graph: {error}").format(error=msg)
            ),
        )

    def _fill_legend(self, data: GraphData, types) -> None:
        self.legend.clear()
        counts = Counter(g for g in data.group_of.values())
        mode = self.color_by.currentData()
        self.legend_title.setText({"tag": _("Tags"), "none": _("Groups")}.get(mode, _("Clusters")))
        other = 0
        for g in sorted(k for k in counts if k is not None):
            if g >= MAX_GROUP_COLORS:
                other += counts[g]
                continue
            item = QListWidgetItem(
                _dot(data.group_color(g)), f"{data.group_label(g)}  ({counts[g]})"
            )
            item.setData(Qt.ItemDataRole.UserRole, g)
            self.legend.addItem(item)
        if other or counts.get(None):
            item = QListWidgetItem(
                _dot(theme.current().q("text_muted")),
                _("Other / untagged ({n})").format(n=other + counts.get(None, 0)),
            )
            item.setData(Qt.ItemDataRole.UserRole, -1)
            self.legend.addItem(item)
        self.type_legend.clear()
        used = Counter(l.type for l in data.links)
        for lt in types:
            if used.get(lt.id):
                self.type_legend.addItem(
                    QListWidgetItem(type_icon(lt), f"{lt.label}  ({used[lt.id]})")
                )

    def _legend_clicked(self, item: QListWidgetItem) -> None:
        group = item.data(Qt.ItemDataRole.UserRole)
        view = self._view()
        members = [n for n, g in view.data.group_of.items() if g == group] if group != -1 else []
        if isinstance(view, Graph2DView):
            view.hover_set = set(members) or None
            view.scene().update()
        else:
            self.status.emit(
                n_("{n} note in this group", "{n} notes in this group", len(members)).format(
                    n=len(members)
                )
            )

    def _selected(self, note_id: str) -> None:
        self.status.emit(self._view().data.titles.get(note_id, ""))

    def _find(self) -> None:
        text = self.search.text().strip().casefold()
        if not text:
            return
        for note_id, title in self._view().data.titles.items():
            if text in (title or "").casefold():
                self._view().focus_node(note_id)
                return
        self.status.emit(_("No note in the graph matches that title."))

    def save_image(self) -> None:
        path, _unused = QFileDialog.getSaveFileName(
            self, _("Save graph as image"), "Graph.png", _("PNG image (*.png)")
        )
        if path:
            self._view().render_image().save(path, "PNG")
            self.window.notify_file(path, _("Graph image saved"))

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()
