"""Tools ▸ Options."""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from zettelapp import i18n, settings, winintegration
from zettelapp.core import apikeys
from zettelapp.core.llm import (
    EFFORTS,
    PROVIDERS,
    LLMError,
    LLMSettings,
    list_models,
    test_connection,
)
from zettelapp.core.models import LinkType, least_used_line_style
from zettelapp.core.suggest import FEATURES
from zettelapp.core.textutil import slugify_type
from zettelapp.i18n import _
from zettelapp.paths import backups_dir
from zettelapp.ui import icons, theme
from zettelapp.ui.graph_common import draw_edge_label
from zettelapp.ui.link_style import (
    ARROW_TIP_NAMES,
    LINE_STYLE_NAMES,
    LIST_ICON,
    draw_sample,
    sample_icon,
    type_color,
    type_icon,
)
from zettelapp.ui.widgets import label, link_button
from zettelapp.ui.workers import run_task


def _merge_mcp_entry(config: dict, entry: dict) -> dict:
    """Return a copy with the ZettelApp server after validating the nested shape."""
    servers = config.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("The existing 'mcpServers' configuration is not a JSON object.")
    merged = dict(config)
    merged["mcpServers"] = {**servers, "zettelapp": entry}
    return merged


PAGES = [
    "General",
    "Link suggestions",
    "Link types",
    "AI assistant",
    "MCP server",
    "Anki",
    "Zotero",
    "Windows integration",
    "Backups",
]
PAGE_ICONS = {
    "General": "settings",
    "Link suggestions": "lightbulb",
    "Link types": "relationship",
    "AI assistant": "chat",
    "MCP server": "server",
    "Anki": "cards",
    "Zotero": "library",
    "Windows integration": "link",
    "Backups": "history",
}
NAV_ROW_HEIGHT = 34


def mcp_command(vault: Path | None, allow_writes: bool) -> tuple[str, list[str], dict]:
    """Command, arguments and environment for launching the MCP server."""
    args = ["--vault", str(vault)] if vault else []
    if allow_writes:
        args.append("--allow-writes")
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).with_name("zettelapp-mcp.exe")), args, {}
    root = str(Path(__file__).resolve().parents[2])
    return sys.executable, ["-m", "zettelapp.mcp_main", *args], {"PYTHONPATH": root}


def claude_desktop_config_path() -> Path:
    return (
        Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        / "Claude"
        / "claude_desktop_config.json"
    )


class _LinkSample(QWidget):
    """A live preview of a link type: two notes joined by a link in its style."""

    def __init__(self):
        super().__init__()
        self.lt: LinkType | None = None
        self.setMinimumHeight(64)
        self.setAccessibleName(_("Preview"))

    def set_type(self, lt: LinkType) -> None:
        self.lt = lt
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        if self.lt is None:
            return
        t = theme.current()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        box = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(t.q("border"), 1))
        p.setBrush(t.q("surface_alt"))
        p.drawRoundedRect(box, 6, 6)
        radius, y = 8.0, box.top() + 32
        a = QPointF(box.left() + 40, y)
        b = QPointF(box.right() - 40, y)
        draw_sample(
            p,
            QPointF(a.x() + radius, y),
            QPointF(b.x() - radius - 3, y),
            type_color(self.lt),
            self.lt.line_style,
            self.lt.tip,
            width=2.2,
        )
        font = theme.ui_font(8.5)
        p.setFont(font)
        for centre, name in ((a, _("Note A")), (b, _("Note B"))):
            p.setPen(QPen(t.q("surface"), 2))
            p.setBrush(t.q("text_muted"))
            p.drawEllipse(centre, radius, radius)
            p.setPen(t.q("text_secondary"))
            p.drawText(
                QRectF(centre.x() - 60, y + radius + 3, 120, 18),
                Qt.AlignmentFlag.AlignHCenter,
                name,
            )
        name = self.lt.label.strip() or _("Untitled")
        draw_edge_label(p, QPointF(box.center().x(), y - 15), name, font)
        reverse = self.lt.inverse_label.strip()
        reading = (
            _("Seen from Note B: {reverse}").format(reverse=reverse)
            if self.lt.directed and reverse
            else _("Reads the same from both notes")
        )
        p.setPen(t.q("text_muted"))
        p.drawText(
            QRectF(a.x() + 60, y + 6, b.x() - a.x() - 120, 20),
            Qt.AlignmentFlag.AlignHCenter,
            p.fontMetrics().elidedText(
                reading, Qt.TextElideMode.ElideRight, int(b.x() - a.x() - 120)
            ),
        )
        p.end()


class OptionsDialog(QDialog):
    def __init__(self, window, page: str = "General"):
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Options")
        self.resize(820, 600)
        outer = QVBoxLayout(self)
        body = QHBoxLayout()
        self.nav = QListWidget()
        self.nav.setFixedWidth(200)
        self.nav.setAccessibleName("Option pages")
        self.nav.setIconSize(QSize(16, 16))
        self.nav.setSpacing(1)
        self.pages = QStackedWidget()
        builders = [
            self._general,
            self._suggestions,
            self._link_types,
            self._ai,
            self._mcp,
            self._anki,
            self._zotero,
            self._integration,
            self._backups,
        ]
        for name, build in zip(PAGES, builders, strict=True):
            item = QListWidgetItem(icons.icon(PAGE_ICONS[name]), name)
            # A fixed row height: setCurrentRow() below lays the list out before the
            # stylesheet's item padding applies, which made rows overlap on hover.
            item.setSizeHint(QSize(0, NAV_ROW_HEIGHT))
            self.nav.addItem(item)
            holder = QWidget()
            lay = QVBoxLayout(holder)
            lay.setContentsMargins(18, 4, 8, 4)
            lay.addWidget(label(name, "heading"))
            build(lay)
            lay.addStretch(1)
            self.pages.addWidget(holder)
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(PAGES.index(page) if page in PAGES else 0)
        body.addWidget(self.nav)
        body.addWidget(self.pages, 1)
        outer.addLayout(body, 1)
        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        box.button(QDialogButtonBox.StandardButton.Ok).setProperty("accent", True)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)
        outer.addWidget(box)

    # --- pages ------------------------------------------------------------

    def _general(self, lay: QVBoxLayout) -> None:
        form = QFormLayout()
        self.theme = QComboBox()
        for text, key in (("Use Windows setting", "system"), ("Light", "light"), ("Dark", "dark")):
            self.theme.addItem(text, key)
        self.theme.setCurrentIndex(max(0, self.theme.findData(settings.get(settings.THEME))))
        form.addRow("App theme", self.theme)
        self.language = QComboBox()
        self.language.addItem(_("Use Windows setting"), "system")
        for code, name in i18n.LANGUAGES.items():
            self.language.addItem(name, code)
        stored = settings.get(settings.UI_LANGUAGE)
        self.language.setCurrentIndex(max(0, self.language.findData(stored)))
        self._language_before = self.language.currentData()
        form.addRow(_("Language"), self.language)
        self.font_size = QSpinBox()
        self.font_size.setRange(9, 20)
        self.font_size.setValue(settings.get(settings.EDITOR_FONT_SIZE))
        self.font_size.setSuffix(" pt")
        form.addRow("Editor text size", self.font_size)
        self.autosave = QSpinBox()
        self.autosave.setRange(300, 10000)
        self.autosave.setSingleStep(100)
        self.autosave.setSuffix(" ms")
        self.autosave.setValue(settings.get(settings.AUTOSAVE_MS))
        form.addRow("Save after typing stops for", self.autosave)
        lay.addLayout(form)
        self.update_check = QCheckBox("Check for updates when ZettelApp starts")
        self.update_check.setToolTip(
            "Downloads a small version file from the ZettelApp website. Nothing about you "
            "or your notes is sent, and a new version is announced only once."
        )
        self.update_check.setChecked(settings.get(settings.UPDATE_CHECK))
        lay.addWidget(self.update_check)
        lay.addWidget(
            label(
                "Notes are saved automatically. Your vault is a folder with a SQLite database "
                "and an assets folder; open another one from File ▸ Open Vault.",
                "caption",
                wrap=True,
            )
        )

    def _suggestions(self, lay: QVBoxLayout) -> None:
        self.suggest_on = QCheckBox("Suggest links while I write")
        self.suggest_on.setChecked(settings.get(settings.SUGGEST_ENABLED))
        lay.addWidget(self.suggest_on)
        lay.addWidget(label("Features used by the Naive Bayes classifier", "section"))
        enabled = settings.get_list(settings.SUGGEST_FEATURES) or [f.key for f in FEATURES]
        self.feature_boxes = {}
        for f in FEATURES:
            box = QCheckBox(f.label)
            box.setChecked(f.key in enabled)
            self.feature_boxes[f.key] = box
            lay.addWidget(box)
        form = QFormLayout()
        self.suggest_limit = QSpinBox()
        self.suggest_limit.setRange(1, 25)
        self.suggest_limit.setValue(settings.get(settings.SUGGEST_LIMIT))
        form.addRow("Show at most", self.suggest_limit)
        self.min_prob = QSlider(Qt.Orientation.Horizontal)
        self.min_prob.setRange(5, 95)
        self.min_prob.setValue(round(settings.get(settings.SUGGEST_MIN_PROB) * 100))
        self.min_prob_label = label("", "secondary")
        self.min_prob.valueChanged.connect(lambda v: self.min_prob_label.setText(f"{v}%"))
        self.min_prob_label.setText(f"{self.min_prob.value()}%")
        row = QHBoxLayout()
        row.addWidget(self.min_prob, 1)
        row.addWidget(self.min_prob_label)
        form.addRow("Minimum match", row)
        self.prior = QDoubleSpinBox()
        self.prior.setRange(0.5, 100)
        self.prior.setValue(settings.get(settings.SUGGEST_PRIOR))
        self.prior.setToolTip(
            "Pseudo-observations behind the prior belief. Higher = trust the prior longer."
        )
        form.addRow("Prior strength", self.prior)
        lay.addLayout(form)
        buttons = QHBoxLayout()
        buttons.addWidget(link_button("Model details…", self._model_details))
        buttons.addWidget(link_button("Forget dismissed suggestions", self._reset_feedback))
        buttons.addStretch(1)
        lay.addLayout(buttons)

    def _model_details(self) -> None:
        report = self.window.suggestions.report()
        importance = report["importance"]
        top = max(importance.values()) or 1
        lines = [
            f"Trained on {report['positives']:.0f} linked and {report['negatives']:.0f} unlinked note pairs "
            f"from {report['notes']} notes.",
            "",
            "How informative each feature is (symmetric KL divergence):",
        ]
        for f in FEATURES:
            v = importance.get(f.key, 0.0)
            lines.append(
                f"{'█' * max(1, round(20 * v / top)) if v else '·':<21} {v:5.2f}  {f.label}"
            )
        QMessageBox.information(self, "Link suggestion model", "\n".join(lines))

    def _reset_feedback(self) -> None:
        if (
            self.window.vault
            and QMessageBox.question(
                self,
                "Forget dismissed suggestions",
                "Dismissed suggestions will be suggested again and stop counting as negative examples. Continue?",
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.window.vault.reset_feedback()

    def _link_types(self, lay: QVBoxLayout) -> None:
        lay.addWidget(
            label(
                _(
                    "Typed links say how notes relate. Directed types read differently from "
                    "each side (“Supports” / “Supported by”). Each type has its own colour and "
                    "line, so links stay easy to tell apart in the graph even without colour."
                ),
                "caption",
                wrap=True,
            )
        )
        body = QHBoxLayout()
        body.setSpacing(12)
        left = QVBoxLayout()
        self.types_list = QListWidget()
        self.types_list.setAccessibleName(_("Link types"))
        self.types_list.setIconSize(LIST_ICON)
        self.types_list.setFixedWidth(220)
        self.types_list.currentRowChanged.connect(self._show_type)
        left.addWidget(self.types_list, 1)
        buttons = QHBoxLayout()
        buttons.addWidget(link_button(_("Add link type"), self._add_type))
        self.remove_type_button = link_button(_("Remove"), self._remove_type)
        buttons.addWidget(self.remove_type_button)
        buttons.addStretch(1)
        left.addLayout(buttons)
        body.addLayout(left)

        editor = QWidget()
        editor.setObjectName("Card")
        editor_lay = QVBoxLayout(editor)
        editor_lay.setContentsMargins(16, 14, 16, 14)
        editor_lay.setSpacing(10)
        form = QFormLayout()
        form.setHorizontalSpacing(14)
        self.type_name = QLineEdit()
        self.type_name.setMaxLength(60)
        self.type_name.textEdited.connect(self._type_edited)
        form.addRow(_("Name"), self.type_name)
        self.type_reverse = QLineEdit()
        self.type_reverse.setMaxLength(60)
        self.type_reverse.setToolTip(_("How the link reads from the note it points to"))
        self.type_reverse.textEdited.connect(self._type_edited)
        form.addRow(_("Reverse name"), self.type_reverse)
        self.type_directed = QCheckBox(_("Directed: reads differently from each side"))
        self.type_directed.toggled.connect(self._type_edited)
        form.addRow("", self.type_directed)
        self.type_colour = QPushButton()
        self.type_colour.setAccessibleName(_("Colour"))
        self.type_colour.setToolTip(_("Choose a colour"))
        self.type_colour.setCursor(Qt.CursorShape.PointingHandCursor)
        self.type_colour.clicked.connect(self._pick_colour)
        colour_row = QHBoxLayout()
        colour_row.addWidget(self.type_colour)
        colour_row.addStretch(1)
        form.addRow(_("Colour"), colour_row)
        self.type_line = QComboBox()
        self.type_line.setAccessibleName(_("Line style"))
        self.type_line.setIconSize(LIST_ICON)
        for key, name in LINE_STYLE_NAMES.items():
            self.type_line.addItem(_(name), key)
        self.type_line.currentIndexChanged.connect(self._type_edited)
        form.addRow(_("Line"), self.type_line)
        self.type_arrow = QComboBox()
        self.type_arrow.setAccessibleName(_("Arrow tip"))
        self.type_arrow.setIconSize(LIST_ICON)
        for key, name in ARROW_TIP_NAMES.items():
            self.type_arrow.addItem(_(name), key)
        self.type_arrow.currentIndexChanged.connect(self._type_edited)
        form.addRow(_("Arrow tip"), self.type_arrow)
        editor_lay.addLayout(form)
        self.type_sample = _LinkSample()
        editor_lay.addWidget(self.type_sample)
        self.type_hint = label("", "caption", wrap=True)
        self.type_hint.setTextFormat(Qt.TextFormat.PlainText)
        editor_lay.addWidget(self.type_hint)
        editor_lay.addStretch(1)
        body.addWidget(editor, 1)
        lay.addLayout(body, 1)

        self._removed_types: list[str] = []
        self._types = [
            replace(lt) for lt in (self.window.vault.link_types() if self.window.vault else [])
        ]
        self._loading_type = False
        self._type_editor = editor
        editor.setEnabled(False)
        for lt in self._types:
            self.types_list.addItem(QListWidgetItem(type_icon(lt), lt.label))
        if self._types:
            self.types_list.setCurrentRow(0)

    def _current_type(self) -> LinkType | None:
        row = self.types_list.currentRow()
        return self._types[row] if 0 <= row < len(self._types) else None

    def _show_type(self, row: int) -> None:
        """Fill the editor with the link type in *row*."""
        lt = self._current_type()
        self._type_editor.setEnabled(lt is not None)
        if lt is None:
            self.remove_type_button.setEnabled(False)
            return
        self._loading_type = True
        self.type_name.setText(lt.label)
        self.type_reverse.setText(lt.inverse_label)
        self.type_directed.setChecked(lt.directed)
        self.type_line.setCurrentIndex(max(0, self.type_line.findData(lt.line_style)))
        self.type_arrow.setCurrentIndex(max(0, self.type_arrow.findData(lt.arrow)))
        self._loading_type = False
        self.remove_type_button.setEnabled(not lt.builtin)
        self.remove_type_button.setToolTip(
            _("Built-in link types can be renamed and restyled but not removed.")
            if lt.builtin
            else ""
        )
        self._refresh_type()

    def _type_edited(self, *_args) -> None:
        lt = self._current_type()
        if lt is None or self._loading_type:
            return
        lt.label = self.type_name.text()
        lt.inverse_label = self.type_reverse.text()
        lt.directed = self.type_directed.isChecked()
        lt.line_style = self.type_line.currentData()
        lt.arrow = self.type_arrow.currentData()
        self._refresh_type()

    def _refresh_type(self) -> None:
        """Redraw the previews of the type being edited."""
        lt = self._current_type()
        if lt is None:
            return
        color = type_color(lt)
        item = self.types_list.currentItem()
        item.setText(lt.label.strip() or _("Untitled"))
        item.setIcon(type_icon(lt))
        self.type_reverse.setEnabled(lt.directed)
        self.type_arrow.setEnabled(lt.directed)
        self.type_reverse.setPlaceholderText("" if lt.directed else _("Same as the name"))
        swatch = QPixmap(32, 32)
        swatch.setDevicePixelRatio(2)
        swatch.fill(Qt.GlobalColor.transparent)
        p = QPainter(swatch)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(theme.current().q("border_strong"), 1))
        p.setBrush(color)
        p.drawRoundedRect(QRectF(1.5, 1.5, 13, 13), 3, 3)
        p.end()
        self.type_colour.setIcon(QIcon(swatch))
        self.type_colour.setText(lt.color.upper())
        for i in range(self.type_line.count()):
            self.type_line.setItemIcon(i, sample_icon(color, self.type_line.itemData(i), None))
        for i in range(self.type_arrow.count()):
            self.type_arrow.setItemIcon(i, sample_icon(color, "solid", self.type_arrow.itemData(i)))
        self.type_sample.set_type(lt)
        type_id = lt.id or slugify_type(lt.label)
        hint = (
            _("In a note, write {example}.").format(example=f"{type_id}::[[…]]")
            if type_id
            else _("Give the link type a name.")
        )
        if lt.builtin:
            hint += " " + _("Built-in link types can be renamed and restyled but not removed.")
        self.type_hint.setText(hint)

    def _pick_colour(self) -> None:
        lt = self._current_type()
        if lt is None:
            return
        colour = QColorDialog.getColor(QColor(lt.color), self, _("Link colour"))
        if colour.isValid():
            lt.color = colour.name()
            self._refresh_type()

    def _add_type(self) -> None:
        used = [lt.color.lower() for lt in self._types]
        lt = LinkType(
            "",
            _("New link type"),
            _("New link type (reverse)"),
            min(theme.CATEGORICAL_LIGHT, key=used.count),
            line_style=least_used_line_style(self._types),
        )
        self._types.append(lt)
        self.types_list.addItem(QListWidgetItem(type_icon(lt), lt.label))
        self.types_list.setCurrentRow(len(self._types) - 1)
        self.type_name.setFocus()
        self.type_name.selectAll()

    def _remove_type(self) -> None:
        lt = self._current_type()
        if lt is None or lt.builtin:
            return
        if lt.id:
            self._removed_types.append(lt.id)
        row = self.types_list.currentRow()
        del self._types[row]
        self.types_list.takeItem(row)
        self._show_type(self.types_list.currentRow())

    def _save_link_types(self, vault) -> bool:
        """Store the edited link types; False (after saying why) if one can't be saved."""
        taken: set[str] = set()
        for row, lt in enumerate(self._types):
            type_id = lt.id or slugify_type(lt.label)
            problem = None
            if not type_id:
                problem = _("Give the new link type a name.")
            elif type_id in taken:
                problem = _("There is already a link type “{name}”.").format(name=lt.label.strip())
            if problem:
                self.nav.setCurrentRow(PAGES.index("Link types"))
                self.types_list.setCurrentRow(row)
                QMessageBox.warning(self, _("Link types"), problem)
                return False
            taken.add(type_id)
        for type_id in self._removed_types:
            vault.delete_link_type(type_id)
        self._removed_types = []
        for lt in self._types:
            lt.id = vault.save_link_type(replace(lt)).id  # new types keep their id from now on
        self._refresh_type()
        return True

    def _ai(self, lay: QVBoxLayout) -> None:
        lay.addWidget(
            label(
                _(
                    "Connect an AI provider to ask questions about your notes (Ask page). Keys are stored "
                    "in Windows Credential Manager, never in plain files. You can save several keys per provider and pick the one to use. Only your question and the "
                    "most relevant notes are sent."
                ),
                "caption",
                wrap=True,
            )
        )
        form = QFormLayout()
        self.provider = QComboBox()
        for pid, info in PROVIDERS.items():
            self.provider.addItem(info.label, pid)
        self.provider.setCurrentIndex(
            max(0, self.provider.findData(settings.get(settings.LLM_PROVIDER)))
        )
        form.addRow(_("Provider"), self.provider)
        self.key_choice = QComboBox()
        self.key_choice.setAccessibleName(_("API key"))
        self.key_choice.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        key_row = QHBoxLayout()
        key_row.addWidget(self.key_choice, 1)
        key_row.addWidget(link_button(_("Add key…"), self._add_key))
        self.key_rename = link_button(_("Rename"), self._rename_key)
        key_row.addWidget(self.key_rename)
        self.key_remove = link_button(_("Delete"), self._remove_key)
        key_row.addWidget(self.key_remove)
        self.key_link = link_button(_("Get a key"), self._open_key_page)
        key_row.addWidget(self.key_link)
        form.addRow(_("API key"), key_row)
        self.key_hint = label("", "caption", wrap=True)
        form.addRow("", self.key_hint)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.setAccessibleName(_("Model"))
        model_row = QHBoxLayout()
        model_row.addWidget(self.model, 1)
        model_row.addWidget(link_button(_("Refresh list"), self._refresh_models))
        form.addRow(_("Model"), model_row)
        self.base_url = QLineEdit(settings.get(settings.LLM_BASE_URL, "") or "")
        form.addRow(_("Endpoint (optional)"), self.base_url)
        self.effort = QComboBox()
        for e in EFFORTS:
            self.effort.addItem(e.capitalize(), e)
        self.effort.setCurrentIndex(max(0, self.effort.findData(settings.get(settings.LLM_EFFORT))))
        self.effort.setToolTip(
            _("Claude only: how much the model thinks before answering (higher costs more)")
        )
        form.addRow(_("Effort"), self.effort)
        lay.addLayout(form)
        test = QPushButton(_("Test connection"))
        test.setIcon(icons.icon("check"))
        test.clicked.connect(self._test)
        self.ai_status = label("", "secondary", wrap=True)
        row = QHBoxLayout()
        row.addWidget(test)
        row.addWidget(self.ai_status, 1)
        lay.addLayout(row)
        self.provider.currentIndexChanged.connect(self._provider_changed)
        self._provider_changed(initial=True)

    def _fill_keys(self, select: str | None = None) -> None:
        provider = self.provider.currentData()
        info = PROVIDERS[provider]
        keys = apikeys.list_keys(provider)
        select = select or apikeys.active_id(provider)
        self.key_choice.blockSignals(True)
        self.key_choice.clear()
        for k in keys:
            self.key_choice.addItem(k.label, k.id)
        if not keys:
            self.key_choice.addItem(
                _("No saved keys") if info.requires_key else _("Not required"), None
            )
        self.key_choice.setCurrentIndex(max(0, self.key_choice.findData(select)))
        self.key_choice.blockSignals(False)
        self.key_choice.setEnabled(bool(keys))
        self.key_rename.setEnabled(bool(keys))
        self.key_remove.setEnabled(bool(keys))
        self.key_hint.setText(
            _(
                "The selected key is the one used for questions. Keys are kept in Windows Credential Manager."
            )
            if len(keys) > 1
            else ""
        )

    def _provider_changed(self, *_args, initial: bool = False) -> None:
        info = PROVIDERS[self.provider.currentData()]
        self._fill_keys()
        self.model.clear()
        self.model.addItems(list(info.suggested_models))
        saved = settings.get(settings.LLM_MODEL, "") if initial else ""
        self.model.setCurrentText(saved or info.default_model)
        self.base_url.setPlaceholderText(info.base_url or _("Default endpoint"))
        if not initial:
            self.base_url.clear()
        self.effort.setEnabled(info.kind == "anthropic")

    def _llm_settings(self) -> LLMSettings:
        return LLMSettings(
            provider=self.provider.currentData(),
            model=self.model.currentText().strip(),
            base_url=self.base_url.text().strip(),
            effort=self.effort.currentData(),
        )

    def _key_for_test(self) -> str | None:
        key_id = self.key_choice.currentData()
        return apikeys.get_key(self.provider.currentData(), key_id) if key_id else None

    def _open_key_page(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl(PROVIDERS[self.provider.currentData()].key_url))

    def _add_key(self) -> None:
        provider = self.provider.currentData()
        info = PROVIDERS[provider]
        count = len(apikeys.list_keys(provider)) + 1
        name, ok = QInputDialog.getText(
            self,
            _("Add key"),
            _("A name to recognise this key by:"),
            text=_("Key {number}").format(number=count),
        )
        if not ok:
            return
        value, ok = QInputDialog.getText(
            self,
            _("Add key"),
            _("Paste your {label} API key:").format(label=info.label),
            QLineEdit.EchoMode.Password,
        )
        if not ok or not value.strip():
            return
        try:
            profile = apikeys.add_key(provider, name, value)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, _("API key"), str(exc))
            return
        self._fill_keys(profile.id)
        self.ai_status.setText(_("Key “{name}” saved on this computer.").format(name=profile.label))

    def _rename_key(self) -> None:
        provider, key_id = self.provider.currentData(), self.key_choice.currentData()
        if not key_id:
            return
        name, ok = QInputDialog.getText(
            self, _("Rename key"), _("Name:"), text=self.key_choice.currentText()
        )
        if ok and name.strip():
            apikeys.rename_key(provider, key_id, name)
            self._fill_keys(key_id)

    def _remove_key(self) -> None:
        provider, key_id = self.provider.currentData(), self.key_choice.currentData()
        if not key_id:
            return
        name = self.key_choice.currentText()
        if (
            QMessageBox.question(
                self,
                _("Delete key"),
                _("Delete the key “{name}” from this computer?").format(name=name),
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            apikeys.delete_key(provider, key_id)
        except OSError as exc:
            QMessageBox.warning(self, _("API key"), str(exc))
            return
        self._fill_keys()
        self.ai_status.setText(_("Key “{name}” deleted from this computer.").format(name=name))

    def _test(self) -> None:
        cfg, key = self._llm_settings(), self._key_for_test()
        self.ai_status.setText("Testing…")
        run_task(
            test_connection,
            cfg,
            key,
            on_done=self.ai_status.setText,
            on_error=lambda msg: self.ai_status.setText(f"Failed: {msg}"),
        )

    def _refresh_models(self) -> None:
        cfg, key = self._llm_settings(), self._key_for_test()
        current = self.model.currentText()

        def done(models: list[str]) -> None:
            self.model.clear()
            self.model.addItems(models)
            self.model.setCurrentText(current)
            self.ai_status.setText(f"{len(models)} models available.")

        run_task(
            list_models,
            cfg,
            key,
            on_done=done,
            on_error=lambda msg: self.ai_status.setText(f"Failed: {msg}"),
        )

    def _mcp(self, lay: QVBoxLayout) -> None:
        lay.addWidget(
            label(
                "ZettelApp includes a Model Context Protocol (MCP) server, so assistants such as "
                "Claude Desktop or Claude Code can search and read your vault. It works only while "
                "ZettelApp is open and the MCP switch in the status bar is on. The switch is off "
                "whenever ZettelApp starts, and the server stops as soon as you switch it off or "
                "close ZettelApp. Turn the switch on before you start your MCP client, or reconnect "
                "ZettelApp in the client afterwards. The server talks over standard input/output "
                "(no network port) and is read-only unless you allow changes below.",
                "caption",
                wrap=True,
            )
        )
        self.mcp_writes = QCheckBox("Allow MCP clients to create notes and links")
        self.mcp_writes.setChecked(settings.get(settings.MCP_ALLOW_WRITES))
        self.mcp_writes.toggled.connect(self._update_mcp_snippets)
        lay.addWidget(self.mcp_writes)
        lay.addWidget(label("Claude Desktop (claude_desktop_config.json)", "section"))
        self.mcp_json = QPlainTextEdit()
        self.mcp_json.setReadOnly(True)
        self.mcp_json.setFixedHeight(150)
        lay.addWidget(self.mcp_json)
        row = QHBoxLayout()
        row.addWidget(
            link_button(
                "Copy", lambda: QGuiApplication.clipboard().setText(self.mcp_json.toPlainText())
            )
        )
        row.addWidget(link_button("Add to Claude Desktop…", self._install_claude_desktop))
        row.addStretch(1)
        lay.addLayout(row)
        lay.addWidget(label("Claude Code", "section"))
        self.mcp_cli = QLineEdit()
        self.mcp_cli.setReadOnly(True)
        lay.addWidget(self.mcp_cli)
        lay.addWidget(
            link_button("Copy", lambda: QGuiApplication.clipboard().setText(self.mcp_cli.text())),
            0,
            Qt.AlignmentFlag.AlignLeft,
        )
        self._update_mcp_snippets()

    def _mcp_entry(self) -> dict:
        command, args, env = mcp_command(
            self.window.vault.folder if self.window.vault else None, self.mcp_writes.isChecked()
        )
        entry = {"command": command, "args": args}
        if env:
            entry["env"] = env
        return entry

    def _update_mcp_snippets(self) -> None:
        entry = self._mcp_entry()
        self.mcp_json.setPlainText(json.dumps({"mcpServers": {"zettelapp": entry}}, indent=2))
        quoted = " ".join(f'"{a}"' if " " in a else a for a in [entry["command"], *entry["args"]])
        env = "".join(f" -e {k}={v}" for k, v in entry.get("env", {}).items())
        self.mcp_cli.setText(f"claude mcp add zettelapp{env} -- {quoted}")

    def _install_claude_desktop(self) -> None:
        path = claude_desktop_config_path()
        if (
            QMessageBox.question(
                self,
                "Add to Claude Desktop",
                f"Add the ZettelApp MCP server to\n{path}?\n\nA backup of the current file is "
                "saved next to it. Restart Claude Desktop afterwards.",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            if not isinstance(config, dict):
                raise ValueError("The existing configuration is not a JSON object.")
            config = _merge_mcp_entry(config, self._mcp_entry())
            if path.exists():
                shutil.copy2(path, path.with_suffix(".json.bak"))
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(config, indent=2), encoding="utf-8")
            os.replace(tmp, path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(
                self, "Add to Claude Desktop", f"Could not update the configuration: {exc}"
            )
            return
        QMessageBox.information(
            self, "Add to Claude Desktop", "Done. Restart Claude Desktop to load ZettelApp."
        )

    def _anki(self, lay: QVBoxLayout) -> None:
        form = QFormLayout()
        self.anki_port = QSpinBox()
        self.anki_port.setRange(1024, 65535)
        self.anki_port.setValue(settings.get(settings.ANKI_PORT))
        form.addRow("AnkiConnect port", self.anki_port)
        self.anki_deck = QLineEdit(settings.get(settings.ANKI_DECK))
        form.addRow("Default deck", self.anki_deck)
        lay.addLayout(form)
        lay.addWidget(
            label(
                "ZettelApp only connects to AnkiConnect on this computer (127.0.0.1).",
                "caption",
                wrap=True,
            )
        )

    def _zotero(self, lay: QVBoxLayout) -> None:
        lay.addWidget(
            label(
                "Cite Zotero items in notes (Insert ▸ Zotero Reference) and create literature notes linked to them. "
                "ZettelApp reads your library through Zotero's local API, which never leaves this computer and is "
                "read-only. Turn it on in Zotero 7 or later: Settings ▸ Advanced ▸ “Allow other applications on this "
                "computer to communicate with Zotero”. Clicking a zotero:// link opens the item or PDF in Zotero.",
                "caption",
                wrap=True,
            )
        )
        form = QFormLayout()
        self.zotero_port = QSpinBox()
        self.zotero_port.setRange(1024, 65535)
        self.zotero_port.setValue(settings.get(settings.ZOTERO_PORT))
        form.addRow("Zotero port", self.zotero_port)
        lay.addLayout(form)
        test = QPushButton("Test connection")
        test.setIcon(icons.icon("check"))
        self.zotero_status = label("", "secondary", wrap=True)
        test.clicked.connect(self._test_zotero)
        row = QHBoxLayout()
        row.addWidget(test)
        row.addWidget(self.zotero_status, 1)
        lay.addLayout(row)

    def _test_zotero(self) -> None:
        from zettelapp.core.zotero import ZoteroClient

        self.zotero_status.setText("Testing…")
        run_task(
            lambda: ZoteroClient(self.zotero_port.value()).search("", limit=1),
            on_done=lambda items: self.zotero_status.setText("Connected to Zotero."),
            on_error=lambda msg: self.zotero_status.setText(msg),
        )

    def _integration(self, lay: QVBoxLayout) -> None:
        lay.addWidget(
            label(
                "Register zettelapp:// links so that links on Anki cards (and elsewhere) open the "
                "matching note. The installer does this for you; use this for the portable version. "
                "Only “open note” links are accepted.",
                "caption",
                wrap=True,
            )
        )
        self.protocol_status = label("", "secondary")
        lay.addWidget(self.protocol_status)
        row = QHBoxLayout()
        register = QPushButton("Register links")
        register.clicked.connect(
            lambda: (winintegration.register_url_protocol(), self._update_protocol())
        )
        unregister = QPushButton("Remove registration")
        unregister.clicked.connect(
            lambda: (winintegration.unregister_url_protocol(), self._update_protocol())
        )
        row.addWidget(register)
        row.addWidget(unregister)
        row.addStretch(1)
        lay.addLayout(row)
        self._update_protocol()

    def _update_protocol(self) -> None:
        command = winintegration.registered_command()
        self.protocol_status.setText(f"Registered: {command}" if command else "Not registered.")

    def _backups(self, lay: QVBoxLayout) -> None:
        self.backup_on = QCheckBox("Back up the vault database once a day when it is opened")
        self.backup_on.setChecked(settings.get(settings.BACKUP_ENABLED))
        lay.addWidget(self.backup_on)
        form = QFormLayout()
        self.backup_keep = QSpinBox()
        self.backup_keep.setRange(1, 100)
        self.backup_keep.setValue(settings.get(settings.BACKUP_KEEP))
        form.addRow("Keep the newest", self.backup_keep)
        lay.addLayout(form)
        lay.addWidget(
            label(
                f"Backups are stored in {backups_dir()}. Images are content-addressed and are "
                "never deleted automatically.",
                "caption",
                wrap=True,
            )
        )
        row = QHBoxLayout()
        now = QPushButton("Back up now")
        now.clicked.connect(self.window.backup_now)
        folder = QPushButton("Open backups folder")
        folder.clicked.connect(lambda: winintegration.reveal_in_explorer(backups_dir()))
        row.addWidget(now)
        row.addWidget(folder)
        row.addStretch(1)
        lay.addLayout(row)

    # --- apply --------------------------------------------------------------

    def apply(self) -> bool:
        settings.put(settings.THEME, self.theme.currentData())
        if self.language.currentData() != self._language_before:
            settings.put(settings.UI_LANGUAGE, self.language.currentData())
            self._language_before = self.language.currentData()
            QMessageBox.information(
                self,
                _("Language"),
                _("Restart ZettelApp to apply the new language."),
            )
        settings.put(settings.EDITOR_FONT_SIZE, self.font_size.value())
        settings.put(settings.AUTOSAVE_MS, self.autosave.value())
        settings.put(settings.UPDATE_CHECK, self.update_check.isChecked())
        settings.put(settings.SUGGEST_ENABLED, self.suggest_on.isChecked())
        settings.put(
            settings.SUGGEST_FEATURES, [k for k, b in self.feature_boxes.items() if b.isChecked()]
        )
        settings.put(settings.SUGGEST_LIMIT, self.suggest_limit.value())
        settings.put(settings.SUGGEST_MIN_PROB, self.min_prob.value() / 100)
        settings.put(settings.SUGGEST_PRIOR, self.prior.value())
        settings.put(settings.ANKI_PORT, self.anki_port.value())
        settings.put(settings.ANKI_DECK, self.anki_deck.text().strip() or "ZettelApp")
        settings.put(settings.ZOTERO_PORT, self.zotero_port.value())
        settings.put(settings.BACKUP_ENABLED, self.backup_on.isChecked())
        settings.put(settings.BACKUP_KEEP, self.backup_keep.value())
        settings.put(settings.MCP_ALLOW_WRITES, self.mcp_writes.isChecked())
        settings.put(settings.LLM_PROVIDER, self.provider.currentData())
        settings.put(settings.LLM_MODEL, self.model.currentText().strip())
        settings.put(settings.LLM_EFFORT, self.effort.currentData())
        base_url = self.base_url.text().strip()
        if base_url:
            from zettelapp.core.llm import validate_base_url

            try:
                validate_base_url(base_url)
            except LLMError as exc:
                QMessageBox.warning(self, "Endpoint", str(exc))
                return False
        settings.put(settings.LLM_BASE_URL, base_url)
        key_id = self.key_choice.currentData()
        if key_id:
            apikeys.set_active(self.provider.currentData(), key_id)
        vault = self.window.vault
        if vault is not None and not self._save_link_types(vault):
            return False
        self.window.settings_changed()
        return True

    def accept(self) -> None:
        if self.apply():
            super().accept()
