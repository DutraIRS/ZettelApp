"""The note editor: title, tags, source link, Markdown body, mind map and flashcards."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from PySide6.QtCore import QLocale, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from zettelapp.core.models import Flashcard, Note, new_mindmap_node
from zettelapp.core.security import (
    UnsafeInputError,
    is_openable_url,
    local_file_path,
    normalize_source_url,
    normalize_web_url,
)
from zettelapp.core.textutil import extract_hashtags, find_tasks, strip_markdown
from zettelapp.i18n import _, n_
from zettelapp.ui import icons, theme
from zettelapp.ui.dialogs import AlarmDialog, CardDialog, FormulaDialog, TextPromptDialog
from zettelapp.ui.markdown_editor import MarkdownEditor, referenced_assets
from zettelapp.ui.mindmap import MindMapView
from zettelapp.ui.preview import NotePreview
from zettelapp.ui.widgets import TagEditor, accent_button, label, tool_button


def friendly_time(iso: str) -> str:
    try:
        when = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    delta = datetime.now(UTC) - when
    seconds = delta.total_seconds()
    if seconds < 60:
        return _("just now")
    if seconds < 3600:
        minutes = int(seconds // 60)
        return n_("{n} min ago", "{n} min ago", minutes).format(n=minutes)
    if seconds < 86400:
        hours = int(seconds // 3600)
        return n_("{n} h ago", "{n} h ago", hours).format(n=hours)
    return QLocale().toString(when.astimezone().date(), "d MMM yyyy")


class NoteEditor(QWidget):
    saved = Signal(str)
    contentChanged = Signal()
    openNote = Signal(str)
    newNoteRequested = Signal(str)
    linkNoteRequested = Signal()
    mindmapLinkRequested = Signal(str)
    statusMessage = Signal(str)

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.note: Note | None = None
        self._loading = False
        self._dirty = False
        self.setObjectName("EditorPane")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.autosave = QTimer(self, singleShot=True, timeout=self.flush)
        self.preview_timer = QTimer(
            self, singleShot=True, interval=350, timeout=self._refresh_preview
        )
        self.inline_tag_timer = QTimer(
            self, singleShot=True, interval=400, timeout=self._refresh_inline_tags
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.empty = QWidget()
        empty_layout = QVBoxLayout(self.empty)
        empty_layout.addStretch(1)
        icon = QLabel()
        icon.setPixmap(icons.icon("notes", theme.current().text_muted, 48).pixmap(48, 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon)
        msg = label(_("Select a note or create a new one"), "heading")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(msg)
        hint = label(
            _("One idea per note. Link it to others to grow your Zettelkasten."), "secondary"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hint)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(accent_button(_("New note"), lambda: self.window.new_note(), "add"))
        button_row.addStretch(1)
        empty_layout.addLayout(button_row)
        empty_layout.addStretch(2)

        self.content = QWidget()
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(28, 14, 28, 10)
        layout.setSpacing(6)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.empty)
        self.stack.addWidget(self.content)
        outer.addWidget(self.stack)

        # Toolbar --------------------------------------------------------
        bar = QHBoxLayout()
        bar.setSpacing(2)
        bar.addWidget(
            tool_button("trash", _("Move note to Trash"), lambda: self.window.trash_current())
        )
        bar.addSpacing(6)
        self.fmt_buttons = [
            tool_button("bold", _("Bold (Ctrl+B)"), lambda: self.body.wrap_selection("**")),
            tool_button("italic", _("Italic (Ctrl+I)"), lambda: self.body.wrap_selection("*")),
            tool_button("heading", _("Heading"), lambda: self.body.prefix_lines("## ")),
            tool_button("bullets", _("Bulleted list"), lambda: self.body.prefix_lines("- ")),
            tool_button("checklist", _("Checklist"), lambda: self.body.prefix_lines("- [ ] ")),
            tool_button("code", _("Code"), lambda: self.body.wrap_selection("`")),
            tool_button("formula", _("Insert formula (LaTeX)"), self.insert_formula),
        ]
        for b in self.fmt_buttons:
            bar.addWidget(b)
        bar.addSpacing(10)
        bar.addWidget(
            tool_button("relationship", _("Link to note (Ctrl+K)"), self.linkNoteRequested.emit)
        )
        bar.addWidget(tool_button("folder", _("Link to a file"), self.insert_file_link))
        bar.addWidget(tool_button("globe", _("Insert web link"), self.insert_web_link))
        bar.addWidget(tool_button("image", _("Insert image (Ctrl+Shift+I)"), self.insert_image))
        bar.addWidget(
            tool_button(
                "library", _("Cite a Zotero reference"), lambda: self.window.zotero_reference()
            )
        )
        bar.addWidget(tool_button("mindmap", _("Add mind map"), self.show_mindmap))
        bar.addWidget(tool_button("cards", _("Add flashcard (Ctrl+Shift+F)"), self.add_card))
        bar.addWidget(tool_button("alarm", _("Set an alarm for this note"), self.set_alarm))
        bar.addStretch(1)
        self.mode_group = QButtonGroup(self)
        for i, (name, tip) in enumerate(
            (("edit", _("Edit")), ("view", _("Split view")), ("document", _("Preview")))
        ):
            b = tool_button(name, _("{tip} (Ctrl+E cycles)").format(tip=tip), checkable=True)
            self.mode_group.addButton(b, i)
            bar.addWidget(b)
        self.mode_group.idClicked.connect(self.set_view_mode)
        more = QToolButton()
        more.setIcon(icons.icon("more"))
        more.setToolTip(_("More"))
        more.setProperty("noindicator", True)
        more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.more_menu = QMenu(more)
        more.setMenu(self.more_menu)
        bar.addWidget(more)
        layout.addLayout(bar)

        # Title, metadata and picture ------------------------------------
        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        self.title = QLineEdit()
        self.title.setObjectName("TitleEdit")
        self.title.setPlaceholderText(_("Untitled"))
        self.title.setAccessibleName(_("Title"))
        self.title.textEdited.connect(self._edited)
        self.title.returnPressed.connect(lambda: self.body.setFocus())
        titles.addWidget(self.title)
        self.meta = label("", "caption")
        self.meta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        titles.addWidget(self.meta)
        head.addLayout(titles, 1)
        self.picture = QLabel()
        self.picture.setFixedSize(QSize(120, 80))
        self.picture.setScaledContents(False)
        self.picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture.setToolTip(_("Note picture (shown in the graph). Right-click to remove."))
        self.picture.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.picture.customContextMenuRequested.connect(self._picture_menu)
        head.addWidget(self.picture)
        layout.addLayout(head)

        self.tags = TagEditor()
        self.tags.tagsChanged.connect(lambda _unused: self._edited())
        layout.addWidget(self.tags)

        url_row = QHBoxLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText(_("Source link (optional): https://… or a zotero:// item link"))
        self.url.setAccessibleName(_("Source link"))
        self.url.addAction(
            icons.icon("globe", theme.current().text_muted, 16),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.url.editingFinished.connect(self._url_finished)
        self.url.textEdited.connect(self._edited)
        url_row.addWidget(self.url, 1)
        self.open_url = tool_button("open_external", _("Open the source link"), self._open_url)
        url_row.addWidget(self.open_url)
        layout.addLayout(url_row)

        # Tabs -------------------------------------------------------------
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.body = MarkdownEditor(self._store_image)
        self.body.resolve_note = self._resolve
        self.body.linkActivated.connect(self._follow_link)
        self.body.textChanged.connect(self._edited)
        self.body.textChanged.connect(self.inline_tag_timer.start)
        self.body.imageError.connect(
            lambda msg: QMessageBox.warning(self, _("Image not added"), msg)
        )
        self.body.fileLinkError.connect(self.statusMessage)
        self.preview = NotePreview(
            lambda name: self.window.vault.asset_path(name) if self.window.vault else None
        )
        self.preview.noteRequested.connect(self.openNote)
        self.preview.newNoteRequested.connect(self.newNoteRequested)
        self.preview.fileRequested.connect(lambda path: self.window.reveal_file(path))
        self.preview.hovered.connect(self.statusMessage)
        self.preview.taskToggled.connect(self._toggle_task)
        self.preview.image_actions = self._image_actions
        self.body.image_actions = self._image_actions
        self.split = QSplitter(Qt.Orientation.Horizontal)
        self.split.addWidget(self.body)
        self.split.addWidget(self.preview)
        self.split.setChildrenCollapsible(False)
        self.tabs.addTab(self.split, icons.icon("notes"), _("Note"))

        mind = QWidget()
        mind_layout = QVBoxLayout(mind)
        mind_layout.setContentsMargins(0, 6, 0, 0)
        mind_bar = QHBoxLayout()
        self.mindmap = MindMapView()
        self.mindmap.changed.connect(self._mindmap_changed)
        self.mindmap.openNote.connect(self.openNote)
        self.mindmap.linkNoteRequested.connect(self.mindmapLinkRequested)
        mind_bar.addWidget(
            tool_button(
                "add", _("Add child idea (Tab)"), self.mindmap.add_child, text=_("Add idea")
            )
        )
        mind_bar.addWidget(
            tool_button(
                "relationship",
                _("Build a mind map from this note's links"),
                self.mindmap_from_links,
                text=_("From links"),
            )
        )
        mind_bar.addWidget(
            tool_button("delete", _("Delete selected idea (Del)"), self.mindmap.delete_selected)
        )
        mind_bar.addStretch(1)
        mind_bar.addWidget(tool_button("fit", _("Fit to window"), self.mindmap.fit))
        export = QToolButton()
        export.setIcon(icons.icon("export"))
        export.setToolTip(_("Export mind map"))
        export.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        export_menu = QMenu(export)
        export_menu.addAction(_("PNG image…"), lambda: self._export_mindmap("png"))
        export_menu.addAction(_("SVG image…"), lambda: self._export_mindmap("svg"))
        export_menu.addAction(_("FreeMind / XMind (.mm)…"), lambda: self._export_mindmap("mm"))
        export.setMenu(export_menu)
        mind_bar.addWidget(export)
        mind_layout.addLayout(mind_bar)
        mind_layout.addWidget(self.mindmap, 1)
        mind_layout.addWidget(
            label(
                _(
                    "Tab adds a child, Enter a sibling, F2 renames, Del removes. "
                    "Right-click an idea to link it to a note."
                ),
                "caption",
            )
        )
        self.tabs.addTab(mind, icons.icon("mindmap"), _("Mind map"))

        cards = QWidget()
        cards_layout = QVBoxLayout(cards)
        cards_layout.setContentsMargins(0, 8, 0, 0)
        cards_bar = QHBoxLayout()
        cards_bar.addWidget(
            tool_button("add", _("Add flashcard"), self.add_card, text=_("Add flashcard"))
        )
        cards_bar.addWidget(tool_button("edit", _("Edit flashcard"), self.edit_card))
        cards_bar.addWidget(tool_button("delete", _("Delete flashcard"), self.delete_card))
        cards_bar.addStretch(1)
        cards_layout.addLayout(cards_bar)
        self.cards = QListWidget()
        self.cards.setAccessibleName(_("Flashcards"))
        self.cards.setWordWrap(True)
        self.cards.itemDoubleClicked.connect(lambda _unused: self.edit_card())
        cards_layout.addWidget(self.cards, 1)
        cards_layout.addWidget(
            label(
                _(
                    "Cards also come from the note text: write “Q: …” then “A: …”, or "
                    "hide words with {{c1::cloze}}."
                ),
                "caption",
                wrap=True,
            )
        )
        self.tabs.addTab(cards, icons.icon("cards"), _("Flashcards"))
        layout.addWidget(self.tabs, 1)

        self._build_more_menu()
        self.set_view_mode(1)

    # --- loading and saving -------------------------------------------------

    def load(self, note: Note | None) -> None:
        self.flush()
        self.note = note
        self.stack.setCurrentIndex(1 if note else 0)
        if note is None:
            return
        self._loading = True
        self.preview.set_renderer(self.window.note_renderer())
        self.title.setText(note.title)
        self.body.setPlainText(note.body)
        self.url.setText(note.url)
        self.tags.set_tags(self.window.vault.manual_tags(note.id), extract_hashtags(note.body))
        self.tags.set_known_tags([t for t, _unused in self.window.vault.all_tags()])
        self.mindmap.set_mindmap(note.mindmap)
        self._loading = False
        self._dirty = False
        self._refresh_meta()
        self._refresh_picture()
        self._refresh_cards()
        self._refresh_preview()
        self.body.document().clearUndoRedoStacks()
        if not note.title:
            self.title.setFocus()

    def _edited(self, *_args) -> None:
        if self._loading or self.note is None:
            return
        self._dirty = True
        self.autosave.start(self.window.autosave_ms())
        self.preview_timer.start()
        self.contentChanged.emit()

    def collect(self) -> Note | None:
        """The note with the editor's current (possibly unsaved) contents."""
        if self.note is None:
            return None
        self.note.title = self.title.text().strip()
        self.note.body = self.body.toPlainText()
        self.note.tags = sorted(set(self.tags.tags()) | set(extract_hashtags(self.note.body)))
        url = self.url.text().strip()
        self.note.url = (normalize_source_url(url) or "") if url else ""
        if self.note.image and self.note.image not in referenced_assets(self.note.body):
            self.note.image = ""
            self._refresh_picture()
        return self.note

    def flush(self) -> None:
        self.autosave.stop()
        if not self._dirty or self.note is None or self.window.vault is None:
            return
        note = self.collect()
        self.window.vault.save_note(note, manual_tags=self.tags.tags())
        self._dirty = False
        self._refresh_meta()
        self._refresh_cards()
        self.saved.emit(note.id)

    def _refresh_meta(self) -> None:
        n = self.note
        words = len(strip_markdown(n.body).split())
        alarm = ""
        if n.alarm:
            try:
                when = datetime.fromisoformat(n.alarm).astimezone()
                alarm = "  ·  " + _("Alarm {when}").format(
                    when=QLocale().toString(
                        when.replace(tzinfo=None), QLocale.FormatType.ShortFormat
                    )
                )
            except ValueError:
                alarm = ""
        self.meta.setText(
            _(
                "Created {friendly_time}  ·  Edited {friendly_time2}  ·  {words} words  ·  ID {id}"
            ).format(
                friendly_time=friendly_time(n.created),
                friendly_time2=friendly_time(n.modified),
                words=words,
                id=n.id,
            )
            + alarm
        )

    def _refresh_preview(self) -> None:
        if self.note is not None and self.preview.isVisible():
            self.preview.show_markdown(self.body.toPlainText())

    def _refresh_inline_tags(self) -> None:
        if self.note is not None:
            self.tags.set_inline_tags(extract_hashtags(self.body.toPlainText()))

    def refresh_style(self) -> None:
        self.body.highlighter.rebuild()
        self._refresh_preview()
        self.mindmap.rebuild()

    # --- following links ------------------------------------------------------

    def _resolve(self, target: str) -> str | None:
        return self.window.vault.resolve_title(target) if self.window.vault else None

    def _follow_link(self, kind: str, target: str) -> None:
        if kind == "note":
            note_id = self._resolve(target)
            if note_id:
                self.openNote.emit(note_id)
            else:
                self.newNoteRequested.emit(target)
        elif kind == "tag":
            self.window.show_tag(target)
        elif local_file_path(target):  # shown in File Explorer, never opened or run
            self.window.reveal_file(target)
        elif is_openable_url(target):  # web pages, e-mail and Zotero items only
            QDesktopServices.openUrl(QUrl(target))
        else:
            self.statusMessage.emit(
                _("Only web, e-mail, Zotero and local file links can be opened.")
            )

    # --- view modes -----------------------------------------------------

    def set_view_mode(self, mode: int) -> None:
        self.mode_group.button(mode).setChecked(True)
        self.body.setVisible(mode in (0, 1))
        self.preview.setVisible(mode in (1, 2))
        for b in self.fmt_buttons:
            b.setEnabled(mode != 2)
        if mode == 1:
            self.split.setSizes([1, 1])
        self._refresh_preview()
        self.tabs.setCurrentIndex(0)

    def cycle_view_mode(self) -> None:
        self.set_view_mode((self.mode_group.checkedId() + 1) % 3)

    # --- insertions -----------------------------------------------------

    def _store_image(self, data: bytes, name: str) -> str:
        asset = self.window.vault.add_image(data, name)
        if self.note is not None and not self.note.image:
            self.note.image = asset
            self._refresh_picture()
        self._edited()
        return asset

    def insert_image(self) -> None:
        if self.note is None:
            return
        path, _unused = QFileDialog.getOpenFileName(
            self, _("Insert image"), "", _("Images (*.png *.jpg *.jpeg *.gif *.webp *.bmp)")
        )
        if not path:
            return
        try:
            asset = self.window.vault.add_image_file(path)
        except (UnsafeInputError, OSError) as exc:
            QMessageBox.warning(self, _("Image not added"), str(exc))
            return
        if not self.note.image:
            self.note.image = asset
            self._refresh_picture()
        name = path.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
        self.body.insert_block(f"![{name}](asset:{asset})\n")

    # --- checklists, formulas, alarms, title image --------------------------------

    def _toggle_task(self, index: int) -> None:
        text = self.body.toPlainText()
        tasks = find_tasks(text)
        if not 0 <= index < len(tasks):
            return
        start, end, checked = tasks[index]
        utf16 = lambda s: len(s.encode("utf-16-le")) // 2  # noqa: E731 - Qt positions
        cursor = QTextCursor(self.body.document())
        cursor.setPosition(utf16(text[:start]))
        cursor.setPosition(utf16(text[:end]), QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText("[ ]" if checked else "[x]")

    def insert_formula(self) -> None:
        if self.note is None:
            return
        selected = self.body.textCursor().selectedText().strip("$ ")
        dialog = FormulaDialog(self, selected)
        if dialog.exec():
            _latex, display = dialog.value()
            if display:
                self.body.insert_block(dialog.markdown() + "\n")
            else:
                self.body.textCursor().insertText(dialog.markdown())
            self.body.setFocus()

    def set_alarm(self) -> None:
        if self.note is None:
            return
        dialog = AlarmDialog(self, self.note.alarm)
        if not dialog.exec():
            return
        self.note.alarm = "" if dialog.removed else dialog.iso()
        self._dirty = True
        self.flush()
        self.window.alarms_changed()

    def _image_actions(self, asset: str) -> list[tuple[str, Callable[[], None]]]:
        if self.note is None:
            return []
        if self.note.image == asset:
            return [(_("Remove title image"), self._remove_picture)]
        return [(_("Use as title image"), lambda: self._set_picture(asset))]

    def _set_picture(self, asset: str) -> None:
        if self.note:
            self.note.image = asset
            self._refresh_picture()
            self._edited()

    def insert_file_link(self) -> None:
        """Link a file where it is (nothing is copied); clicking shows it in File Explorer."""
        if self.note is None:
            return
        path, _unused = QFileDialog.getOpenFileName(self, _("Link to a file"))
        if path:
            self.body.insert_file_link(path)

    def insert_web_link(self) -> None:
        selected = self.body.textCursor().selectedText()
        dialog = TextPromptDialog(
            _("Insert web link"), _("Address (http, https or mailto):"), "", self, _("Insert")
        )
        if dialog.exec():
            url = normalize_web_url(dialog.value())
            if url is None:
                QMessageBox.warning(
                    self, _("Link not inserted"), _("Only http(s) and mailto links are allowed.")
                )
                return
            self.body.textCursor().insertText(f"[{selected or url}]({url})")

    def insert_note_link(self, title: str, link_type: str = "related") -> None:
        prefix = "" if link_type == "related" else f"{link_type}::"
        self.body.textCursor().insertText(f"{prefix}[[{title}]]")
        self.body.setFocus()

    def show_mindmap(self) -> None:
        if self.note is None:
            return
        self.tabs.setCurrentIndex(1)
        self.mindmap.ensure_root(self.title.text())
        self.mindmap.setFocus()

    def mindmap_from_links(self) -> None:
        if self.note is None:
            return
        from zettelapp.core.models import MAX_MINDMAP_NODES

        vault = self.window.vault
        links = vault.links_from(self.note.id) + vault.links_to(self.note.id)
        if not links:
            self.statusMessage.emit(_("This note has no links yet. Link it to other notes first."))
            return
        types = vault.link_type_map()
        titles = vault.titles()
        root = new_mindmap_node(self.title.text() or "Untitled", self.note.id)
        groups: dict[str, dict] = {}
        seen = {self.note.id}
        # Storage refuses maps with more than MAX_MINDMAP_NODES nodes, so the root, the link
        # types and every linked note get room first, then the notes those link to.
        room = MAX_MINDMAP_NODES - 1
        left_out = 0
        linked: list[tuple[dict, list[str]]] = []
        for link in links:
            outgoing = link.src == self.note.id
            other = link.dst if outgoing else link.src
            lt = types.get(link.type)
            verb = lt.label_for(outgoing) if lt else link.type
            second_level = sorted(vault.neighbors(other) - seen - {other})[:6]
            seen.add(other)
            cost = 1 if verb in groups else 2  # a new link type needs its branch too
            if cost > room:
                left_out += 1 + len(second_level)
                continue
            room -= cost
            branch = groups.setdefault(verb, new_mindmap_node(verb))
            child = new_mindmap_node(titles.get(other) or "Untitled", other)
            branch["children"].append(child)
            linked.append((child, second_level))
        for child, second_level in linked:
            fit = second_level[:room]
            for second in fit:
                child["children"].append(new_mindmap_node(titles.get(second) or "Untitled", second))
            room -= len(fit)
            left_out += len(second_level) - len(fit)
        root["children"] = list(groups.values())
        if (
            self.note.mindmap
            and QMessageBox.question(
                self,
                _("Replace mind map"),
                _("Replace the current mind map with one built from this note's links?"),
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.mindmap.set_mindmap(root)
        self._mindmap_changed(root)
        self.tabs.setCurrentIndex(1)
        if left_out:
            self.statusMessage.emit(
                n_(
                    "Left out {n} link: a mind map holds at most {limit} ideas.",
                    "Left out {n} links: a mind map holds at most {limit} ideas.",
                    left_out,
                ).format(n=left_out, limit=MAX_MINDMAP_NODES)
            )

    def _mindmap_changed(self, data) -> None:
        if self.note is None:
            return
        self.note.mindmap = data
        self._edited()

    def _export_mindmap(self, kind: str) -> None:
        if self.note is None or not self.note.mindmap:
            self.statusMessage.emit(_("This note has no mind map to export."))
            return
        from zettelapp.core.export import export_mindmap
        from zettelapp.core.security import safe_filename

        filters = {
            "png": _("PNG image (*.png)"),
            "svg": _("SVG image (*.svg)"),
            "mm": _("FreeMind mind map (*.mm)"),
        }
        name = safe_filename(self.title.text() or _("Mind map")) + "." + kind
        path, _unused = QFileDialog.getSaveFileName(self, _("Export mind map"), name, filters[kind])
        if not path:
            return
        if kind == "png":
            self.mindmap.render_image().save(path, "PNG")
        elif kind == "svg":
            self.mindmap.render_svg(path)
        else:
            export_mindmap(self.note.mindmap, path)
        self.window.notify_file(path, _("Mind map exported"))

    # --- picture ------------------------------------------------------------

    def _refresh_picture(self) -> None:
        path = (
            self.window.vault.asset_path(self.note.image) if self.note and self.note.image else None
        )
        self.picture.setVisible(path is not None)
        if path is not None:
            px = QPixmap(str(path)).scaled(
                self.picture.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.picture.setPixmap(px)

    def _picture_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.addAction(_("Remove note picture"), self._remove_picture)
        menu.exec(self.picture.mapToGlobal(pos))

    def _remove_picture(self) -> None:
        if self.note:
            self.note.image = ""
            self._refresh_picture()
            self._edited()

    # --- source link --------------------------------------------------------

    def _url_finished(self) -> None:
        text = self.url.text().strip()
        if text and normalize_source_url(text) is None:
            self.statusMessage.emit(
                _("Use an http(s), mailto or zotero:// item link as the source link.")
            )
            self.url.setStyleSheet(
                f"QLineEdit {{ border-bottom: 2px solid {theme.current().danger}; }}"
            )
        else:
            self.url.setStyleSheet("")
            if text:
                self.url.setText(normalize_source_url(text))

    def _open_url(self) -> None:
        url = normalize_source_url(self.url.text())
        if url:
            QDesktopServices.openUrl(QUrl(url))

    # --- flashcards -----------------------------------------------------

    def _refresh_cards(self) -> None:
        self.cards.clear()
        if self.note is None:
            return
        cards = self.window.vault.cards_for(self.note.id)
        for card in cards:
            front = card.front if card.kind == "basic" else card.front.replace("\n", " ")
            text = f"{front}\n→ {card.back}" if card.kind == "basic" else f"{front}"
            badge = "  ·  " + _("from note text") if card.source == "inline" else ""
            item = QListWidgetItem(
                icons.icon("cards"),
                text + ("\n" + (_("Cloze") if card.kind == "cloze" else _("Q&A")) + badge),
            )
            item.setData(Qt.ItemDataRole.UserRole, card)
            self.cards.addItem(item)
        self.tabs.setTabText(
            2, _("Flashcards ({len})").format(len=len(cards)) if cards else _("Flashcards")
        )

    def _selected_card(self) -> Flashcard | None:
        item = self.cards.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def add_card(self) -> None:
        if self.note is None:
            return
        self.flush()
        card = Flashcard(None, self.note.id, "")
        if CardDialog(card, self).exec():
            self.window.vault.save_card(card)
            self._refresh_cards()
            self.tabs.setCurrentIndex(2)

    def edit_card(self) -> None:
        card = self._selected_card()
        if card is None:
            return
        if card.source == "inline":
            QMessageBox.information(
                self,
                _("Flashcard from text"),
                _("This card comes from the note text (Q:/A: or {{c1::…}}). Edit it there."),
            )
            return
        if CardDialog(card, self).exec():
            self.window.vault.save_card(card)
            self._refresh_cards()

    def delete_card(self) -> None:
        card = self._selected_card()
        if card is None or card.source == "inline":
            return
        if (
            QMessageBox.question(self, _("Delete flashcard"), _("Delete this flashcard?"))
            == QMessageBox.StandardButton.Yes
        ):
            self.window.vault.delete_card(card.id)
            self._refresh_cards()

    # --- more menu ----------------------------------------------------------

    def _build_more_menu(self) -> None:
        m = self.more_menu
        m.addAction(icons.icon("copy"), _("Copy note link"), self._copy_link)
        m.addAction(
            icons.icon("copy"),
            _("Copy note ID"),
            lambda: QGuiApplication.clipboard().setText(self.note.id if self.note else ""),
        )
        m.addSeparator()
        m.addAction(
            icons.icon("graph"),
            _("Show in graph"),
            lambda: self.window.show_local_graph(self.note.id if self.note else None),
        )
        m.addAction(
            icons.icon("export"),
            _("Export this note and its links…"),
            lambda: self.window.export_dialog("subgraph"),
        )
        m.addAction(
            icons.icon("review"),
            _("Quiz on this note's neighbourhood"),
            lambda: self.window.quiz_current(),
        )
        m.addAction(
            icons.icon("chat"), _("Ask about this note…"), lambda: self.window.ask_about_current()
        )

    def _copy_link(self) -> None:
        if self.note:
            QGuiApplication.clipboard().setText(f"[[{self.note.title or self.note.id}]]")
            self.statusMessage.emit(_("Copied a [[link]] to this note."))
