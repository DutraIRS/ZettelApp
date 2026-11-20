"""Android platform integration (no-ops or safe fallbacks elsewhere).

- Android environment detection (`IS_ANDROID`);
- the per-user `zettelapp://` URL scheme handling for Android Intents;
- file manager and share intent launcher (`reveal_in_file_manager`);
- AnkiDroid (`com.ichi2.anki`) integration helper;
- Zotero mobile link (`zotero://`) URI launcher.

Intents are dispatched through whichever Python→Java bridge is available:
PyJNIus (Kivy-style builds) or Chaquopy's `java` module, with the activity the
Android shell registered via :func:`set_activity` (its `bootstrap` call).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from zettelapp import URL_SCHEME

IS_ANDROID = (
    sys.platform == "android"
    or "ANDROID_ARGUMENT" in os.environ
    or "ANDROID_ROOT" in os.environ
    or hasattr(sys, "getandroidapilevel")
)

ANKIDROID_PACKAGE = "com.ichi2.anki"
ANKIDROID_AUTHORITY = "com.ichi2.anki.flashcards"

_activity: object | None = None


def set_activity(activity: object | None) -> None:
    """Register the foreground Activity (called by the Android shell)."""
    global _activity
    _activity = activity


def bootstrap(base_dir: str, cache_dir: str, activity: object | None = None) -> None:
    """One call from the Android shell once Python is up: dirs + activity."""
    from zettelapp import paths

    set_activity(activity)
    paths.set_android_dirs(base_dir, cache_dir)


def launch_command() -> str:
    """Command/action string for zettelapp:// protocol on Android."""
    return f"{URL_SCHEME}://note/%s"


def register_url_protocol() -> None:
    """On Android, zettelapp:// protocol registration is handled in AndroidManifest.xml."""
    pass


def unregister_url_protocol() -> None:
    """On Android, zettelapp:// protocol registration is handled in AndroidManifest.xml."""
    pass


def registered_command() -> str | None:
    """The protocol scheme string registered on Android."""
    if not IS_ANDROID:
        return None
    return launch_command()


def _java_bridge() -> tuple[object, object, object] | None:
    """(Intent, Uri, activity) through the available Java bridge, else None."""
    # PyJNIus (Kivy / buildozer builds)
    try:
        from jnius import autoclass  # type: ignore[import-not-found]

        activity = getattr(autoclass("org.kivy.android.PythonActivity"), "mActivity", None)
        if activity:
            return (
                autoclass("android.content.Intent"),
                autoclass("android.net.Uri"),
                activity,
            )
    except Exception:
        pass
    # Chaquopy (Gradle builds): the shell registers its Activity at startup.
    try:
        from java import jclass  # type: ignore[import-not-found]

        if _activity is not None:
            return jclass("android.content.Intent"), jclass("android.net.Uri"), _activity
    except Exception:
        pass
    return None


def _view_uri(uri: str, mime: str = "") -> bool:
    """Open *uri* through an ACTION_VIEW intent. False when no bridge is up."""
    bridge = _java_bridge()
    if bridge is None:
        return False
    Intent, Uri, activity = bridge
    try:
        intent = Intent(Intent.ACTION_VIEW, Uri.parse(uri))
        if mime:
            intent.setDataAndType(intent.getData(), mime)
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        activity.startActivity(intent)
        return True
    except Exception:
        return False


def reveal_in_file_manager(path: str | Path) -> None:
    """Show *path* in an Android file manager or trigger a system VIEW intent."""
    if not IS_ANDROID:
        return
    _view_uri(Path(path).to_uri(), "*/*")


def is_ankidroid_available() -> bool:
    """True if AnkiDroid is installed and available on Android."""
    if not IS_ANDROID:
        return False
    bridge = _java_bridge()
    if bridge is None:
        return False
    try:
        _, _, activity = bridge
        pm = activity.getPackageManager()
        pm.getPackageInfo(ANKIDROID_PACKAGE, 0)
        return True
    except Exception:
        return False


def get_ankidroid_content_uri() -> str:
    """Returns the AnkiDroid content provider authority URI."""
    return f"content://{ANKIDROID_AUTHORITY}"


def launch_zotero_url(url: str) -> bool:
    """Launch a zotero:// link on Android using ACTION_VIEW intent."""
    if not IS_ANDROID or not url.startswith("zotero://"):
        return False
    return _view_uri(url)
