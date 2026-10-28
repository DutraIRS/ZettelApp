# MCP-Server

Das [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) ist ein offener Standard, über den
KI-Assistenten Tools und Daten anderer Programme verwenden können. ZettelApp enthält einen MCP-Server.
Damit können Assistenten wie **Claude Desktop** und **Claude Code** Ihren Zettelkasten durchsuchen,
Notizen lesen, typisierten Links folgen und während der Zusammenarbeit Linkvorschläge anfordern.

## Funktionsweise

Der Server ist ein separates kleines Programm, **`zettelapp-mcp.exe`**, das neben `ZettelApp.exe`
installiert wird. Aus dem Quellcode wird derselbe Server mit `python -m zettelapp.mcp_main` gestartet.
Ihr MCP-Client startet ihn bei Bedarf und kommuniziert über die Standardein- und -ausgabe mit ihm. **Es
wird kein Netzwerkport geöffnet.**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

Ohne `--vault` stellt der Server den Tresor bereit, den Sie zuletzt in ZettelApp geöffnet haben. Änderungen
über MCP erscheinen innerhalb weniger Sekunden in der App.

## Der MCP-Schalter

MCP-Clients können nur dann auf Ihre Notizen zugreifen, wenn **ZettelApp geöffnet und der MCP-Schalter in
der Statusleiste eingeschaltet ist**. Bei jedem Start von ZettelApp ist der Schalter **ausgeschaltet**.
Sie entscheiden also für jede Sitzung, ob Assistenten Ihre Notizen lesen dürfen. Schalten Sie ihn aus oder
schließen Sie ZettelApp, und der Server stoppt innerhalb etwa einer Sekunde. Ohne den Schalter verweigert
der Server den Start und nennt den Grund. Das genaue Verhalten ist in der [MCP-API-Referenz](mcp-reference.md)
beschrieben.

## Claude Desktop verbinden

Öffnen Sie *Werkzeuge ▸ Optionen ▸ MCP-Server* und klicken Sie auf **Zu Claude Desktop hinzufügen…**.
ZettelApp trägt sich in `%APPDATA%\Claude\claude_desktop_config.json` ein (und sichert die bisherige Datei).
Starten Sie anschließend Claude Desktop neu. Aktivieren Sie den **MCP-Schalter** in der Statusleiste von
ZettelApp, bevor Sie Claude Desktop starten. Wenn Sie den Schalter erst später aktivieren, verbinden Sie
ZettelApp in Claude Desktop erneut oder starten Sie Claude Desktop neu. Um die Einrichtung manuell
vorzunehmen, kopieren Sie den auf dieser Seite angezeigten Ausschnitt in die Datei. Er sieht so aus:

```json
{
  "mcpServers": {
    "zettelapp": {
      "command": "C:\\Users\\me\\AppData\\Local\\Programs\\ZettelApp\\zettelapp-mcp.exe",
      "args": ["--vault", "C:\\Users\\me\\Documents\\ZettelApp"]
    }
  }
}
```

## Claude Code verbinden

Dieselbe Seite unter „Optionen“ zeigt den zu kopierenden Befehl:

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

Andere MCP-Clients benötigen denselben Befehl und dieselben Argumente. Wie bei Claude Desktop schalten Sie
MCP zunächst in ZettelApp ein. Wenn Sie den Schalter erst danach aktivieren, verbinden Sie den Server in
Ihrem Client erneut (in Claude Code mit `/mcp`).

## Tools

| Tool | Funktion |
|---|---|
| `search_notes` | Volltextsuche in Titeln, Text und Tags (Filter wie `tag:name` funktionieren). Eine leere Anfrage listet zuletzt bearbeitete Notizen auf. |
| `get_note` | Vollständiger Text, Tags, Quellenlink, Daten, typisierte Links in beide Richtungen, Lernkarten und Mindmap-Gliederung einer Notiz. |
| `list_tags` | Alle Tags mit der Anzahl der Notizen, die sie verwenden. |
| `get_subgraph` | Notizen innerhalb von 1–4 Links zu einer Notiz sowie die typisierten Verbindungen dazwischen (optional nur ausgewählte Linktypen). |
| `suggest_links` | Noch nicht verknüpfte Notizen, die wahrscheinlich zu einer Notiz passen, sortiert nach dem [Naive-Bayes-Vorschlag](link-suggestions.md). |
| `list_link_types` | Die Linktypen im Tresor, etwa *unterstützt*, *widerspricht* und *Teil von*. |
| `create_note` | *(schreibt)* Erstellt eine Notiz. `[[Title]]` im Text verknüpft bestehende Notizen. |
| `add_link` | *(schreibt)* Fügt einen typisierten Link von einer Notiz zu einer anderen hinzu. |

## Standardmäßig schreibgeschützt

Der Server öffnet Ihren Tresor **schreibgeschützt**. Die beiden Schreib-Tools werden nur angeboten, wenn
**beide** folgenden Bedingungen erfüllt sind:

1. Die Option **MCP-Clients dürfen Notizen und Links erstellen** ist unter *Optionen ▸ MCP-Server* aktiviert.
2. Der Server wurde mit `--allow-writes` gestartet. Sobald Sie die Option aktivieren, enthält der Ausschnitt auf der Seite „Optionen“ diese Option.

Die Einstellung wird bei jedem Schreibvorgang erneut geprüft; wenn Sie sie deaktivieren, wirkt das sofort.
Wenn Sie sie aktivieren, muss der MCP-Client den Server neu starten.

Notizinhalte werden dem Assistenten als Daten übergeben, und der Server weist ihn an, sie nicht als
Anweisungen zu behandeln. Eingaben (IDs, Größen und Grenzwerte) werden validiert; der Server greift nie auf
Dateien außerhalb des Tresors zu.

## Fehlerbehebung

- **Der Client meldet, dass der Server nicht gestartet werden konnte, oder Tool-Aufrufe melden, dass der Schalter ausgeschaltet ist.** Öffnen Sie ZettelApp, schalten Sie MCP in der Statusleiste ein und verbinden Sie den Server in Ihrem Client erneut.
- **Der Server lässt sich weiterhin nicht starten.** Prüfen Sie, ob der Pfad zu `zettelapp-mcp.exe` stimmt. Führen Sie den Befehl selbst in einem Terminal aus: Auf der Standardfehlerausgabe steht, was nicht stimmt (zum Beispiel „No ZettelApp vault found“).
- **Schreib-Tools fehlen.** Aktivieren Sie die Option *und* fügen Sie `--allow-writes` hinzu; starten Sie anschließend den Client neu.
