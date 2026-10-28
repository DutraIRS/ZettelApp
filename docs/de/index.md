# ZettelApp-Dokumentation

ZettelApp ist ein Zettelkasten für Windows: ein Netzwerk aus kleinen Notizen, die jeweils eine Idee enthalten und durch Links verbunden sind, die erklären, *wie* die Ideen zusammenhängen. Beim Schreiben schlägt die App Links vor, stellt Ihr Wissen als 2D- oder 3D-Graph dar, macht aus Notizen Lernkarten und Quizfragen und funktioniert mit Anki, Zotero und KI-Assistenten.

Alles bleibt auf Ihrem Computer, außer wenn Sie etwas anfordern, das eine Netzwerkverbindung benötigt.

## Neu hier?

- **[Was ist ein Zettelkasten?](what-is-zettelkasten.md)**: die Methode, ihre Herkunft und wie ZettelApp sie unterstützt.
- **[Tutorial: Ihre ersten 30 Minuten](tutorial.md)**: eine praktische Einführung von der ersten Notiz bis zum 3D-Graphen.

## Inhalt

- [Erste Schritte](getting-started.md): Installation, Ihr erster Tresor und ein Rundgang durch das Fenster
- [Notizen und Links](notes-and-links.md): Markdown, Wiki-Links, typisierte und gerichtete Links, Tags, Bilder, Mindmaps, Lernkarten, Suche und der Papierkorb
- [Linkvorschläge](link-suggestions.md): wie der Naive-Bayes-Vorschlag funktioniert und wie Sie ihn abstimmen
- [Graph und Einblicke](graph-and-insights.md): 2D- und 3D-Graphen, Clustering, Gruppierung und Diagramme
- [Wiederholung, Quizfragen und Anki](review-and-anki.md): verteiltes Wiederholen, Quizmodi, Anki-Synchronisierung und Decks
- [Zotero](zotero.md): Referenzen zitieren und Literatur-Notizen schreiben
- [Fragen Sie Ihre Notizen (KI)](ai-assistant.md): Antworten von Claude, OpenAI oder Z.ai, gestützt auf Ihre Notizen
- [MCP-Server](mcp-server.md): Claude Desktop, Claude Code und andere MCP-Clients den Tresor lesen lassen
- [MCP-API-Referenz](mcp-reference.md): Protokoll, Tools und Fehler – für Entwickler von MCP-Clients
- [Export und Import](export-import.md): die gesamte Sammlung oder einen beliebigen Teilgraphen in sieben Formaten
- [Tastenkombinationen](keyboard-shortcuts.md)
- [Datenschutz und Sicherheit](privacy-and-security.md): was Ihren Computer verlässt, wo Ihre Daten liegen und wie ZettelApp sie schützt
- [Entwicklung](development.md): aus dem Quellcode erstellen, Tests ausführen und eine Version paketieren
- [FAQ](faq.md)

## Die Ideen dahinter

Ein **Zettelkasten** (deutsch für „slip box“, etwa „Zettelbox“) ist eine Notizmethode, die durch den Soziologen Niklas Luhmann bekannt wurde. Jede Notiz ist *atomar* (eine Idee, in eigenen Worten) und hat eine dauerhafte ID. Der Wert entsteht durch die Verbindungen: Wenn Sie eine neue Notiz mit vorhandenen verknüpfen, müssen Sie darüber nachdenken, wie die Ideen zusammenhängen. Später können Sie diesen Links folgen und unerwartete Kombinationen entdecken.

ZettelApp bewahrt diese Disziplin und beseitigt zugleich unnötige Hürden:

- **IDs werden automatisch vergeben**: Jede Notiz erhält eine Zeitstempel-ID wie `20261027153012`.
- **Links können ausdrücken, wie Notizen zusammenhängen**: *unterstützt*, *widerspricht*, *erweitert*, *Beispiel für*, *Teil von*, *zitiert* oder Ihre eigenen Linktypen.
- **Vorschläge machen übersehene Verbindungen sichtbar**: Ein Klassifikator vergleicht eine Notiz mit dem übrigen Tresor und lernt aus Links, die Sie annehmen oder verwerfen.
- **Wiederholung ist integriert**: Aus Notizen werden Lernkarten und Quizfragen, mit verteiltem Wiederholen oder Anki.
