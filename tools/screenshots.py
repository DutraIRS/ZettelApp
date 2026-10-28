"""Render screenshots of the real app (offscreen) for the website and docs.

Run with:  python tools/screenshots.py [output-folder]
Settings go to a temporary INI file, so your own preferences are untouched.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="zettelapp-shots-"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"))
os.environ["ZETTELAPP_SETTINGS_FILE"] = str(TMP / "settings.ini")

from PySide6.QtCore import QEventLoop, QThreadPool, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from tools.demo_vault import build_demo  # noqa: E402
from zettelapp import settings  # noqa: E402
from zettelapp.core.storage import Vault  # noqa: E402
from zettelapp.ui import theme  # noqa: E402


def settle(app: QApplication, ms: int = 400, window=None) -> None:
    for _ in range(3):
        QThreadPool.globalInstance().waitForDone(20000)
        if window is not None:
            window.suggestions.pool.waitForDone(20000)
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()
        app.processEvents()


def main() -> None:
    theme._windows_accent = lambda dark: None  # screenshots use the default Windows blue accent
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "website" / "assets" / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    vault_dir = TMP / "Demo vault"
    vault = Vault.open(vault_dir)
    ids = build_demo(vault)
    vault.close()

    from zettelapp.ui.main_window import MainWindow

    for mode in ("light", "dark"):
        settings.put(settings.THEME, mode)
        theme.apply_theme(app, mode)
        window = MainWindow()
        window.resize(1440, 900)
        window.show()
        window.open_vault(vault_dir)
        window.status_vault.setText(r"C:\Users\you\Documents\ZettelApp")  # never publish a real local path
        window.open_note(ids["Spaced repetition"])
        window.editor.set_view_mode(1)
        settle(app, 900, window)
        window.grab().save(str(out / f"notes-{mode}.png"))

        window.editor.tabs.setCurrentIndex(1)
        window.editor.mindmap.fit()
        settle(app)
        window.grab().save(str(out / f"mindmap-{mode}.png"))
        window.editor.tabs.setCurrentIndex(0)

        window.show_page(1)
        settle(app, 600)
        window.grab().save(str(out / f"graph-{mode}.png"))
        window.graph.color_by.setCurrentIndex(1)  # k-means clusters
        settle(app, 600)
        window.grab().save(str(out / f"graph-clusters-{mode}.png"))
        window.graph.dim_group.button(1).click()  # 3D
        settle(app, 600)
        window.grab().save(str(out / f"graph-3d-{mode}.png"))
        window.graph.dim_group.button(0).click()
        window.graph.color_by.setCurrentIndex(0)

        window.show_page(2)
        settle(app, 800)
        window.grab().save(str(out / f"insights-{mode}.png"))
        window.show_page(3)
        settle(app)
        window.grab().save(str(out / f"review-{mode}.png"))
        window.review.mode_combo.setCurrentIndex(1)
        window.review.start_quiz()
        settle(app)
        window.grab().save(str(out / f"quiz-{mode}.png"))
        window.review.finish()
        window.show_page(4)
        window.ask.question.setPlainText("How do spacing and retrieval work together?")
        window.ask.answer.set_renderer(window.ask._renderer())
        window.ask.answer.show_markdown(
            "Spacing and retrieval reinforce each other. **Spaced repetition** schedules reviews just before "
            f"forgetting [[{ids['Spaced repetition']}]], and each review is an act of **active recall** "
            f"[[{ids['Active recall']}]], which strengthens memory more than rereading "
            f"[[{ids['Illusion of competence']}]]. The forgetting curve flattens after each successful "
            f"retrieval [[{ids['Forgetting curve']}]].")
        settle(app)
        window.grab().save(str(out / f"ask-{mode}.png"))
        window.close()
        settle(app, 200)
    print("Screenshots written to", out)


if __name__ == "__main__":
    main()
