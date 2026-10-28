"""Input validation used wherever untrusted data enters the app.

Untrusted data includes note text (it may come from imports), URLs typed by
the user, image files, archives, and messages from the zettelapp:// protocol
handler. Everything here fails closed: unknown input is rejected.
"""

from __future__ import annotations

import re
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from zettelapp import URL_SCHEME

WEB_SCHEMES = frozenset({"http", "https", "mailto"})
MAX_URL_LENGTH = 2048

NOTE_ID_RE = re.compile(r"^\d{14}(?:-\d{1,4})?$")
ASSET_NAME_RE = re.compile(r"^[0-9a-f]{20}\.(?:png|jpg|gif|webp|bmp)$")

MAX_IMAGE_BYTES = 25 * 1024 * 1024

_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class UnsafeInputError(ValueError):
    """Raised when input fails validation."""


def is_valid_note_id(value: object) -> bool:
    return isinstance(value, str) and bool(NOTE_ID_RE.match(value))


def is_valid_asset_name(value: object) -> bool:
    return isinstance(value, str) and bool(ASSET_NAME_RE.match(value))


def is_safe_web_url(url: str) -> bool:
    """True for http(s) URLs with a host and for mailto: links."""
    if not isinstance(url, str) or not url or len(url) > MAX_URL_LENGTH:
        return False
    if _CONTROL_CHARS.search(url) or " " in url.strip():
        return False
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return False
    scheme = parts.scheme.lower()
    if scheme not in WEB_SCHEMES:
        return False
    if scheme in ("http", "https"):
        return bool(parts.hostname)
    return bool(parts.path)


ZOTERO_KEY_RE = re.compile(r"[A-Z0-9]{8}")
_ZOTERO_URL_RE = re.compile(
    r"^zotero://(?:select|open-pdf)/(?:library|groups/\d{1,12})/items/[A-Z0-9]{8}(?:\?page=\d{1,5})?$"
)


def is_zotero_url(url: object) -> bool:
    """Only "select item" and "open PDF" links into Zotero are accepted."""
    return isinstance(url, str) and bool(_ZOTERO_URL_RE.match(url.strip()))


def is_openable_url(url: object) -> bool:
    """Links ZettelApp will hand to Windows: web pages, e-mail and Zotero items."""
    return is_safe_web_url(url) or is_zotero_url(url)


def normalize_source_url(text: str) -> str | None:
    """A note's source link: a web/mailto URL or a Zotero item link."""
    text = (text or "").strip()
    return text if is_zotero_url(text) else normalize_web_url(text)


def normalize_web_url(text: str) -> str | None:
    """Turn user input such as "example.com/page" into a safe URL, or None."""
    text = (text or "").strip()
    if not text:
        return None
    scheme = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):(?!\d+(?:/|$))", text)
    if scheme and scheme.group(1).lower() not in WEB_SCHEMES:
        return None  # javascript:, file:, ms-settings: and other non-web schemes
    if "://" not in text and not text.lower().startswith("mailto:"):
        if "@" in text and "/" not in text:
            text = "mailto:" + text
        else:
            text = "https://" + text
    return text if is_safe_web_url(text) else None


def safe_filename(name: str, default: str = "untitled", max_length: int = 80) -> str:
    """A file name that is valid on Windows and cannot escape its directory."""
    name = unicodedata.normalize("NFC", name or "")
    name = _CONTROL_CHARS.sub("", name)
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    name = re.sub(r"\s+", " ", name).strip().strip(".")
    name = name[:max_length].rstrip(" .")
    if not name or name.upper().split(".")[0] in _WINDOWS_RESERVED:
        name = default
    return name


_IMAGE_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"BM", "bmp"),
)


def sniff_image_type(data: bytes) -> str | None:
    """File extension for a supported raster image, judged by its content.

    SVG is deliberately unsupported: it is a document format that can carry
    scripts and external references.
    """
    for signature, ext in _IMAGE_SIGNATURES:
        if data.startswith(signature):
            return ext
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def parse_app_url(url: str) -> str | None:
    """Note id from a zettelapp://note/<id> URL; None for anything else."""
    if not isinstance(url, str) or len(url) > 200:
        return None
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return None
    if parts.scheme.lower() != URL_SCHEME or parts.netloc.lower() != "note":
        return None
    note_id = parts.path.strip("/")
    return note_id if is_valid_note_id(note_id) else None


def app_url(note_id: str) -> str:
    return f"{URL_SCHEME}://note/{note_id}"


# --- archives -------------------------------------------------------------

MAX_ARCHIVE_MEMBERS = 50_000
MAX_ARCHIVE_TOTAL_BYTES = 2 * 1024**3
MAX_COMPRESSION_RATIO = 200


def check_zip(zf: zipfile.ZipFile) -> None:
    """Reject archives with unsafe paths or decompression-bomb proportions."""
    members = zf.infolist()
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise UnsafeInputError("The archive contains too many files.")
    total = 0
    for info in members:
        safe_member_path(info.filename)
        total += info.file_size
        if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
            raise UnsafeInputError(f"Suspicious compression ratio in {info.filename!r}.")
    if total > MAX_ARCHIVE_TOTAL_BYTES:
        raise UnsafeInputError("The archive is too large to import.")


def safe_member_path(name: str) -> PurePosixPath:
    """Validate a relative archive path (no absolute paths, drives or '..')."""
    if not name or "\x00" in name:
        raise UnsafeInputError("Empty or invalid path in archive.")
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise UnsafeInputError(f"Unsafe path in archive: {name!r}")
    if ":" in path.parts[0]:
        raise UnsafeInputError(f"Unsafe path in archive: {name!r}")
    return path


def resolve_inside(base: Path, relative: str) -> Path:
    """Resolve *relative* against *base*, refusing results outside *base*."""
    base = base.resolve()
    target = (base / relative).resolve()
    if target != base and base not in target.parents:
        raise UnsafeInputError(f"Path escapes its folder: {relative!r}")
    return target
