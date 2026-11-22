# ZettelApp on Android

ZettelApp runs on Android through **Chaquopy**, which embeds Python inside a normal Android app:
a native Kotlin/Compose screen drives the same core the desktop app uses — storage, models,
Markdown rendering, Anki export and security. The desktop UI (PySide6) is not shipped on Android;
the phone gets its own screen that talks to the core through the small, Qt-free
[`zettelapp.mobile`](../zettelapp/mobile.py) facade.

## Status (alpha)

What works:

- **Notes list** with search over titles and a tag filter, **editing** and **creating** notes
  (title, text, tags), saved the same way the desktop app saves them (atomic writes, link resync,
  `#tags` and typed `[[links]]` in the text), a simple preview, and moving notes to the trash.
- Under each note, its **links, backlinks and flashcards**.
- **Graph** (a ring layout grouped by tag, links in their type colours), **Insights** (counts, notes
  per month, top tags, links by type) and **Review** of due flashcards, cloze cards included.
- A new vault starts with the same **starter notes** as on the desktop.
- **Deep links**: `zettelapp://note/<id>` opens the matching note, so links on Anki cards work.
- **Storage**: the vault lives in the app's private storage. (Scoped storage mounts the shared
  `Documents` folder but won't let SQLite lock a database there, so it isn't used.) Logs, backups and
  the app's settings follow the same layout the desktop uses, under the app's private directories.
- **Secrets**: API keys are kept in memory for the current session — Android has no shared secret
  store the app could use today.
- **Anki and Zotero**: AnkiDroid availability checks and `zotero://` links go through Android
  intents (`zettelapp/androidintegration.py`).

Not yet on Android: semantic search and *Ask your notes* (their wheels have no Android builds
yet), a force-directed graph and the clustering (numpy), the Markdown renderer in the preview,
translations of the phone screens, on-device flashcard export to AnkiDroid, sync, and signed store
releases.

## Building

The Gradle project lives in `android/`:

- Open the `android/` folder in Android Studio and let it sync, or run
  `gradle assembleDebug` from `android/` with a JDK 17 and the Android SDK (API 35) installed.
- The build bundles the repository's Python package (`zettelapp/…`) into the APK through
  Chaquopy and pip-installs the pure-Python dependencies of the core (`markdown-it-py`,
  `PyYAML`, `genanki`). The heavy desktop wheels (PySide6, numpy, rapidfuzz, onnxruntime,
  tokenizers) are desktop-only and are not shipped on the phone.
- `adb install android/app/build/outputs/apk/debug/app-debug.apk` puts it on a device or
  emulator; `adb shell am start -a android.intent.action.VIEW -d "zettelapp://note/<id>"` tests
  a deep link.

## Where the code lives

| Piece | Location |
|---|---|
| Native screen and deep-link handling | `android/app/src/main/java/com/dutrairs/zettelapp/MainActivity.kt` |
| Qt-free core facade the screen calls | `zettelapp/mobile.py` |
| Intents, AnkiDroid, `zettelapp://` | `zettelapp/androidintegration.py` |
| Android path handling | `zettelapp/paths.py` (`IS_ANDROID`) |
| Secrets fallback | `zettelapp/core/secrets.py` (`IS_ANDROID`) |
| Facade tests | `tests/test_mobile.py`, `tests/test_android_integration.py` |
