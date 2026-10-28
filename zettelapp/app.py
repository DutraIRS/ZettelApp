"""Application entry point."""

from __future__ import annotations

import getpass
import hashlib
import importlib
import json
import logging
import os
import pkgutil
import shutil
import sys
import traceback
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QByteArray, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from zettelapp import APP_NAME, ORG_NAME, __version__, i18n, settings, winintegration
from zettelapp.core.security import parse_app_url
from zettelapp.paths import ensure_dir, logs_dir, resource_path
from zettelapp.ui import theme

log = logging.getLogger("zettelapp")
MAX_MESSAGE = 4096
UPDATE_CHECK_DELAY_MS = 4000


def configure_logging() -> None:
    try:
        handler = RotatingFileHandler(
            ensure_dir(logs_dir()) / "zettelapp.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def _server_name() -> str:
    """Per-user pipe name, so two Windows accounts never talk to each other."""
    return f"{APP_NAME}-{hashlib.sha256(getpass.getuser().encode('utf-8')).hexdigest()[:16]}"


def _message_from_args(args: list[str]) -> dict:
    for arg in args[1:]:
        note_id = parse_app_url(arg)
        if note_id:
            return {"open": note_id}
    return {"activate": True}


def _send_to_running_instance(message: dict) -> bool:
    socket = QLocalSocket()
    socket.connectToServer(_server_name())
    if not socket.waitForConnected(400):
        return False
    winintegration.allow_foreground_switch()
    socket.write(QByteArray(json.dumps(message).encode("utf-8")))
    socket.flush()
    socket.waitForBytesWritten(1000)
    socket.disconnectFromServer()
    return True


def _listen(window) -> QLocalServer:
    server = QLocalServer(window)
    server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)  # current user only
    if not server.listen(_server_name()):
        QLocalServer.removeServer(_server_name())  # stale pipe from a crashed instance
        server.listen(_server_name())

    def on_connection() -> None:
        socket = server.nextPendingConnection()
        if socket is None:
            return

        def read() -> None:
            data = bytes(socket.readAll())[:MAX_MESSAGE]
            try:
                message = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return
            if isinstance(message, dict):
                window.handle_message(message)

        socket.readyRead.connect(read)
        socket.disconnected.connect(socket.deleteLater)

    server.newConnection.connect(on_connection)
    return server


def _install_excepthook() -> None:
    def hook(exc_type, exc, tb) -> None:
        log.error("Unhandled error", exc_info=(exc_type, exc, tb))
        if QApplication.instance() is None:
            return
        box = QMessageBox(
            QMessageBox.Icon.Critical,
            APP_NAME,
            "Something went wrong. Your notes are saved automatically, so nothing should be lost.\n\n"
            f"{exc_type.__name__}: {exc}",
        )
        box.setDetailedText("".join(traceback.format_exception(exc_type, exc, tb)))
        box.setInformativeText(f"Details were written to the log in {logs_dir()}.")
        box.exec()

    sys.excepthook = hook


def _self_test(argv: list[str]) -> int:
    """Check that a packaged build is complete: import every module and build the window offscreen."""
    import zettelapp

    for module in pkgutil.walk_packages(zettelapp.__path__, "zettelapp."):
        importlib.import_module(module.name)
    app = QApplication([argv[0], "-platform", "offscreen"])
    theme.apply_theme(app, "light")
    from zettelapp.ui.main_window import MainWindow

    window = MainWindow()
    window.close()
    print(f"{APP_NAME} {__version__} self-test OK")
    return 0


def remove_user_data() -> int:
    """Run by the uninstaller when the user ticks "Also delete my ZettelApp settings…":
    removes settings, saved API keys, logs, cache and automatic backups. Notes are never
    touched: vaults live in folders the user chose (Documents\\ZettelApp by default)."""
    from zettelapp.core import secrets
    from zettelapp.paths import local_data_dir

    store = settings.store()
    store.clear()
    store.sync()
    secrets.delete_all()
    shutil.rmtree(local_data_dir(), ignore_errors=True)
    return 0


def _option(argv: list[str], name: str) -> str | None:
    if name in argv:
        index = argv.index(name)
        if index + 1 < len(argv):
            return argv[index + 1]
    return None


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if "--self-test" in argv:
        return _self_test(argv)
    if "--remove-user-data" in argv:  # no window, no log file: the uninstaller is waiting
        return remove_user_data()
    vault_arg = _option(argv, "--vault")
    winintegration.set_app_user_model_id()
    configure_logging()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationVersion(__version__)
    icon_file = resource_path("icon.ico")
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))

    message = _message_from_args(argv)
    if _send_to_running_instance(message):
        return 0

    _install_excepthook()
    i18n.install(app, settings.get(settings.UI_LANGUAGE))
    theme.apply_theme(app, settings.get(settings.THEME))

    from zettelapp.ui.main_window import MainWindow

    window = MainWindow()
    server = _listen(window)
    window.show()
    if vault_arg and os.path.isdir(vault_arg):
        window.open_vault(vault_arg)
    else:
        window.open_default_vault()
    if "open" in message:
        window.handle_message(message)
    # Look for a newer version once start-up has settled; it never interrupts anything.
    QTimer.singleShot(UPDATE_CHECK_DELAY_MS, window.check_for_updates)

    def follow_system_theme(*_args) -> None:
        if settings.get(settings.THEME) == "system":
            window.settings_changed()

    try:
        app.styleHints().colorSchemeChanged.connect(follow_system_theme)
    except AttributeError:  # pragma: no cover - Qt < 6.5
        pass
    log.info("%s %s started", APP_NAME, __version__)
    code = app.exec()
    server.close()
    return code
