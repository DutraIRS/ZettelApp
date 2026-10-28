"""API keys and other secrets, kept in Windows Credential Manager.

Secrets are stored as generic credentials named "ZettelApp/<name>" for the
current user on this computer (they do not roam). Nothing is written to the
registry or to disk by this module, and secret values are never logged.
Outside Windows, secrets live in memory for the current session only.
"""

from __future__ import annotations

import re
import sys

PREFIX = "ZettelApp/"
_NAME_RE = re.compile(r"^[\w./-]{1,100}$")
_MAX_BLOB = 5 * 512  # CRED_MAX_CREDENTIAL_BLOB_SIZE
_memory: dict[str, str] = {}

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2
    ERROR_NOT_FOUND = 1168

    class _CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    _PCREDENTIAL = ctypes.POINTER(_CREDENTIAL)
    _advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    _CredWrite = _advapi32.CredWriteW
    _CredWrite.argtypes = [_PCREDENTIAL, wintypes.DWORD]
    _CredWrite.restype = wintypes.BOOL
    _CredRead = _advapi32.CredReadW
    _CredRead.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_PCREDENTIAL),
    ]
    _CredRead.restype = wintypes.BOOL
    _CredDelete = _advapi32.CredDeleteW
    _CredDelete.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    _CredDelete.restype = wintypes.BOOL
    _CredFree = _advapi32.CredFree
    _CredFree.argtypes = [ctypes.c_void_p]
    _CredFree.restype = None


def secrets_available() -> bool:
    """True when secrets persist securely (Windows Credential Manager)."""
    return sys.platform == "win32"


def _target(name: str) -> str:
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise ValueError("Invalid secret name.")
    return PREFIX + name


def set_secret(name: str, value: str) -> None:
    target = _target(name)
    if not isinstance(value, str) or not value:
        raise ValueError("The secret is empty.")
    blob = value.encode("utf-16-le")  # same encoding as Credential Manager's own UI
    if len(blob) > _MAX_BLOB:
        raise ValueError("The secret is too long.")
    if not secrets_available():
        _memory[target] = value
        return
    buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    try:
        cred = _CREDENTIAL()
        cred.Type = CRED_TYPE_GENERIC
        cred.TargetName = target
        cred.CredentialBlobSize = len(blob)
        cred.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
        cred.Persist = CRED_PERSIST_LOCAL_MACHINE
        cred.UserName = "ZettelApp"
        if not _CredWrite(ctypes.byref(cred), 0):
            raise OSError(ctypes.get_last_error(), "Could not save to Windows Credential Manager.")
    finally:
        ctypes.memset(buffer, 0, len(blob))


def get_secret(name: str) -> str | None:
    target = _target(name)
    if not secrets_available():
        return _memory.get(target)
    pointer = _PCREDENTIAL()
    if not _CredRead(target, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return None
        raise OSError(error, "Could not read from Windows Credential Manager.")
    try:
        cred = pointer.contents
        blob = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize)
    finally:
        _CredFree(pointer)
    try:
        return blob.decode("utf-16-le")
    except UnicodeDecodeError:  # written by another tool as UTF-8
        return blob.decode("utf-8", errors="replace")


def delete_secret(name: str) -> None:
    target = _target(name)
    if not secrets_available():
        _memory.pop(target, None)
        return
    if not _CredDelete(target, CRED_TYPE_GENERIC, 0):
        error = ctypes.get_last_error()
        if error != ERROR_NOT_FOUND:
            raise OSError(error, "Could not remove from Windows Credential Manager.")
