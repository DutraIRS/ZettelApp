import struct
import zlib

import pytest

from zettelapp.core.storage import Vault


@pytest.fixture
def vault(tmp_path):
    v = Vault.open(tmp_path / "vault")
    yield v
    v.close()


def tiny_png(color=(15, 108, 189)) -> bytes:
    """A valid 1x1 PNG."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    raw = b"\x00" + bytes(color)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


@pytest.fixture
def sample(vault):
    """A small Zettelkasten about learning."""
    a = vault.create_note(
        "Spaced repetition",
        "Reviewing material at increasing intervals improves "
        "long-term memory retention. See [[Forgetting curve]].\n\nQ: Who described the "
        "forgetting curve?\nA: Hermann Ebbinghaus",
        tags=["learning", "memory"],
    )
    b = vault.create_note(
        "Forgetting curve",
        "Memory retention decays exponentially over time unless "
        "the material is reviewed. Ebbinghaus measured it.",
        tags=["memory"],
    )
    c = vault.create_note(
        "Active recall",
        "Testing yourself (retrieval practice) strengthens memory "
        "more than rereading. {{c1::Retrieval practice}} is also called active recall.",
        tags=["learning"],
    )
    d = vault.create_note(
        "Sourdough bread",
        "Flour, water, salt and a starter. Long fermentation develops flavour.",
        tags=["cooking"],
    )
    e = vault.create_note(
        "Interleaving",
        "Mixing different topics during practice improves learning and "
        "memory transfer compared with blocked practice.",
        tags=["learning"],
    )
    vault.add_link(c.id, a.id, "supports")
    vault.add_link(e.id, a.id, "related")
    return {"a": a, "b": b, "c": c, "d": d, "e": e}
