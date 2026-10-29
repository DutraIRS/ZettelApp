"""The main window: navigation, menus, vault lifecycle and wiring between pages."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from zettelapp import (
    APP_NAME,
    DOCS_URL,
    HOMEPAGE_URL,
    ISSUES_URL,
    RELEASES_URL,
    SPONSOR_URL,
    settings,
    winintegration,
)
from zettelapp.core.export import export as run_export
from zettelapp.core.graph import subgraph
from zettelapp.core.importer import import_path
from zettelapp.core.security import (
    UnsafeInputError,
    is_valid_note_id,
    local_file_path,
    safe_filename,
)
from zettelapp.core.starter import HUB as STARTER_HUB
from zettelapp.core.starter import create_starter_notes
from zettelapp.core.storage import Vault, VaultError
from zettelapp.core.suggest import FEATURES, NoteData
from zettelapp.core.textutil import strip_markdown
from zettelapp.core.updates import available_update
from zettelapp.i18n import N_, _, n_
from zettelapp.mcp_switch import McpSwitch
from zettelapp.paths import backups_dir, default_vault_dir, documents_dir
from zettelapp.ui import icons, theme
from zettelapp.ui.ask_page import AskPage
from zettelapp.ui.dialogs import AboutDialog, ExportDialog, LinkPickerDialog, ShortcutsDialog
from zettelapp.ui.editor import NoteEditor
from zettelapp.ui.graph_page import GraphPage
from zettelapp.ui.insights import InsightsPage
from zettelapp.ui.note_list import NoteListPanel
from zettelapp.ui.quest import Quest
from zettelapp.ui.review_page import ReviewPage
from zettelapp.ui.settings_dialog import OptionsDialog
from zettelapp.ui.side_panel import SidePanel
from zettelapp.ui.update_notice import UpdateNotice
from zettelapp.ui.widgets import InfoBar, ToggleSwitch, label
from zettelapp.ui.workers import SuggestionService, run_task

log = logging.getLogger(__name__)

NAV = [
    ("notes", N_("Notes")),
    ("graph", N_("Graph")),
    ("insights", N_("Insights")),
    ("review", N_("Review")),
    ("chat", N_("Ask")),
]


class NavRail(QWidget):
    def __init__(self, on_change, on_settings, on_donate):
        super().__init__()
        self.setObjectName("NavRail")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(76)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 10, 6, 10)
        layout.setSpacing(4)
        self.group = QButtonGroup(self)
        self.buttons: list[QToolButton] = []
        for i, (glyph, text) in enumerate(NAV):
            b = self._button(glyph, _(text))
            b.setCheckable(True)
            b.setToolTip(f"{_(text)} (Ctrl+{i + 1})")
            self.group.addButton(b, i)
            self.buttons.append(b)
            layout.addWidget(b)
        layout.addStretch(1)
        donate = self._button("heart", _("Donate"))
        donate.setIcon(icons.icon("heart", theme.current().categorical[4], size=22))
        donate.setToolTip(_("ZettelApp is free. Donate on Ko-fi to support it"))
        donate.clicked.connect(on_donate)
        layout.addWidget(donate)
        settings_button = self._button("settings", _("Options"))
        settings_button.setToolTip(_("Options (Ctrl+,)"))
        settings_button.clicked.connect(on_settings)
        layout.addWidget(settings_button)
        self.group.idClicked.connect(on_change)

    def _button(self, glyph: str, text: str) -> QToolButton:
        b = QToolButton()
        b.setObjectName("NavButton")
        b.setIcon(icons.icon(glyph, size=22))
        b.setIconSize(QSize(22, 22))
        b.setText(text)
        b.setAccessibleName(text)
        b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        b.setFixedSize(64, 58)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        return b

    def select(self, index: int) -> None:
        self.buttons[index].setChecked(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.vault: Vault | None = None
        self._data_version: int | None = None
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(QSize(980, 640))
        self.suggestions = SuggestionService(self)
        self.suggestions.ready.connect(self._suggestions_ready)
        self.suggestions.failed.connect(lambda msg: log.warning("Suggestions failed: %s", msg))
        self._configure_suggestions()

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.nav = NavRail(self.show_page, lambda: self.open_options(), self.donate)
        root.addWidget(self.nav)
        right = QWidget()
        right.setObjectName("Page")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.info = InfoBar()
        info_holder = QHBoxLayout()
        info_holder.setContentsMargins(12, 8, 12, 0)
        info_holder.addWidget(self.info)
        right_layout.addLayout(info_holder)
        self.pages = QStackedWidget()
        right_layout.addWidget(self.pages, 1)
        root.addWidget(right, 1)
        self.setCentralWidget(central)

        self.list = NoteListPanel()
        self.editor = NoteEditor(self)
        self.side = SidePanel()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.list)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.side)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([280, 760, 260])  # room for the editor toolbar on one line
        self.splitter.setChildrenCollapsible(False)
        self.list.setMinimumWidth(240)
        self.side.setMinimumWidth(240)
        self.graph = GraphPage(self)
        self.insights = InsightsPage(self)
        self.review = ReviewPage(self)
        self.ask = AskPage(self)
        for page in (self.splitter, self.graph, self.insights, self.review, self.ask):
            self.pages.addWidget(page)

        self.suggest_timer = QTimer(
            self, singleShot=True, interval=900, timeout=self.request_suggestions
        )
        self.refresh_timer = QTimer(
            self, singleShot=True, interval=400, timeout=self._refresh_after_save
        )
        self.watch_timer = QTimer(self, interval=3000, timeout=self._check_external_changes)
        self.watch_timer.start()
        self.alarm_timer = QTimer(self, interval=20000, timeout=self.check_alarms)
        self.alarm_timer.start()
        self._tray = None
        self._tray_note: str | None = None
        self._wire()
        self.quest = Quest(self)
        self._build_menus()
        self.status_vault = label("", "caption")
        self.status_counts = label("", "caption")
        self.statusBar().addPermanentWidget(self._build_mcp_switch())
        self.statusBar().addPermanentWidget(self.status_counts)
        self.statusBar().addPermanentWidget(self.status_vault)
        self._restore_window()
        self.show_page(0)

    # --- wiring -----------------------------------------------------------

    def _wire(self) -> None:
        self.list.noteSelected.connect(self.open_note)
        self.list.newNoteRequested.connect(self.new_note)
        self.list.linkToCurrent.connect(lambda dst, t: self._add_manual_link(dst, t))
        self.list.showInGraph.connect(self.show_local_graph)
        self.list.exportFrom.connect(
            lambda note_id: (self.open_note(note_id), self.export_dialog("subgraph"))
        )
        self.list.trashRequested.connect(self.trash_notes)
        self.list.restoreRequested.connect(self.restore_notes)
        self.list.purgeRequested.connect(self.purge_notes)
        self.list.duplicateRequested.connect(self.duplicate_notes)
        self.list.emptyTrashRequested.connect(self.empty_trash)
        self.editor.saved.connect(lambda _id: self.refresh_timer.start())
        self.editor.contentChanged.connect(self.suggest_timer.start)
        self.editor.openNote.connect(self.open_note)
        self.editor.newNoteRequested.connect(self.new_note)
        self.editor.linkNoteRequested.connect(self.link_note_inline)
        self.editor.mindmapLinkRequested.connect(self._mindmap_link)
        self.editor.statusMessage.connect(lambda m: self.statusBar().showMessage(m, 6000))
        self.side.openNote.connect(self.open_note)
        self.side.acceptSuggestion.connect(self.accept_suggestion)
        self.side.rejectSuggestion.connect(self.reject_suggestion)
        self.side.addLinkRequested.connect(self.add_link_dialog)
        self.side.removeLink.connect(self._remove_link)
        self.side.changeLinkType.connect(self._change_link_type)
        self.side.reverseLink.connect(self._reverse_link)
        self.graph.openNote.connect(self.open_note)
        self.graph.nodeMenuRequested.connect(self._graph_menu)
        self.graph.exportRequested.connect(lambda ids: self.export_dialog("all", preset=ids))
        self.graph.status.connect(lambda m: self.statusBar().showMessage(m, 5000))
        self.insights.openNote.connect(self.open_note)
        self.review.openNote.connect(self.open_note)
        self.review.status.connect(lambda m: self.statusBar().showMessage(m, 8000))
        self.ask.openNote.connect(self.open_note)
        self.ask.configureRequested.connect(lambda: self.open_options("AI assistant"))
        self.ask.status.connect(lambda m: self.statusBar().showMessage(m, 8000))

    def _action(
        self, menu, text: str, slot, shortcut=None, glyph: str | None = None, tip: str = ""
    ) -> QAction:
        action = QAction(_(text), self)
        if glyph:
            action.setIcon(icons.icon(glyph))
        if shortcut is not None:
            action.setShortcut(QKeySequence(shortcut))
        if tip:
            action.setStatusTip(_(tip))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _build_menus(self) -> None:
        bar = self.menuBar()
        f = bar.addMenu(_("&File"))
        self._action(f, "&New Note", self.new_note, QKeySequence.StandardKey.New, "add")
        self._action(f, "New &Vault…", self.new_vault_dialog, None, "folder")
        self._action(
            f, "&Open Vault…", self.open_vault_dialog, QKeySequence.StandardKey.Open, "open"
        )
        self.recent_menu = f.addMenu(_("Open &Recent"))
        f.addSeparator()
        self._action(
            f,
            "&Import…",
            self.import_dialog,
            None,
            "import",
            "Import a ZettelApp archive, JSON or Markdown files",
        )
        self._action(
            f,
            "Import Markdown &Folder…",
            self.import_folder_dialog,
            None,
            None,
            "Import a folder of Markdown files, such as an Obsidian vault",
        )
        self._action(f, "&Export…", lambda: self.export_dialog("all"), "Ctrl+Shift+E", "export")
        f.addSeparator()
        self._action(f, "&Back Up Vault Now", self.backup_now, None, "save")
        self._action(
            f,
            "Show Vault in &File Explorer",
            lambda: self.vault and winintegration.reveal_in_explorer(self.vault.folder),
        )
        f.addSeparator()
        self._action(f, "E&xit", self.close, "Alt+F4")

        e = bar.addMenu(_("&Edit"))
        for text, method, key in (
            (N_("&Undo"), "undo", QKeySequence.StandardKey.Undo),
            (N_("&Redo"), "redo", "Ctrl+Y"),
            (None, None, None),
            (N_("Cu&t"), "cut", QKeySequence.StandardKey.Cut),
            (N_("&Copy"), "copy", QKeySequence.StandardKey.Copy),
            (N_("&Paste"), "paste", QKeySequence.StandardKey.Paste),
            (N_("Select &All"), "selectAll", QKeySequence.StandardKey.SelectAll),
        ):
            if text is None:
                e.addSeparator()
                continue
            action = self._action(
                e, text, lambda _unused=False, m=method: self._edit_command(m), key
            )
            action.setShortcutContext(
                Qt.ShortcutContext.WidgetShortcut
            )  # let editors handle the keys
        e.addSeparator()
        self._action(e, "&Find Notes", self._focus_search, QKeySequence.StandardKey.Find, "search")
        e.addSeparator()
        self._action(e, "&Duplicate Note", self.duplicate_current, "Ctrl+D", "copy")
        self._action(e, "Move Note to &Trash", self.trash_current, "Ctrl+Delete", "delete")

        v = bar.addMenu(_("&View"))
        for i, (glyph, text) in enumerate(NAV):
            self._action(
                v,
                f"&{_(text)}",
                lambda _unused=False, n=i: self.show_page(n),
                f"Ctrl+{i + 1}",
                glyph,
            )
        v.addSeparator()
        self._action(v, "Toggle &Preview", self.editor.cycle_view_mode, "Ctrl+E", "view")
        self._action(v, "&Full Screen", self._toggle_full_screen, "F11", "fit")
        theme_menu = v.addMenu(_("&Theme"))
        group = QActionGroup(self)
        for text, key in (
            (N_("Use &Windows Setting"), "system"),
            (N_("&Light"), "light"),
            (N_("&Dark"), "dark"),
        ):
            action = QAction(_(text), self, checkable=True)
            action.setChecked(settings.get(settings.THEME) == key)
            action.triggered.connect(lambda _unused=False, k=key: self._set_theme(k))
            group.addAction(action)
            theme_menu.addAction(action)

        i = bar.addMenu(_("&Insert"))
        self._action(i, "&Link to Note…", self.link_note_inline, "Ctrl+K", "relationship")
        self._action(i, "&Web Link…", self.editor.insert_web_link, None, "globe")
        self._action(i, "Link to a &File…", self.editor.insert_file_link, None, "folder")
        self._action(i, "&Image…", self.editor.insert_image, "Ctrl+Shift+I", "image")
        self._action(i, "&Zotero Reference…", self.zotero_reference, None, "library")
        self._action(i, "&Mind Map", self.editor.show_mindmap, None, "mindmap")
        self._action(i, "&Flashcard…", self.editor.add_card, "Ctrl+Shift+F", "cards")
        self._action(
            i, "Chec&klist", lambda: self.editor.body.prefix_lines("- [ ] "), None, "checklist"
        )
        self._action(i, "F&ormula…", self.editor.insert_formula, None, "formula")
        self._action(i, "&Alarm…", self.editor.set_alarm, None, "alarm")

        t = bar.addMenu(_("&Tools"))
        self._action(
            t, "Start &Review", lambda: (self.show_page(3), self.review.start_due()), None, "review"
        )
        self._action(t, "&Quiz on This Note's Neighbourhood", self.quiz_current, None)
        self._action(t, "Ask &About This Note…", self.ask_about_current, None, "chat")
        self._action(
            t, "&Sync with Anki", lambda: (self.show_page(3), self.review.sync_anki()), None, "sync"
        )
        t.addSeparator()
        self._action(t, "&Options…", lambda: self.open_options(), "Ctrl+,", "settings")

        h = bar.addMenu(_("&Help"))
        self._action(
            h,
            "&Documentation",
            lambda: QDesktopServices.openUrl(QUrl(DOCS_URL)),
            QKeySequence.StandardKey.HelpContents,
            "help",
        )
        self._action(h, "&Keyboard Shortcuts", lambda: ShortcutsDialog(self).exec(), None)
        h.addSeparator()
        self.quest.add_menu_actions(h)
        h.addSeparator()
        self._action(
            h,
            "ZettelApp &Website",
            lambda: QDesktopServices.openUrl(QUrl(HOMEPAGE_URL)),
            None,
            "globe",
        )
        self._action(
            h,
            "Check for &Updates",
            lambda: QDesktopServices.openUrl(QUrl(RELEASES_URL)),
            None,
            "sync",
        )
        self._action(
            h, "Report an &Issue", lambda: QDesktopServices.openUrl(QUrl(ISSUES_URL)), None
        )
        self._action(
            h,
            "&Donate (Ko-fi)…",
            self.donate,
            None,
            "heart",
            "ZettelApp is free; donations help the roadmap happen sooner",
        )
        h.addSeparator()
        self._action(
            h,
            _("&About {app}").format(app=APP_NAME),
            lambda: AboutDialog(self).exec(),
            None,
            "info",
        )

    def donate(self) -> None:
        QDesktopServices.openUrl(QUrl(SPONSOR_URL))

    def _edit_command(self, method: str) -> None:
        widget = QApplication.focusWidget()
        if widget is not None and hasattr(widget, method):
            getattr(widget, method)()

    def _focus_search(self) -> None:
        self.show_page(0)
        self.list.search.setFocus()
        self.list.search.selectAll()

    def _toggle_full_screen(self) -> None:
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    # --- pages ----------------------------------------------------------------

    def show_page(self, index: int) -> None:
        if index != 0:
            self.editor.flush()
        self.nav.select(index)
        self.pages.setCurrentIndex(index)
        self.graph.set_focus_note(self.current_note_id())

    def show_local_graph(self, note_id: str | None) -> None:
        self.show_page(1)
        self.graph.show_local(note_id)

    def quiz_current(self) -> None:
        note_id = self.current_note_id()
        if note_id is None:
            return
        self.editor.flush()
        ids = subgraph([note_id], self.vault.all_links(), 2)
        self.show_page(3)
        self.review.quiz_notes(ids)

    def ask_about_current(self) -> None:
        self.editor.flush()
        self.show_page(4)
        self.ask.focus_with_scope("subgraph" if self.current_note_id() else "all")

    # --- alarms ---------------------------------------------------------------

    def alarms_changed(self) -> None:
        self.list.refresh()
        self.check_alarms()

    def check_alarms(self) -> None:
        """Pop up a notification for every alarm note whose time has come."""
        if self.vault is None:
            return
        due = self.vault.due_alarms()
        for note in due:
            self.vault.mark_alarm_fired(note.id)
            self._notify_alarm(note)
        if due:
            self.list.refresh()

    def _notify_alarm(self, note) -> None:
        title = note.title or _("Untitled")
        self.info.show_message(_("Alarm: {title}").format(title=title))
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        if self._tray is None:
            self._tray = QSystemTrayIcon(self.windowIcon(), self)
            self._tray.messageClicked.connect(self._open_alarm_note)
            self._tray.show()
        self._tray_note = note.id
        self._tray.showMessage(
            title,
            strip_markdown(note.body)[:140] or _("Time for this note."),
            QSystemTrayIcon.MessageIcon.Information,
            15000,
        )

    def _open_alarm_note(self) -> None:
        if self._tray_note and self.vault is not None:
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self.open_note(self._tray_note)

    # --- vault lifecycle ---------------------------------------------------

    def open_vault(self, folder: str | Path) -> bool:
        try:
            vault = Vault.open(folder)
        except (VaultError, OSError) as exc:
            log.exception("Could not open vault")
            QMessageBox.critical(self, _("Could not open vault"), f"{folder}\n\n{exc}")
            return False
        except Exception as exc:  # noqa: BLE001 - last-resort boundary, never crash the UI
            log.exception("Unexpected error opening vault")
            QMessageBox.critical(self, _("Could not open vault"), f"{folder}\n\n{exc}")
            return False
        self.close_vault()
        self.vault = vault
        self.quest.attach(vault)
        self._data_version = self._read_data_version()
        self._maybe_backup()
        settings.put(settings.LAST_VAULT, str(vault.folder))
        recent = [str(vault.folder)] + [
            p for p in settings.get_list(settings.RECENT_VAULTS) if p != str(vault.folder)
        ]
        settings.put(settings.RECENT_VAULTS, recent[:8])
        self._rebuild_recent()
        self.setWindowTitle(f"{vault.name} - {APP_NAME}")
        self.status_vault.setText(str(vault.folder))
        types = vault.link_types()
        self.side.set_link_types(types)
        self.list.link_types = types
        self.list.set_vault(vault)
        self.suggestions.invalidate()
        self.graph.invalidate()
        self._update_counts()
        self.editor.body.set_titles(list(vault.titles().values()))
        first = self.list.model.rows[0]["id"] if self.list.model.rows else None
        self.open_note(first) if first else self.editor.load(None)
        QTimer.singleShot(1500, self.check_alarms)
        return True

    def close_vault(self) -> None:
        if self.vault is None:
            return
        self.editor.flush()
        self.editor.load(None)
        self.vault.close()
        self.vault = None

    def _rebuild_recent(self) -> None:
        self.recent_menu.clear()
        for path in settings.get_list(settings.RECENT_VAULTS):
            self.recent_menu.addAction(path, lambda p=path: self.open_vault(p))
        self.recent_menu.setEnabled(not self.recent_menu.isEmpty())

    def open_vault_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, _("Open vault"), str(documents_dir()))
        if not folder:
            return
        if (
            not Vault.is_vault(folder)
            and QMessageBox.question(
                self,
                _("Create vault"),
                _("{folder} is not a ZettelApp vault yet. Create a new vault there?").format(
                    folder=folder
                ),
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self._open_vault_with_onboarding(folder)

    def new_vault_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, _("Choose or create an empty folder for the new vault"), str(documents_dir())
        )
        if folder:
            self._open_vault_with_onboarding(folder)

    def open_default_vault(self) -> None:
        last = settings.get(settings.LAST_VAULT, "")
        if last and Vault.is_vault(last) and self.open_vault(last):
            self.quest.start_up()
            return
        self._open_vault_with_onboarding(default_vault_dir())

    def _open_vault_with_onboarding(self, folder: str | Path) -> bool:
        fresh = not Vault.is_vault(folder)
        if not self.open_vault(folder):
            return False
        if fresh:
            self._create_welcome_notes()
        self.quest.start_up()
        return True

    def _create_welcome_notes(self) -> None:
        """Fill a new vault with the starter notes (in the interface language) and open the hub."""
        ids = create_starter_notes(self.vault)
        self.list.refresh()
        self.list.refresh_tags()
        self._update_counts()
        self.editor.body.set_titles(list(self.vault.titles().values()))
        self.open_note(ids[STARTER_HUB])

    def _maybe_backup(self) -> None:
        if not settings.get(settings.BACKUP_ENABLED):
            return
        dest = self._backup_folder()
        if Vault.last_backup_date(dest) != date.today():
            try:
                self.vault.backup(dest, settings.get(settings.BACKUP_KEEP))
            except OSError:
                log.exception("Automatic backup failed")

    def _backup_folder(self) -> Path:
        return backups_dir() / f"{safe_filename(self.vault.name)}-{self.vault.vault_id[:8]}"

    def backup_now(self) -> None:
        if self.vault is None:
            return
        self.editor.flush()
        try:
            path = self.vault.backup(self._backup_folder(), settings.get(settings.BACKUP_KEEP))
        except OSError as exc:
            QMessageBox.warning(self, _("Backup"), str(exc))
            return
        self.notify_file(path, _("Backup saved"))

    def _read_data_version(self) -> int | None:
        try:
            return (
                self.vault.conn.execute("PRAGMA data_version").fetchone()[0] if self.vault else None
            )
        except Exception:  # noqa: BLE001
            return None

    def _check_external_changes(self) -> None:
        """Refresh when another process (e.g. the MCP server) changed the vault."""
        version = self._read_data_version()
        if version is None or version == self._data_version:
            return
        self._data_version = version
        self.list.refresh()
        self.list.refresh_tags()
        self.suggestions.invalidate()
        self.graph.invalidate()
        self._update_counts()
        note_id = self.current_note_id()
        if note_id and not self.editor._dirty:
            note = self.vault.get_note(note_id)
            if note and note.modified != self.editor.note.modified:
                self.editor.load(note)
        self._refresh_side()

    # --- notes ------------------------------------------------------------

    def note_renderer(self):
        from zettelapp.core.render import NoteRenderer
        from zettelapp.ui.preview import math_href

        vault = self.vault

        def title_of(note_id: str) -> str:
            note = vault.get_note(note_id)
            return note.display_title if note else note_id

        return NoteRenderer(
            vault.resolve_title,
            title_of,
            link_types=vault.link_type_map(),
            allow_file_links=True,
            task_links=True,
            math_href=math_href,
        )

    def reveal_file(self, path: str) -> None:
        """Show a linked file in File Explorer, selected. The file is never opened or run."""
        local = local_file_path(path)  # network paths are refused before any disk access
        if local is None:
            return
        target = Path(local)
        if target.exists():
            winintegration.reveal_in_explorer(target)
        elif target.parent.is_dir():
            winintegration.reveal_in_explorer(target.parent)
            self.statusBar().showMessage(
                _("{name} is no longer in that folder.").format(name=target.name), 6000
            )
        else:
            self.statusBar().showMessage(_("File not found: {path}").format(path=local), 6000)

    def current_note_id(self) -> str | None:
        return self.editor.note.id if self.editor.note else None

    def new_note(self, title: str = "") -> None:
        if self.vault is None:
            return
        self.editor.flush()
        if self.list.trash_mode:
            self.list.trash_button.setChecked(False)
            self.list.toggle_trash()
        note = self.vault.create_note(title=title if isinstance(title, str) else "")
        self.list.search.clear()
        self.list.refresh()
        self.show_page(0)
        self.open_note(note.id)
        self.editor.title.setFocus() if not note.title else self.editor.body.setFocus()

    def open_note(self, note_id: str) -> None:
        if self.vault is None or not is_valid_note_id(note_id):
            return
        note = self.vault.get_note(note_id)
        if note is None:
            self.statusBar().showMessage(_("That note no longer exists."), 5000)
            return
        if self.pages.currentIndex() != 0:
            self.show_page(0)
        if note.deleted and not self.list.trash_mode:
            self.list.trash_button.setChecked(True)
            self.list.toggle_trash()
        self.editor.load(note)
        self.list.select(note_id, emit=False)
        self.graph.set_focus_note(note_id)
        self._refresh_side()
        self.side.set_suggestions([], "")
        self.request_suggestions()

    def show_tag(self, tag: str) -> None:
        """List the notes with *tag* (Ctrl+click on a #tag)."""
        if self.vault is None:
            return
        self.editor.flush()  # a #tag typed a moment ago must be saved before it can be listed
        self.list.refresh_tags()
        index = self.list.tag_filter.findData(tag)
        if index < 0:
            self.statusBar().showMessage(_("No notes are tagged #{tag} yet.").format(tag=tag), 5000)
            return
        self.show_page(0)
        self.list.tag_filter.setCurrentIndex(index)

    def _refresh_after_save(self) -> None:
        self.list.refresh()
        self.list.refresh_tags()
        self._update_counts()
        self._refresh_side()
        if self.vault:
            self.editor.body.set_titles(list(self.vault.titles().values()))
            self.editor.tags.set_known_tags([t for t, _unused in self.vault.all_tags()])

    def _refresh_side(self) -> None:
        note = self.editor.note
        if self.vault is None or note is None:
            self.side.set_links("", [], [])
            return
        titles = self.vault.titles()
        out = [(l, titles.get(l.dst, "")) for l in self.vault.links_from(note.id)]
        inc = [(l, titles.get(l.src, "")) for l in self.vault.links_to(note.id)]
        self.side.set_links(note.id, out, inc)

    def _update_counts(self) -> None:
        if self.vault:
            notes, links = self.vault.count_notes(), len(self.vault.all_links())
            self.status_counts.setText(
                n_("{n} note", "{n} notes", notes).format(n=notes)
                + "  ·  "
                + n_("{n} link", "{n} links", links).format(n=links)
            )

    def _targets(self) -> list[str]:
        """The notes the Edit menu acts on: those selected in the list, or the open one."""
        ids = self.list.selected_ids() if self.list.view.hasFocus() else []
        current = self.current_note_id()
        return ids or ([current] if current else [])

    def trash_current(self) -> None:
        if ids := self._targets():
            self.trash_notes(ids)

    def duplicate_current(self) -> None:
        if ids := self._targets():
            self.duplicate_notes(ids)

    def trash_note(self, note_id: str) -> None:
        self.trash_notes([note_id])

    def trash_notes(self, note_ids: list[str]) -> None:
        self.editor.flush()
        notes = [n for i in note_ids if (n := self.vault.get_note(i))]
        with self.vault.transaction():
            for note in notes:
                self.vault.trash_note(note.id)
        if self.current_note_id() in {n.id for n in notes}:
            self.editor.load(None)
        self.list.refresh()
        self._update_counts()
        ids = [n.id for n in notes]
        message = (
            _("“{title}” moved to the Trash.").format(title=notes[0].display_title)
            if len(notes) == 1
            else n_(
                "{n} note moved to the Trash.", "{n} notes moved to the Trash.", len(notes)
            ).format(n=len(notes))
        )
        self.info.show_message(message, "info", _("Undo"), lambda: self.restore_notes(ids))

    def restore_note(self, note_id: str) -> None:
        self.restore_notes([note_id])

    def restore_notes(self, note_ids: list[str]) -> None:
        with self.vault.transaction():
            for note_id in note_ids:
                self.vault.restore_note(note_id)
        self.list.refresh()
        self._update_counts()
        n = len(note_ids)
        self.statusBar().showMessage(
            _("Note restored.")
            if n == 1
            else n_("{n} note restored.", "{n} notes restored.", n).format(n=n),
            4000,
        )

    def purge_note(self, note_id: str) -> None:
        self.purge_notes([note_id])

    def purge_notes(self, note_ids: list[str]) -> None:
        notes = [n for i in note_ids if (n := self.vault.get_note(i))]
        if not notes:
            return
        question = (
            _("Permanently delete “{title}”? This can't be undone.").format(
                title=notes[0].display_title
            )
            if len(notes) == 1
            else n_(
                "Permanently delete {n} note? This can't be undone.",
                "Permanently delete {n} notes? This can't be undone.",
                len(notes),
            ).format(n=len(notes))
        )
        if (
            QMessageBox.warning(
                self,
                _("Delete permanently"),
                question,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            if self.current_note_id() in {n.id for n in notes}:
                self.editor.load(None)
            with self.vault.transaction():
                for note in notes:
                    self.vault.purge_note(note.id)
            self.list.refresh()

    def duplicate_notes(self, note_ids: list[str]) -> None:
        self.editor.flush()
        copies = []
        with self.vault.transaction():
            for note_id in note_ids:
                note = self.vault.get_note(note_id)
                if note is not None:
                    title = _("{title} (copy)").format(title=note.title) if note.title else ""
                    copies.append(self.vault.duplicate_note(note_id, title))
        if not copies:
            return
        self.list.refresh()
        self._update_counts()
        self.suggestions.invalidate()
        self.graph.invalidate()
        self.open_note(copies[0].id)
        self.statusBar().showMessage(
            n_("{n} note duplicated.", "{n} notes duplicated.", len(copies)).format(n=len(copies)),
            4000,
        )

    def empty_trash(self) -> None:
        n = self.vault.count_notes(deleted=True)
        if (
            n
            and QMessageBox.warning(
                self,
                _("Empty Trash"),
                n_(
                    "Permanently delete {n} note? This can't be undone.",
                    "Permanently delete {n} notes? This can't be undone.",
                    n,
                ).format(n=n),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.editor.load(None)
            self.vault.empty_trash()
            self.list.refresh()

    # --- links and suggestions ----------------------------------------------

    def link_note_inline(self) -> None:
        note = self.editor.note
        if note is None:
            return
        dialog = LinkPickerDialog(self.vault, {note.id}, self, _("Link to note"))
        if dialog.exec() and dialog.selected():
            dst, link_type = dialog.selected()
            target = self.vault.get_note(dst)
            title = (
                target.title
                if target and target.title and self.vault.resolve_title(target.title) == dst
                else dst
            )
            self.editor.insert_note_link(title, link_type)

    def add_link_dialog(self) -> None:
        note = self.editor.note
        if note is None:
            return
        exclude = {note.id}
        dialog = LinkPickerDialog(self.vault, exclude, self, _("Add link"))
        if dialog.exec() and dialog.selected():
            dst, link_type = dialog.selected()
            self._add_manual_link(dst, link_type)

    def _add_manual_link(self, dst: str, link_type: str, origin: str = "manual") -> None:
        note = self.editor.note
        if note is None or dst == note.id:
            return
        self.editor.flush()
        self.vault.add_link(note.id, dst, link_type, origin)
        self._refresh_side()
        self.list.refresh()
        self._update_counts()
        self.graph.invalidate()

    def _remove_link(self, src: str, dst: str, link_type: str) -> None:
        self.vault.remove_link(src, dst, link_type)
        self._refresh_side()
        self.graph.invalidate()

    def _change_link_type(self, src: str, dst: str, old: str, new: str) -> None:
        self.vault.change_link_type(src, dst, old, new)
        self._refresh_side()
        self.graph.invalidate()

    def _reverse_link(self, src: str, dst: str, link_type: str) -> None:
        self.vault.reverse_link(src, dst, link_type)
        self._refresh_side()
        self.graph.invalidate()

    def _mindmap_link(self, node_id: str) -> None:
        dialog = LinkPickerDialog(self.vault, set(), self, _("Link idea to note"), show_types=False)
        if dialog.exec() and dialog.selected():
            dst, _unused = dialog.selected()
            note = self.vault.get_note(dst)
            self.editor.mindmap.set_node_note(node_id, dst, note.display_title if note else None)

    def request_suggestions(self) -> None:
        note = self.editor.collect()
        if self.vault is None or note is None or not settings.get(settings.SUGGEST_ENABLED):
            self.side.set_suggestions([], "")
            return
        self.side.set_busy(True)
        data = NoteData(note.id, note.title, note.body, frozenset(note.tags))
        self.suggestions.request(
            self.vault,
            data,
            settings.get(settings.SUGGEST_LIMIT),
            settings.get(settings.SUGGEST_MIN_PROB),
        )

    def _suggestions_ready(self, note_id: str, items: list) -> None:
        if note_id != self.current_note_id():
            return
        note = self.editor.note
        empty = (
            _("Write a little more to get suggestions.")
            if len((note.body or "").split()) < 5
            else _("No strong matches yet. Suggestions improve as your vault grows.")
        )
        self.side.set_suggestions(items, empty)

    def accept_suggestion(self, dst: str, link_type: str) -> None:
        note_id = self.current_note_id()
        if note_id is None:
            return
        self.vault.record_feedback(note_id, dst, 1)
        self._add_manual_link(dst, link_type, origin="suggestion")
        self.statusBar().showMessage(_("Linked. The model will learn from this choice."), 4000)
        self.request_suggestions()

    def reject_suggestion(self, dst: str) -> None:
        note_id = self.current_note_id()
        if note_id is None:
            return
        self.vault.record_feedback(note_id, dst, 0)
        self.statusBar().showMessage(_("Dismissed. The model will learn from this choice."), 4000)
        self.request_suggestions()

    def _graph_menu(self, note_id: str, global_pos) -> None:
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        menu.addAction(icons.icon("open"), _("Open note"), lambda: self.open_note(note_id))
        menu.addAction(
            icons.icon("graph"), _("Show local graph"), lambda: self.graph.show_local(note_id)
        )
        menu.addAction(
            icons.icon("review"),
            _("Quiz on this neighbourhood"),
            lambda: (self.open_note(note_id), self.quiz_current()),
        )
        menu.addAction(
            icons.icon("export"),
            _("Export with linked notes…"),
            lambda: (self.open_note(note_id), self.export_dialog("subgraph")),
        )
        menu.exec(global_pos.toPoint() if hasattr(global_pos, "toPoint") else global_pos)

    def zotero_reference(self) -> None:
        """Cite a Zotero item in the open note, or start a literature note from it."""
        from zettelapp.core.zotero import citation_markdown, literature_note
        from zettelapp.ui.zotero_dialog import ZoteroDialog

        if self.vault is None:
            return
        dialog = ZoteroDialog(self)
        if not dialog.exec() or dialog.result_item is None:
            return
        item = dialog.result_item
        if dialog.action == "cite" and self.editor.note is not None:
            self.editor.body.textCursor().insertText(citation_markdown(item))
            self.editor.body.setFocus()
            return
        title, body, tags, url = literature_note(item, dialog.pdf_key)
        self.editor.flush()
        note = self.vault.create_note(title=title, body=body, tags=tags, url=url)
        self.list.refresh()
        self.list.refresh_tags()
        self.open_note(note.id)
        self.statusBar().showMessage(_("Literature note created from Zotero."), 5000)

    # --- scope, export and import -----------------------------------------------

    def resolve_scope(self, mode: str, depth: int, tag: str | None) -> set[str]:
        if self.vault is None:
            return set()
        if mode == "subgraph" and self.current_note_id():
            return subgraph([self.current_note_id()], self.vault.all_links(), depth)
        if mode == "tag" and tag:
            return self.vault.notes_with_tags([tag])
        return {n.id for n in self.vault.all_notes()}

    def export_dialog(
        self, scope: str = "all", fmt: str | None = None, preset: set[str] | None = None
    ) -> None:
        if self.vault is None:
            return
        self.editor.flush()
        resolve = (lambda *_unused: set(preset)) if preset else self.resolve_scope
        dialog = ExportDialog(
            self.vault,
            self.current_note_id(),
            resolve,
            self,
            initial_scope=scope if self.current_note_id() or scope != "subgraph" else "all",
        )
        if fmt:
            for button in dialog.group.buttons():
                if button.property("fmt") == fmt:
                    button.setChecked(True)
        if preset:
            dialog.scope.setEnabled(False)
        if not dialog.exec():
            return
        dest = dialog.destination()
        if dest is None:
            return
        ids, kind, folder = dialog.note_ids(), dialog.fmt(), self.vault.folder
        deck = settings.get(settings.ANKI_DECK)
        self.statusBar().showMessage(_("Exporting…"))

        def work():
            reader = Vault.open(folder, readonly=True)  # own connection for this thread
            try:
                return run_export(reader, kind, ids, dest, deck_name=deck)
            finally:
                reader.close()

        def done(result) -> None:
            items = [
                n_("{n} note", "{n} notes", result.notes).format(n=result.notes),
                n_("{n} link", "{n} links", result.links).format(n=result.links),
            ]
            if result.cards:
                items.append(
                    n_("{n} flashcard", "{n} flashcards", result.cards).format(n=result.cards)
                )
            self.notify_file(result.path, _("Exported {items}").format(items=", ".join(items)))

        run_task(
            work,
            on_done=done,
            on_error=lambda msg: QMessageBox.warning(self, _("Export failed"), msg),
        )

    def import_dialog(self) -> None:
        path, _unused = QFileDialog.getOpenFileName(
            self,
            _("Import"),
            str(documents_dir()),
            _(
                "Supported files (*.zip *.json *.md);;ZettelApp archive or Markdown (*.zip);;JSON (*.json);;Markdown (*.md)"
            ),
        )
        if path:
            self._import(path)

    def import_folder_dialog(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, _("Import a folder of Markdown files"), str(documents_dir())
        )
        if folder:
            self._import(folder)

    def _import(self, path: str) -> None:
        if self.vault is None:
            return
        self.editor.flush()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            result = import_path(self.vault, path)
        except (UnsafeInputError, ValueError, OSError) as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, _("Import failed"), str(exc))
            return
        QApplication.restoreOverrideCursor()
        self.list.refresh()
        self.list.refresh_tags()
        self._update_counts()
        self.suggestions.invalidate()
        self.graph.invalidate()
        items = [
            n_("{n} note", "{n} notes", result.notes).format(n=result.notes),
            n_("{n} link", "{n} links", result.links).format(n=result.links),
            n_("{n} flashcard", "{n} flashcards", result.cards).format(n=result.cards),
            n_("{n} image", "{n} images", result.images).format(n=result.images),
        ]
        text = _("Imported {items}.").format(items=", ".join(items))
        if result.skipped:
            text += " " + n_(
                "{n} unchanged note was skipped.",
                "{n} unchanged notes were skipped.",
                result.skipped,
            ).format(n=result.skipped)
        if result.warnings:
            skipped = "\n• ".join(result.warnings[:15])
            QMessageBox.information(
                self,
                _("Import finished"),
                f"{text}\n\n" + _("Some items were skipped:") + f"\n• {skipped}",
            )
        else:
            self.info.show_message(text, "success")

    def notify_file(self, path, text: str) -> None:
        self.statusBar().clearMessage()
        self.info.show_message(
            f"{text}: {Path(path).name}",
            "success",
            _("Show in folder"),
            lambda: winintegration.reveal_in_explorer(path),
        )

    # --- settings -------------------------------------------------------------

    def autosave_ms(self) -> int:
        return settings.get(settings.AUTOSAVE_MS)

    def _configure_suggestions(self) -> None:
        enabled = settings.get_list(settings.SUGGEST_FEATURES) or [f.key for f in FEATURES]
        self.suggestions.configure(enabled, settings.get(settings.SUGGEST_PRIOR))

    def open_options(self, page: str = "General") -> None:
        self.editor.flush()
        OptionsDialog(self, page).exec()

    def _set_theme(self, mode: str) -> None:
        settings.put(settings.THEME, mode)
        self.settings_changed()

    def settings_changed(self) -> None:
        theme.apply_theme(QApplication.instance(), settings.get(settings.THEME))
        winintegration.set_window_frame_dark(int(self.winId()), theme.current().dark)
        self.editor.body.set_font_size(settings.get(settings.EDITOR_FONT_SIZE))
        self.editor.refresh_style()
        self._configure_suggestions()
        if self.vault:
            types = self.vault.link_types()
            self.side.set_link_types(types)
            self.list.link_types = types
            self._refresh_side()
        self.graph.invalidate()
        if self.pages.currentIndex() == 1:
            self.graph.refresh()
        self.ask.refresh()
        self.request_suggestions()

    # --- single instance / protocol handler ------------------------------------

    def handle_message(self, message: dict) -> None:
        self.showNormal() if self.isMinimized() else None
        self.raise_()
        self.activateWindow()
        note_id = message.get("open")
        if isinstance(note_id, str) and is_valid_note_id(note_id):
            self.open_note(note_id)

    # --- window state -----------------------------------------------------------

    def _restore_window(self) -> None:
        store = settings.store()
        geometry = store.value("window/geometry")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        else:
            self.resize(1440, 900)
        split = store.value("window/splitter")
        if isinstance(split, QByteArray):
            self.splitter.restoreState(split)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        winintegration.set_window_frame_dark(int(self.winId()), theme.current().dark)

    # --- updates --------------------------------------------------------------

    def check_for_updates(self) -> None:
        """Quietly ask the website for the latest version; failures never show anything."""
        if settings.get(settings.UPDATE_CHECK):
            run_task(
                available_update, on_done=self._show_update_notice, on_error=lambda *_unused: None
            )

    def _show_update_notice(self, version: str | None) -> None:
        if (
            not version
            or version == settings.get(settings.UPDATE_NOTIFIED)
            or not settings.get(settings.UPDATE_CHECK)
        ):
            return
        settings.put(settings.UPDATE_NOTIFIED, version)  # each version is announced once
        self.update_notice = UpdateNotice(self, version)
        self.update_notice.show()

    # --- MCP switch ---------------------------------------------------------

    def _build_mcp_switch(self) -> QWidget:
        """The status-bar switch that lets MCP clients (AI agents) reach the vault.

        Always off when ZettelApp starts; the state is never saved."""
        self.mcp_switch = McpSwitch()
        self.mcp_toggle = ToggleSwitch()
        self.mcp_toggle.setAccessibleName(_("Let AI agents use ZettelApp through MCP"))
        self.mcp_toggle.toggled.connect(self._set_mcp)
        self.mcp_label = label(_("MCP off"), "caption")
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 10, 0)
        row.setSpacing(4)
        row.addWidget(self.mcp_toggle)
        row.addWidget(self.mcp_label)
        box.setToolTip(
            _(
                "MCP lets AI agents such as Claude Desktop or Claude Code search and read your notes.\n"
                "It works only while ZettelApp is open and this switch is on. The switch is off\n"
                "whenever ZettelApp starts, and the agent's connection stops when you switch it\n"
                "off or close ZettelApp. Set it up in Tools ▸ Options ▸ MCP server."
            )
        )
        return box

    def _set_mcp(self, on: bool) -> None:
        try:
            if on:
                self.mcp_switch.on()
            else:
                self.mcp_switch.off()
        except OSError:
            log.exception("Could not switch MCP access")
            self.mcp_toggle.blockSignals(True)
            self.mcp_toggle.setChecked(self.mcp_switch.is_on)
            self.mcp_toggle.blockSignals(False)
            self.statusBar().showMessage(_("Could not switch MCP on."), 6000)
            return
        self.mcp_label.setText(_("MCP on") if on else _("MCP off"))
        if on:
            self.statusBar().showMessage(
                _(
                    "MCP is on: AI agents connected to ZettelApp can read and add to your notes "
                    "until you switch it off or close ZettelApp."
                )
                if settings.get(settings.MCP_ALLOW_WRITES)
                else _(
                    "MCP is on: AI agents connected to ZettelApp can read your notes until you "
                    "switch it off or close ZettelApp."
                ),
                8000,
            )
        else:
            self.statusBar().showMessage(
                _("MCP is off: AI agents can no longer reach your notes."), 5000
            )

    def closeEvent(self, event) -> None:  # noqa: N802
        self.mcp_toggle.setChecked(False)  # agents lose access the moment the app closes
        self.editor.flush()
        store = settings.store()
        store.setValue("window/geometry", self.saveGeometry())
        store.setValue("window/splitter", self.splitter.saveState())
        store.sync()
        self.close_vault()
        if self._tray is not None:
            self._tray.hide()
        super().closeEvent(event)
