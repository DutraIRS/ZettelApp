"""The note editor: title, tags, source link, Markdown body, mind map and flashcards."""

from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtCore import QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication, QPixmap
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
    normalize_source_url,
    normalize_web_url,
)
from zettelapp.core.textutil import extract_hashtags, strip_markdown
from zettelapp.ui import icons, theme
from zettelapp.ui.dialogs import CardDialog, TextPromptDialog
from zettelapp.ui.markdown_editor import MarkdownEditor
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
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)} h ago"
    return when.astimezone().strftime("%d %b %Y")


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
        msg = label("Select a note or create a new one", "heading")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(msg)
        hint = label("One idea per note. Link it to others to grow your Zettelkasten.", "secondary")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(hint)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(accent_button("New note", lambda: self.window.new_note(), "add"))
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
        self.fmt_buttons = [
            tool_button("bold", "Bold (Ctrl+B)", lambda: self.body.wrap_selection("**")),
            tool_button("italic", "Italic (Ctrl+I)", lambda: self.body.wrap_selection("*")),
            tool_button("heading", "Heading", lambda: self.body.prefix_lines("## ")),
            tool_button("bullets", "Bulleted list", lambda: self.body.prefix_lines("- ")),
            tool_button("code", "Code", lambda: self.body.wrap_selection("`")),
        ]
        for b in self.fmt_buttons:
            bar.addWidget(b)
        bar.addSpacing(10)
        bar.addWidget(
            tool_button("relationship", "Link to note (Ctrl+K)", self.linkNoteRequested.emit)
        )
        bar.addWidget(tool_button("globe", "Insert web link", self.insert_web_link))
        bar.addWidget(tool_button("image", "Insert image (Ctrl+Shift+I)", self.insert_image))
        bar.addWidget(
            tool_button(
                "library", "Cite a Zotero reference", lambda: self.window.zotero_reference()
            )
        )
        bar.addWidget(tool_button("mindmap", "Add mind map", self.show_mindmap))
        bar.addWidget(tool_button("cards", "Add flashcard (Ctrl+Shift+F)", self.add_card))
        bar.addStretch(1)
        self.mode_group = QButtonGroup(self)
        for i, (name, tip) in enumerate(
            (("edit", "Edit"), ("view", "Split view"), ("document", "Preview"))
        ):
            b = tool_button(name, f"{tip} (Ctrl+E cycles)", checkable=True)
            self.mode_group.addButton(b, i)
            bar.addWidget(b)
        self.mode_group.idClicked.connect(self.set_view_mode)
        more = QToolButton()
        more.setIcon(icons.icon("more"))
        more.setToolTip("More")
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
        self.title.setPlaceholderText("Untitled")
        self.title.setAccessibleName("Title")
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
        self.picture.setToolTip("Note picture (shown in the graph). Right-click to remove.")
        self.picture.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.picture.customContextMenuRequested.connect(self._picture_menu)
        head.addWidget(self.picture)
        layout.addLayout(head)

        self.tags = TagEditor()
        self.tags.tagsChanged.connect(lambda _: self._edited())
        layout.addWidget(self.tags)

        url_row = QHBoxLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText("Source link (optional): https://… or a zotero:// item link")
        self.url.setAccessibleName("Source link")
        self.url.addAction(
            icons.icon("globe", theme.current().text_muted, 16),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.url.editingFinished.connect(self._url_finished)
        self.url.textEdited.connect(self._edited)
        url_row.addWidget(self.url, 1)
        self.open_url = tool_button("open_external", "Open the source link", self._open_url)
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
        self.body.imageError.connect(lambda msg: QMessageBox.warning(self, "Image not added", msg))
        self.preview = NotePreview(
            lambda name: self.window.vault.asset_path(name) if self.window.vault else None
        )
        self.preview.noteRequested.connect(self.openNote)
        self.preview.newNoteRequested.connect(self.newNoteRequested)
        self.preview.hovered.connect(self.statusMessage)
        self.split = QSplitter(Qt.Orientation.Horizontal)
        self.split.addWidget(self.body)
        self.split.addWidget(self.preview)
        self.split.setChildrenCollapsible(False)
        self.tabs.addTab(self.split, icons.icon("notes"), "Note")

        mind = QWidget()
        mind_layout = QVBoxLayout(mind)
        mind_layout.setContentsMargins(0, 6, 0, 0)
        mind_bar = QHBoxLayout()
        self.mindmap = MindMapView()
        self.mindmap.changed.connect(self._mindmap_changed)
        self.mindmap.openNote.connect(self.openNote)
        self.mindmap.linkNoteRequested.connect(self.mindmapLinkRequested)
        mind_bar.addWidget(
            tool_button("add", "Add child idea (Tab)", self.mindmap.add_child, text="Add idea")
        )
        mind_bar.addWidget(
            tool_button(
                "relationship",
                "Build a mind map from this note's links",
                self.mindmap_from_links,
                text="From links",
            )
        )
        mind_bar.addWidget(
            tool_button("delete", "Delete selected idea (Del)", self.mindmap.delete_selected)
        )
        mind_bar.addStretch(1)
        mind_bar.addWidget(tool_button("fit", "Fit to window", self.mindmap.fit))
        export = QToolButton()
        export.setIcon(icons.icon("export"))
        export.setToolTip("Export mind map")
        export.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        export_menu = QMenu(export)
        export_menu.addAction("PNG image…", lambda: self._export_mindmap("png"))
        export_menu.addAction("SVG image…", lambda: self._export_mindmap("svg"))
        export_menu.addAction("FreeMind / XMind (.mm)…", lambda: self._export_mindmap("mm"))
        export.setMenu(export_menu)
        mind_bar.addWidget(export)
        mind_layout.addLayout(mind_bar)
        mind_layout.addWidget(self.mindmap, 1)
        mind_layout.addWidget(
            label(
                "Tab adds a child, Enter a sibling, F2 renames, Del removes. "
                "Right-click an idea to link it to a note.",
                "caption",
            )
        )
        self.tabs.addTab(mind, icons.icon("mindmap"), "Mind map")

        cards = QWidget()
        cards_layout = QVBoxLayout(cards)
        cards_layout.setContentsMargins(0, 8, 0, 0)
        cards_bar = QHBoxLayout()
        cards_bar.addWidget(
            tool_button("add", "Add flashcard", self.add_card, text="Add flashcard")
        )
        cards_bar.addWidget(tool_button("edit", "Edit flashcard", self.edit_card))
        cards_bar.addWidget(tool_button("delete", "Delete flashcard", self.delete_card))
        cards_bar.addStretch(1)
        cards_layout.addLayout(cards_bar)
        self.cards = QListWidget()
        self.cards.setAccessibleName("Flashcards")
        self.cards.setWordWrap(True)
        self.cards.itemDoubleClicked.connect(lambda _: self.edit_card())
        cards_layout.addWidget(self.cards, 1)
        cards_layout.addWidget(
            label(
                "Cards also come from the note text: write “Q: …” then “A: …”, or "
                "hide words with {{c1::cloze}}.",
                "caption",
                wrap=True,
            )
        )
        self.tabs.addTab(cards, icons.icon("cards"), "Flashcards")
        layout.addWidget(self.tabs, 1)

        self._build_more_menu()
        self.set_view_mode(0)
        self.load(None)

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
        self.tags.set_known_tags([t for t, _ in self.window.vault.all_tags()])
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
        self.meta.setText(
            f"Created {friendly_time(n.created)}  ·  Edited {friendly_time(n.modified)}  ·  "
            f"{words} words  ·  ID {n.id}"
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
        elif is_openable_url(target):  # web pages, e-mail and Zotero items only
            QDesktopServices.openUrl(QUrl(target))
        else:
            self.statusMessage.emit("Only web, e-mail and Zotero links can be opened.")

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
        path, _ = QFileDialog.getOpenFileName(
            self, "Insert image", "", "Images (*.png *.jpg *.jpeg *.gif *.webp *.bmp)"
        )
        if not path:
            return
        try:
            asset = self.window.vault.add_image_file(path)
        except (UnsafeInputError, OSError) as exc:
            QMessageBox.warning(self, "Image not added", str(exc))
            return
        if not self.note.image:
            self.note.image = asset
            self._refresh_picture()
        name = path.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
        self.body.insert_block(f"![{name}](asset:{asset})\n")

    def insert_web_link(self) -> None:
        selected = self.body.textCursor().selectedText()
        dialog = TextPromptDialog(
            "Insert web link", "Address (http, https or mailto):", "", self, "Insert"
        )
        if dialog.exec():
            url = normalize_web_url(dialog.value())
            if url is None:
                QMessageBox.warning(
                    self, "Link not inserted", "Only http(s) and mailto links are allowed."
                )
                return
            self.body.textCursor().insertText(f"[{selected or url}]({url})")

    def insert_note_link(self, title: str, link_type: str = "related") -> None:
        prefix = "" if link_type == "related" else f"{link_type}:: "
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
            self.statusMessage.emit("This note has no links yet. Link it to other notes first.")
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
                "Replace mind map",
                "Replace the current mind map with one built from this note's links?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.mindmap.set_mindmap(root)
        self._mindmap_changed(root)
        self.tabs.setCurrentIndex(1)
        if left_out:
            self.statusMessage.emit(
                f"Left out {left_out} link{'s' if left_out != 1 else ''}: "
                f"a mind map holds at most {MAX_MINDMAP_NODES} ideas."
            )

    def _mindmap_changed(self, data) -> None:
        if self.note is None:
            return
        self.note.mindmap = data
        self._edited()

    def _export_mindmap(self, kind: str) -> None:
        if self.note is None or not self.note.mindmap:
            self.statusMessage.emit("This note has no mind map to export.")
            return
        from zettelapp.core.export import export_mindmap
        from zettelapp.core.security import safe_filename

        filters = {
            "png": "PNG image (*.png)",
            "svg": "SVG image (*.svg)",
            "mm": "FreeMind mind map (*.mm)",
        }
        name = safe_filename(self.title.text() or "Mind map") + "." + kind
        path, _ = QFileDialog.getSaveFileName(self, "Export mind map", name, filters[kind])
        if not path:
            return
        if kind == "png":
            self.mindmap.render_image().save(path, "PNG")
        elif kind == "svg":
            self.mindmap.render_svg(path)
        else:
            export_mindmap(self.note.mindmap, path)
        self.window.notify_file(path, "Mind map exported")

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
        menu.addAction("Remove note picture", self._remove_picture)
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
                "Use an http(s), mailto or zotero:// item link as the source link."
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
            badge = "  ·  from note text" if card.source == "inline" else ""
            item = QListWidgetItem(
                icons.icon("cards"),
                text + ("\n" + ("Cloze" if card.kind == "cloze" else "Q&A") + badge),
            )
            item.setData(Qt.ItemDataRole.UserRole, card)
            self.cards.addItem(item)
        self.tabs.setTabText(2, f"Flashcards ({len(cards)})" if cards else "Flashcards")

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
                "Flashcard from text",
                "This card comes from the note text (Q:/A: or {{c1::…}}). Edit it there.",
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
            QMessageBox.question(self, "Delete flashcard", "Delete this flashcard?")
            == QMessageBox.StandardButton.Yes
        ):
            self.window.vault.delete_card(card.id)
            self._refresh_cards()

    # --- more menu ----------------------------------------------------------

    def _build_more_menu(self) -> None:
        m = self.more_menu
        m.addAction(icons.icon("copy"), "Copy note link", self._copy_link)
        m.addAction(
            icons.icon("copy"),
            "Copy note ID",
            lambda: QGuiApplication.clipboard().setText(self.note.id if self.note else ""),
        )
        m.addSeparator()
        m.addAction(
            icons.icon("graph"),
            "Show in graph",
            lambda: self.window.show_local_graph(self.note.id if self.note else None),
        )
        m.addAction(
            icons.icon("export"),
            "Export this note and its links…",
            lambda: self.window.export_dialog("subgraph"),
        )
        m.addAction(
            icons.icon("review"),
            "Quiz on this note's neighbourhood",
            lambda: self.window.quiz_current(),
        )
        m.addAction(
            icons.icon("chat"), "Ask about this note…", lambda: self.window.ask_about_current()
        )
        m.addSeparator()
        m.addAction(icons.icon("delete"), "Move to Trash", lambda: self.window.trash_current())

    def _copy_link(self) -> None:
        if self.note:
            QGuiApplication.clipboard().setText(f"[[{self.note.title or self.note.id}]]")
            self.statusMessage.emit("Copied a [[link]] to this note.")
