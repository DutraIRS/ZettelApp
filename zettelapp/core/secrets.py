"""API keys and other secrets, kept in the system's secret store.

Windows keeps secrets as generic credentials named "ZettelApp/<name>" in
Windows Credential Manager for the current user on this computer (they do not
roam). Linux keeps them in the freedesktop Secret Service (GNOME Keyring,
KWallet and others implement it) through libsecret, as items with the
attributes ``application=ZettelApp`` and ``name=ZettelApp/<name>``.

Nothing is written to the registry, settings or vault by this module, and
secret values are never logged. When no secret store is available, secrets
live in memory for the current session only.
"""

from __future__ import annotations

import ctypes
import re
import sys

from zettelapp.i18n import _

PREFIX = "ZettelApp/"
_NAME_RE = re.compile(r"^[\w./-]{1,100}$")
_MAX_BLOB = 5 * 512  # CRED_MAX_CREDENTIAL_BLOB_SIZE (Windows Credential Manager)
_MAX_LINUX_CHARS = 4096  # generous: D-Bus carries far more than any API key
_memory: dict[str, str] = {}

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

if IS_WINDOWS:
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
    _CredEnumerate = _advapi32.CredEnumerateW
    _CredEnumerate.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(ctypes.POINTER(_PCREDENTIAL)),
    ]
    _CredEnumerate.restype = wintypes.BOOL

elif IS_LINUX:
    # The freedesktop Secret Service through libsecret (GNOME Keyring, KWallet, …).
    _lib = None
    for _name in ("libsecret-1.so.0", "libsecret-1.so"):
        try:
            _lib = ctypes.CDLL(_name)
            break
        except OSError:
            continue

    _SERVICE_OK: bool | None = None  # answered once a keyring daemon has been asked

    if _lib is not None:
        _SECRET_SCHEMA_ATTRIBUTE_STRING = 0
        _SECRET_SEARCH_ALL = 1 << 0
        _SECRET_SEARCH_UNLOCK = 1 << 1
        _SECRET_SEARCH_LOAD_SECRETS = 1 << 2

        class _GList(ctypes.Structure):
            pass

        _GList._fields_ = [
            ("data", ctypes.c_void_p),
            ("next", ctypes.POINTER(_GList)),
            ("prev", ctypes.POINTER(_GList)),
        ]

        class _GError(ctypes.Structure):
            _fields_ = [
                ("domain", ctypes.c_uint32),  # GQuark
                ("code", ctypes.c_int),
                ("message", ctypes.c_char_p),
            ]

        _lib.g_object_unref.argtypes = [ctypes.c_void_p]
        _lib.g_object_unref.restype = None
        _lib.g_free.argtypes = [ctypes.c_void_p]
        _lib.g_free.restype = None
        _lib.g_list_free.argtypes = [ctypes.c_void_p]
        _lib.g_list_free.restype = None
        _lib.g_hash_table_lookup.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        _lib.g_hash_table_lookup.restype = ctypes.c_char_p

        _lib.secret_schema_new.restype = ctypes.c_void_p
        _lib.secret_schema_new.argtypes = [ctypes.c_char_p, ctypes.c_int]

        # SecretSchema is a ref-counted boxed type, not a GObject: release with
        # secret_schema_unref (older libsecret builds name it secret_schema_free).
        if hasattr(_lib, "secret_schema_unref"):
            _free_schema = _lib.secret_schema_unref
        else:
            _free_schema = _lib.secret_schema_free
        _free_schema.restype = None
        _free_schema.argtypes = [ctypes.c_void_p]
        _lib._free_schema = _free_schema

        _lib.secret_service_get_sync.restype = ctypes.c_void_p
        _lib.secret_service_get_sync.argtypes = [
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.POINTER(_GError)),
        ]

        _lib.secret_password_store_sync.restype = ctypes.c_int
        _lib.secret_password_store_sync.argtypes = [
            ctypes.c_void_p,  # schema
            ctypes.c_char_p,  # collection
            ctypes.c_char_p,  # label
            ctypes.c_char_p,  # password
            ctypes.c_void_p,  # cancellable
            ctypes.POINTER(ctypes.POINTER(_GError)),
        ]  # then attribute pairs, NULL-terminated (variadic)

        _lib.secret_password_lookup_sync.restype = ctypes.c_void_p
        _lib.secret_password_lookup_sync.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.POINTER(_GError)),
        ]  # then attribute pairs, NULL-terminated (variadic)

        _lib.secret_password_search_sync.restype = ctypes.POINTER(_GList)
        _lib.secret_password_search_sync.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,  # SecretSearchFlags
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.POINTER(_GError)),
        ]  # then attribute pairs, NULL-terminated (variadic)

        _lib.secret_item_get_attributes.restype = ctypes.c_void_p
        _lib.secret_item_get_attributes.argtypes = [ctypes.c_void_p]

        _lib.secret_item_delete_sync.restype = ctypes.c_int
        _lib.secret_item_delete_sync.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.POINTER(_GError)),
        ]

    def _schema() -> int:
        """The ZettelApp schema; the Secret Service matches items by its attributes."""
        schema = _lib.secret_schema_new(
            b"org.zettelapp.Secret",
            0,
            b"application",
            _SECRET_SCHEMA_ATTRIBUTE_STRING,
            b"name",
            _SECRET_SCHEMA_ATTRIBUTE_STRING,
            None,
        )
        if not schema:
            raise OSError(_("Could not talk to the system keyring."))
        return schema

    def _raise_gerror(error: _GError | None, fallback: str) -> None:
        if error is not None and error.message:
            raise OSError(error.code, error.message.decode("utf-8", errors="replace"))
        raise OSError(fallback)


def secrets_available() -> bool:
    """True when secrets persist securely (Credential Manager or the Secret Service)."""
    global _SERVICE_OK
    if IS_WINDOWS:
        return True
    if not IS_LINUX or _lib is None:
        return False
    if _SERVICE_OK is None:
        error = ctypes.POINTER(_GError)()
        service = _lib.secret_service_get_sync(0, None, ctypes.byref(error))
        if service:
            _lib.g_object_unref(service)
            _SERVICE_OK = True
        else:
            _SERVICE_OK = False
    return _SERVICE_OK


def _target(name: str) -> str:
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise ValueError(_("Invalid secret name."))
    return PREFIX + name


def _checked(name: str, value: str | None) -> str:
    target = _target(name)
    if not isinstance(value, str) or not value:
        raise ValueError(_("The secret is empty."))
    if IS_WINDOWS:
        blob = value.encode("utf-16-le")  # same encoding as Credential Manager's own UI
        if len(blob) > _MAX_BLOB:
            raise ValueError(_("The secret is too long."))
    elif len(value) > _MAX_LINUX_CHARS:
        raise ValueError(_("The secret is too long."))
    return target


def set_secret(name: str, value: str) -> None:
    target = _checked(name, value)
    if not secrets_available():
        _memory[target] = value
        return
    if IS_WINDOWS:
        blob = value.encode("utf-16-le")
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
                raise OSError(
                    ctypes.get_last_error(), _("Could not save to Windows Credential Manager.")
                )
        finally:
            ctypes.memset(buffer, 0, len(blob))
        return
    schema = _schema()
    error = ctypes.POINTER(_GError)()
    ok = _lib.secret_password_store_sync(
        schema,
        None,  # the default collection
        f"ZettelApp: {target}".encode(),
        value.encode("utf-8"),
        None,
        ctypes.byref(error),
        b"application",
        b"ZettelApp",
        b"name",
        target.encode("utf-8"),
        None,
    )
    _lib._free_schema(schema)
    if not ok:
        _raise_gerror(error, _("Could not save to the system keyring."))


def get_secret(name: str) -> str | None:
    target = _target(name)
    if not secrets_available():
        return _memory.get(target)
    if IS_WINDOWS:
        pointer = _PCREDENTIAL()
        if not _CredRead(target, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
            error = ctypes.get_last_error()
            if error == ERROR_NOT_FOUND:
                return None
            raise OSError(error, _("Could not read from Windows Credential Manager."))
        try:
            cred = pointer.contents
            blob = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize)
        finally:
            _CredFree(pointer)
        try:
            return blob.decode("utf-16-le")
        except UnicodeDecodeError:  # written by another tool as UTF-8
            return blob.decode("utf-8", errors="replace")
    schema = _schema()
    error = ctypes.POINTER(_GError)()
    pointer = _lib.secret_password_lookup_sync(
        schema,
        None,
        ctypes.byref(error),
        b"application",
        b"ZettelApp",
        b"name",
        target.encode("utf-8"),
        None,
    )
    _lib._free_schema(schema)
    if not pointer:
        if error:
            _raise_gerror(error, _("Could not read from the system keyring."))
        return None  # no such secret
    try:
        return ctypes.string_at(pointer).decode("utf-8")
    finally:
        _lib.g_free(pointer)


def delete_secret(name: str) -> None:
    target = _target(name)
    if not secrets_available():
        _memory.pop(target, None)
        return
    if IS_WINDOWS:
        if not _CredDelete(target, CRED_TYPE_GENERIC, 0):
            error = ctypes.get_last_error()
            if error != ERROR_NOT_FOUND:
                raise OSError(error, _("Could not remove from Windows Credential Manager."))
        return
    schema = _schema()
    error = ctypes.POINTER(_GError)()
    ok = _lib.secret_password_clear_sync(
        schema,
        None,
        ctypes.byref(error),
        b"application",
        b"ZettelApp",
        b"name",
        target.encode("utf-8"),
        None,
    )
    _lib._free_schema(schema)
    if not ok:
        _raise_gerror(error, _("Could not remove from the system keyring."))


def delete_all() -> int:
    """Remove every ZettelApp secret (when the user deletes their data). Returns how many."""
    if not secrets_available():
        doomed = [t for t in _memory if t.startswith(PREFIX)]
        for target in doomed:
            del _memory[target]
        return len(doomed)
    if IS_WINDOWS:
        count = wintypes.DWORD()
        found = ctypes.POINTER(_PCREDENTIAL)()
        if not _CredEnumerate(PREFIX + "*", 0, ctypes.byref(count), ctypes.byref(found)):
            return 0  # none stored (ERROR_NOT_FOUND)
        try:
            targets = [
                found[i].contents.TargetName
                for i in range(count.value)
                if found[i].contents.Type == CRED_TYPE_GENERIC
            ]
        finally:
            _CredFree(found)
        return sum(
            1
            for t in targets
            if t and t.startswith(PREFIX) and _CredDelete(t, CRED_TYPE_GENERIC, 0)
        )
    schema = _schema()
    error = ctypes.POINTER(_GError)()
    # UNLOCK | ALL | LOAD_SECRETS: the item may live in a locked collection and
    # gnome-keyring only returns the full set through the loading search path.
    items = _lib.secret_password_search_sync(
        schema,
        _SECRET_SEARCH_ALL | _SECRET_SEARCH_UNLOCK | _SECRET_SEARCH_LOAD_SECRETS,
        None,
        ctypes.byref(error),
        b"application",
        b"ZettelApp",
        None,
    )
    _lib._free_schema(schema)
    if not items:
        if error:
            _raise_gerror(error, _("Could not read from the system keyring."))
        return 0  # none stored
    prefix = PREFIX.encode("utf-8")
    count = 0
    node = items
    while node:
        item = node.contents.data
        if item:
            attributes = _lib.secret_item_get_attributes(ctypes.c_void_p(item))
            name_bytes = _lib.g_hash_table_lookup(attributes, b"name") if attributes else None
            if name_bytes and bytes(name_bytes).startswith(prefix):
                item_error = ctypes.POINTER(_GError)()
                if _lib.secret_item_delete_sync(
                    ctypes.c_void_p(item), None, ctypes.byref(item_error)
                ):
                    count += 1
            _lib.g_object_unref(ctypes.c_void_p(item))
        node = node.contents.next
    _lib.g_list_free(items)
    return count
