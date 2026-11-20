"""Android platform integration (no-ops or safe fallbacks elsewhere).

- Android environment detection (`IS_ANDROID`);
- the per-user `zettelapp://` URL scheme handling for Android Intents;
- file manager and share intent launcher (`reveal_in_file_manager`);
- AnkiDroid (`com.ichi2.anki`) integration helper;
- Zotero mobile link (`zotero://`) URI launcher.
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


def reveal_in_file_manager(path: str | Path) -> None:
    """Show *path* in Android file manager or trigger a system VIEW intent."""
    path = Path(path)
    if not IS_ANDROID:
        return

    # Attempt PyJNIus / Chaquopy Android Intent invocation if runtime is available
    try:
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        activity = getattr(PythonActivity, "mActivity", None)
        if activity:
            intent = Intent(Intent.ACTION_VIEW)
            file_uri = Uri.parse(path.to_uri())
            intent.setDataAndType(file_uri, "*/*")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            activity.startActivity(intent)
    except Exception:
        # Fallback when running outside Android Java runtime or in unit test
        pass


def is_ankidroid_available() -> bool:
    """True if AnkiDroid is installed and available on Android."""
    if not IS_ANDROID:
        return False

    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = getattr(PythonActivity, "mActivity", None)
        if activity:
            pm = activity.getPackageManager()
            pm.getPackageInfo(ANKIDROID_PACKAGE, 0)
            return True
    except Exception:
        pass
    return False


def get_ankidroid_content_uri() -> str:
    """Returns the AnkiDroid content provider authority URI."""
    return f"content://{ANKIDROID_AUTHORITY}"


def launch_zotero_url(url: str) -> bool:
    """Launch a zotero:// link on Android using ACTION_VIEW intent."""
    if not IS_ANDROID or not url.startswith("zotero://"):
        return False

    try:
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        activity = getattr(PythonActivity, "mActivity", None)
        if activity:
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            activity.startActivity(intent)
            return True
    except Exception:
        pass
    return False
