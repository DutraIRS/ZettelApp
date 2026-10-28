import io
import json
import sys

from zettelapp import mcp_main, mcp_server
from zettelapp.mcp_server import PROTOCOL_VERSIONS, ZettelMcpServer

READ_TOOLS = {"search_notes", "get_note", "list_tags", "get_subgraph", "suggest_links", "list_link_types"}


def run(server, *messages):
    raw = b"".join((m if isinstance(m, bytes) else json.dumps(m).encode()) + b"\n" for m in messages)
    out = io.BytesIO()
    server.serve(io.BytesIO(raw), out)
    return [json.loads(line) for line in out.getvalue().splitlines()]


def req(msg_id, method, params=None):
    message = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


def call(server, name, arguments):
    (reply,) = run(server, req(1, "tools/call", {"name": name, "arguments": arguments}))
    return reply


def test_handshake(vault):
    server = ZettelMcpServer(vault, writes_enabled=lambda: False)
    (init,) = run(server, req(1, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                                "clientInfo": {"name": "test", "version": "1"}}))
    result = init["result"]
    assert result["protocolVersion"] == "2025-06-18"
    assert result["capabilities"] == {"tools": {"listChanged": False}}
    assert result["serverInfo"]["name"] == "zettelapp" and result["instructions"]
    (newer,) = run(server, req(2, "initialize", {"protocolVersion": "2099-01-01"}))
    assert newer["result"]["protocolVersion"] == PROTOCOL_VERSIONS[0]
    replies = run(server, {"jsonrpc": "2.0", "method": "notifications/initialized"}, req(3, "ping"))
    assert replies == [{"jsonrpc": "2.0", "id": 3, "result": {}}]


def test_read_only_by_default(vault, sample):
    server = ZettelMcpServer(vault, allow_writes=False, writes_enabled=lambda: True)
    (listing,) = run(server, req(1, "tools/list"))
    tools = listing["result"]["tools"]
    assert {t["name"] for t in tools} == READ_TOOLS
    assert all(t["annotations"]["readOnlyHint"] and t["inputSchema"]["type"] == "object" for t in tools)
    assert call(server, "create_note", {"title": "x"})["error"]["code"] == -32602
    assert vault.count_notes() == 5


def test_writes_need_flag_and_setting(vault, sample):
    switch = {"on": True}
    server = ZettelMcpServer(vault, allow_writes=True, writes_enabled=lambda: switch["on"])
    (listing,) = run(server, req(1, "tools/list"))
    assert {"create_note", "add_link"} <= {t["name"] for t in listing["result"]["tools"]}
    created = call(server, "create_note", {"title": "From MCP", "body": "See [[Forgetting curve]]", "tags": ["mcp"]})
    new_id = created["result"]["structuredContent"]["id"]
    assert vault.get_note(new_id).tags == ["mcp"]
    assert vault.links_from(new_id)[0].dst == sample["b"].id
    linked = call(server, "add_link", {"src": new_id, "dst": sample["a"].id, "type": "supports"})
    assert linked["result"]["structuredContent"]["added"] is True
    bad_type = call(server, "add_link", {"src": new_id, "dst": sample["a"].id, "type": "nonsense"})
    assert bad_type["result"]["isError"] is True
    switch["on"] = False  # the user turns the option off while the server runs
    assert "error" in call(server, "create_note", {"title": "Blocked"})
    assert vault.count_notes() == 6


def test_search_and_get_note(vault, sample):
    server = ZettelMcpServer(vault)
    found = call(server, "search_notes", {"query": "memory", "limit": 3})["result"]
    ids = [r["id"] for r in found["structuredContent"]["results"]]
    assert ids and len(ids) <= 3 and sample["d"].id not in ids
    assert json.loads(found["content"][0]["text"]) == found["structuredContent"]
    tagged = call(server, "search_notes", {"query": "tag:cooking"})["result"]["structuredContent"]
    assert [r["id"] for r in tagged["results"]] == [sample["d"].id]

    note = call(server, "get_note", {"id": sample["a"].id})["result"]["structuredContent"]
    assert note["title"] == "Spaced repetition" and note["tags"] == ["learning", "memory"]
    assert (sample["c"].id, "Supported by") in {(l["id"], l["label"]) for l in note["links_in"]}
    assert sample["b"].id in {l["id"] for l in note["links_out"]}
    assert note["flashcards"][0]["front"] == "Who described the forgetting curve?"


def test_graph_tools(vault, sample):
    server = ZettelMcpServer(vault)
    tags = call(server, "list_tags", {})["result"]["structuredContent"]["tags"]
    assert {"tag": "learning", "count": 3} in tags
    sub = call(server, "get_subgraph", {"id": sample["c"].id, "depth": 2})["result"]["structuredContent"]
    assert {n["id"] for n in sub["nodes"]} == {sample[k].id for k in "abce"}
    only = call(server, "get_subgraph", {"id": sample["c"].id, "depth": 3, "link_types": ["supports"]})
    assert {n["id"] for n in only["result"]["structuredContent"]["nodes"]} == {sample["c"].id, sample["a"].id}
    suggestions = call(server, "suggest_links", {"id": sample["b"].id, "limit": 3})["result"]["structuredContent"]
    assert len(suggestions["suggestions"]) <= 3
    assert all(s["id"] != sample["b"].id for s in suggestions["suggestions"])
    types = call(server, "list_link_types", {})["result"]["structuredContent"]["link_types"]
    assert "supports" in {t["id"] for t in types}


def test_protocol_errors(vault):
    server = ZettelMcpServer(vault)
    replies = run(
        server,
        b"{not json",
        req(2, "resources/list"),
        req(3, "tools/call", {"name": "get_note", "arguments": {"id": "../../etc"}}),
        req(4, "tools/call", {"name": "get_note", "arguments": {"id": "20261027120000", "extra": 1}}),
        {"jsonrpc": "2.0", "method": "unknown/notification"},
        req(5, "tools/call", {"name": "no_such_tool"}),
        [req(6, "ping"), req(7, "ping")],
        req(8, "tools/call", {"name": "search_notes", "arguments": {"query": "x", "limit": "ten"}}),
        req(9, "tools/call", {"name": "get_note", "arguments": {"id": "20000101000000"}}),
        {"jsonrpc": "1.0", "id": 10, "method": "ping"},
    )
    assert replies[0]["error"]["code"] == -32700
    assert replies[1]["error"]["code"] == -32601
    assert replies[2]["result"]["isError"] is True
    assert replies[3]["result"]["isError"] is True
    assert replies[4]["error"]["code"] == -32602  # the notification produced no reply
    assert [r["id"] for r in replies[5]] == [6, 7]
    assert replies[6]["result"]["isError"] is True
    assert "No note" in replies[7]["result"]["content"][0]["text"]
    assert replies[8]["error"]["code"] == -32600


def test_oversized_message_is_skipped(vault, monkeypatch):
    monkeypatch.setattr(mcp_server, "MAX_MESSAGE_BYTES", 100)
    server = ZettelMcpServer(vault)
    big = b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{"x":"' + b"a" * 500 + b'"}}'
    replies = run(server, big, req(2, "ping"))
    assert replies[0]["error"]["code"] == -32600
    assert replies[1] == {"jsonrpc": "2.0", "id": 2, "result": {}}


class _Std:
    def __init__(self, data: bytes = b""):
        self.buffer = io.BytesIO(data)


def _run_main(monkeypatch, args, setting, messages):
    stdin = _Std(b"".join(json.dumps(m).encode() + b"\n" for m in messages))
    stdout = _Std()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(mcp_main, "_settings_allow_writes", lambda: setting)
    monkeypatch.setattr(mcp_server, "_settings_allow_writes", lambda: setting)
    code = mcp_main.main(args)
    return code, [json.loads(line) for line in stdout.buffer.getvalue().splitlines()]


def test_main_entry_point(vault, sample, monkeypatch, tmp_path):
    listing = [req(1, "tools/list")]
    code, replies = _run_main(monkeypatch, ["--vault", str(vault.folder)], True, listing)
    assert code == 0 and {t["name"] for t in replies[0]["result"]["tools"]} == READ_TOOLS
    code, replies = _run_main(monkeypatch, ["--vault", str(vault.folder), "--allow-writes"], False, listing)
    assert {t["name"] for t in replies[0]["result"]["tools"]} == READ_TOOLS  # option off in the app
    code, replies = _run_main(monkeypatch, ["--vault", str(vault.folder), "--allow-writes"], True, listing)
    assert "create_note" in {t["name"] for t in replies[0]["result"]["tools"]}
    code, _ = _run_main(monkeypatch, ["--vault", str(tmp_path / "missing")], False, listing)
    assert code == 2
