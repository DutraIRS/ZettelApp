"""The update notice: a small card in the lower-right corner of the main window.

It never takes focus or blocks anything, appears at most once per new version, and can
be closed or silenced for good ("Don't check for updates").
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
)

from zettelapp import RELEASES_URL, settings
from zettelapp.i18n import _
from zettelapp.ui import icons, theme
from zettelapp.ui.widgets import accent_button, label, link_button, tool_button

MARGIN = 16


class UpdateNotice(QFrame):
    def __init__(self, window: QMainWindow, version: str):
        super().__init__(window)
        self.window = window
        self.version = version
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName(_("ZettelApp {version} is available").format(version=version))
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(shadow)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 6, 12)
        row.setSpacing(12)
        glyph = QLabel()
        glyph.setPixmap(icons.icon("sync", theme.current().accent, 20).pixmap(20, 20))
        row.addWidget(glyph, 0, Qt.AlignmentFlag.AlignTop)
        text = QVBoxLayout()
        text.setSpacing(4)
        text.addWidget(label(_("Update available"), "section"))
        text.addWidget(
            label(
                _("ZettelApp {version} is ready to download.").format(version=version), "secondary"
            )
        )
        buttons = QHBoxLayout()
        buttons.setSpacing(4)
        buttons.addWidget(accent_button(_("Download"), self._download))
        buttons.addWidget(link_button(_("Don't check for updates"), self._silence))
        buttons.addStretch(1)
        text.addSpacing(4)
        text.addLayout(buttons)
        row.addLayout(text, 1)
        row.addWidget(tool_button("cancel", _("Close"), self.close), 0, Qt.AlignmentFlag.AlignTop)
        for button in self.findChildren(QAbstractButton):
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # clicking never steals focus
        self.setFixedWidth(360)
        self.adjustSize()
        window.installEventFilter(self)
        self.reposition()

    def reposition(self) -> None:
        bar = self.window.statusBar()
        bottom = self.window.height() - (bar.height() if bar.isVisible() else 0)
        self.move(self.window.width() - self.width() - MARGIN, bottom - self.height() - MARGIN)
        self.raise_()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self.window and event.type() == QEvent.Type.Resize:
            self.reposition()
        return False

    def _download(self) -> None:
        QDesktopServices.openUrl(QUrl(RELEASES_URL))  # always the fixed releases page
        self.close()

    def _silence(self) -> None:
        settings.put(settings.UPDATE_CHECK, False)
        self.window.statusBar().showMessage(
            _("ZettelApp won't check for updates. Turn it back on in Tools ▸ Options ▸ General."),
            8000,
        )
        self.close()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.window.removeEventFilter(self)
        super().closeEvent(event)
        self.deleteLater()
