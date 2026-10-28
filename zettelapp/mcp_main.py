"""Entry point of the ZettelApp MCP server (zettelapp-mcp.exe).

    zettelapp-mcp --vault "C:\\Users\\me\\Documents\\ZettelApp" [--allow-writes]

Without --vault, the vault last opened in ZettelApp is served.

The MCP client starts this process, but it only runs while ZettelApp is open with the
MCP switch in its status bar on: it refuses to start otherwise, and exits by itself
within a second of the switch going off or ZettelApp closing, so no ZettelApp process
is left running when the app isn't.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time

from zettelapp import __version__
from zettelapp.core.storage import Vault, VaultError
from zettelapp.mcp_server import SWITCHED_OFF, ZettelMcpServer, _settings_allow_writes
from zettelapp.mcp_switch import mcp_switched_on

SWITCH_POLL_SECONDS = 1.0


def _exit_when_switched_off(log: logging.Logger) -> threading.Thread:
    """Stop the whole process once ZettelApp's MCP switch is off (or the app is gone).

    The main thread is blocked reading stdin, so the watcher ends the process itself;
    SQLite's journal keeps the vault consistent even if a write was in progress.
    """

    def watch() -> None:
        while mcp_switched_on():
            time.sleep(SWITCH_POLL_SECONDS)
        log.info("MCP was switched off in ZettelApp, or ZettelApp was closed. Stopping.")
        for handler in logging.getLogger().handlers:
            handler.flush()
        os._exit(0)

    thread = threading.Thread(target=watch, name="mcp-switch-watch", daemon=True)
    thread.start()
    return thread


def _last_vault() -> str | None:
    try:
        from zettelapp import settings

        return settings.get(settings.LAST_VAULT) or None
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zettelapp-mcp", description="MCP server for a ZettelApp vault (stdio)."
    )
    parser.add_argument(
        "--vault", help="Vault folder (default: the vault last opened in ZettelApp)."
    )
    parser.add_argument(
        "--allow-writes",
        action="store_true",
        help="Offer create_note and add_link (also requires the option in ZettelApp).",
    )
    parser.add_argument("--version", action="version", version=f"zettelapp-mcp {__version__}")
    args = parser.parse_args(argv)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[attr-defined]  # TextIO lacks reconfigure; guarded by hasattr
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    log = logging.getLogger("zettelapp.mcp")

    if sys.stdin is None or sys.stdout is None:
        log.error("zettelapp-mcp must be started by an MCP client with stdin/stdout attached.")
        return 2
    if not mcp_switched_on():
        log.error(SWITCHED_OFF)
        return 1
    path = args.vault or _last_vault()
    if not path or not Vault.is_vault(path):
        log.error("No ZettelApp vault found%s. Pass --vault PATH.", f" at {path}" if path else "")
        return 2
    writes = args.allow_writes and _settings_allow_writes()
    if args.allow_writes and not writes:
        log.warning(
            "--allow-writes ignored: enable MCP writes in ZettelApp (Tools ▸ Options ▸ MCP server)."
        )
    try:
        vault = Vault.open(path, create=False, readonly=not writes)
    except (VaultError, OSError) as exc:
        log.error("Could not open the vault: %s", exc)
        return 2

    out = sys.stdout.buffer
    sys.stdout = sys.stderr  # stray prints must never corrupt the protocol stream
    log.info("Serving %s (%s)", vault.folder, "read-write" if writes else "read-only")
    _exit_when_switched_off(log)
    try:
        ZettelMcpServer(vault, allow_writes=writes).serve(sys.stdin.buffer, out)
    except KeyboardInterrupt:
        pass
    finally:
        vault.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
