"""Tools ▸ Options."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from zettelapp import settings, winintegration
from zettelapp.core.llm import (
    EFFORTS,
    PROVIDERS,
    LLMError,
    LLMSettings,
    list_models,
    test_connection,
)
from zettelapp.core.models import LinkType
from zettelapp.core.secrets import delete_secret, get_secret, set_secret
from zettelapp.core.suggest import FEATURES
from zettelapp.paths import backups_dir
from zettelapp.ui import icons
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
                "Typed links say how notes relate. Directed types read differently from each side "
                "(“Supports” / “Supported by”). In text, write type:: [[Note]], e.g. supports:: [[Claim]].",
                "caption",
                wrap=True,
            )
        )
        self.types_table = QTableWidget(0, 4)
        self.types_table.setHorizontalHeaderLabels(["Name", "Reverse name", "Colour", "Directed"])
        self.types_table.horizontalHeader().setStretchLastSection(True)
        self.types_table.verticalHeader().setVisible(False)
        self.types_table.cellDoubleClicked.connect(self._pick_colour)
        lay.addWidget(self.types_table, 1)
        row = QHBoxLayout()
        row.addWidget(link_button("Add link type", self._add_type))
        row.addWidget(link_button("Remove selected", self._remove_type))
        row.addStretch(1)
        lay.addLayout(row)
        self._removed_types: list[str] = []
        for lt in self.window.vault.link_types() if self.window.vault else []:
            self._add_type_row(lt)

    def _add_type_row(self, lt: LinkType) -> None:
        r = self.types_table.rowCount()
        self.types_table.insertRow(r)
        name = QTableWidgetItem(lt.label)
        name.setData(Qt.ItemDataRole.UserRole, lt.id)
        self.types_table.setItem(r, 0, name)
        self.types_table.setItem(r, 1, QTableWidgetItem(lt.inverse_label))
        colour = QTableWidgetItem(lt.color)
        colour.setBackground(QColor(lt.color))
        colour.setForeground(QColor("#ffffff"))
        colour.setFlags(colour.flags() & ~Qt.ItemFlag.ItemIsEditable)
        colour.setToolTip("Double-click to choose a colour")
        self.types_table.setItem(r, 2, colour)
        directed = QTableWidgetItem()
        directed.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        directed.setCheckState(Qt.CheckState.Checked if lt.directed else Qt.CheckState.Unchecked)
        self.types_table.setItem(r, 3, directed)

    def _pick_colour(self, row: int, column: int) -> None:
        if column != 2:
            return
        item = self.types_table.item(row, 2)
        colour = QColorDialog.getColor(QColor(item.text()), self, "Link colour")
        if colour.isValid():
            item.setText(colour.name())
            item.setBackground(colour)

    def _add_type(self) -> None:
        self._add_type_row(LinkType("", "New link type", "New link type (reverse)", "#6250d6"))
        self.types_table.editItem(self.types_table.item(self.types_table.rowCount() - 1, 0))

    def _remove_type(self) -> None:
        row = self.types_table.currentRow()
        if row < 0:
            return
        type_id = self.types_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if type_id == "related":
            QMessageBox.information(
                self, "Link types", "“Related to” is the default link type and can't be removed."
            )
            return
        if type_id:
            self._removed_types.append(type_id)
        self.types_table.removeRow(row)

    def _ai(self, lay: QVBoxLayout) -> None:
        lay.addWidget(
            label(
                "Connect an AI provider to ask questions about your notes (Ask page). Keys are stored "
                "in Windows Credential Manager, never in plain files. Only your question and the "
                "most relevant notes are sent.",
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
        form.addRow("Provider", self.provider)
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setAccessibleName("API key")
        key_row = QHBoxLayout()
        key_row.addWidget(self.key, 1)
        self.key_link = link_button("Get a key", self._open_key_page)
        key_row.addWidget(self.key_link)
        remove = link_button("Remove key", self._remove_key)
        key_row.addWidget(remove)
        form.addRow("API key", key_row)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.setAccessibleName("Model")
        model_row = QHBoxLayout()
        model_row.addWidget(self.model, 1)
        model_row.addWidget(link_button("Refresh list", self._refresh_models))
        form.addRow("Model", model_row)
        self.base_url = QLineEdit(settings.get(settings.LLM_BASE_URL, "") or "")
        form.addRow("Endpoint (optional)", self.base_url)
        self.effort = QComboBox()
        for e in EFFORTS:
            self.effort.addItem(e.capitalize(), e)
        self.effort.setCurrentIndex(max(0, self.effort.findData(settings.get(settings.LLM_EFFORT))))
        self.effort.setToolTip(
            "Claude only: how much the model thinks before answering (higher costs more)"
        )
        form.addRow("Effort", self.effort)
        lay.addLayout(form)
        test = QPushButton("Test connection")
        test.setIcon(icons.icon("check"))
        test.clicked.connect(self._test)
        self.ai_status = label("", "secondary", wrap=True)
        row = QHBoxLayout()
        row.addWidget(test)
        row.addWidget(self.ai_status, 1)
        lay.addLayout(row)
        self.provider.currentIndexChanged.connect(self._provider_changed)
        self._provider_changed(initial=True)

    def _provider_changed(self, *_args, initial: bool = False) -> None:
        info = PROVIDERS[self.provider.currentData()]
        has_key = bool(get_secret(info.secret_name))
        self.key.clear()
        self.key.setPlaceholderText(
            "Saved in Windows Credential Manager (type to replace)"
            if has_key
            else ("Paste your API key" if info.requires_key else "Not required")
        )
        self.model.clear()
        self.model.addItems(list(info.suggested_models))
        saved = settings.get(settings.LLM_MODEL, "") if initial else ""
        self.model.setCurrentText(saved or info.default_model)
        self.base_url.setPlaceholderText(info.base_url or "Default endpoint")
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
        return self.key.text().strip() or get_secret(
            PROVIDERS[self.provider.currentData()].secret_name
        )

    def _open_key_page(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl(PROVIDERS[self.provider.currentData()].key_url))

    def _remove_key(self) -> None:
        info = PROVIDERS[self.provider.currentData()]
        delete_secret(info.secret_name)
        self._provider_changed()
        self.ai_status.setText(f"{info.label} key removed from this computer.")

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
        if self.key.text().strip():
            set_secret(PROVIDERS[self.provider.currentData()].secret_name, self.key.text().strip())
            self.key.clear()
            self._provider_changed()
        vault = self.window.vault
        if vault is not None:
            for type_id in self._removed_types:
                vault.delete_link_type(type_id)
            self._removed_types = []
            for r in range(self.types_table.rowCount()):
                name = self.types_table.item(r, 0)
                vault.save_link_type(
                    LinkType(
                        name.data(Qt.ItemDataRole.UserRole) or name.text(),
                        name.text(),
                        self.types_table.item(r, 1).text(),
                        self.types_table.item(r, 2).text(),
                        self.types_table.item(r, 3).checkState() == Qt.CheckState.Checked,
                    )
                )
        self.window.settings_changed()
        return True

    def accept(self) -> None:
        if self.apply():
            super().accept()
