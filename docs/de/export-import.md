# Export und Import

## Exportieren

Mit *Datei ▸ Exportieren…* (Ctrl+Shift+E) exportieren Sie **die gesamte Sammlung oder einen beliebigen Teil davon**:

| Bereich | Exportierter Inhalt |
|---|---|
| **Gesamte Sammlung** | Jede Notiz (außer dem Papierkorb). |
| **Aktuelle Notiz und verknüpfte Notizen** | Die geöffnete Notiz und alle Notizen innerhalb von **Tiefe** Links, wobei Links in beide Richtungen verfolgt werden: ein *Teilgraph*. |
| **Notizen mit Tag** | Notizen mit dem angegebenen Tag, einschließlich verschachtelter Tags (`math` umfasst `math/algebra`). |

Der Dialog zeigt, wie viele Notizen, Links und Lernkarten der ausgewählte Bereich enthält. Sie können auch
über die Notizliste exportieren (Rechtsklick ▸ *Mit verknüpften Notizen exportieren…*), über das ⋯-Menü
einer Notiz, über den Graph (die Export-Schaltfläche exportiert die sichtbaren Notizen) und über das Menü
eines Graphknotens.

### Formate

| Format | Datei | Inhalt |
|---|---|---|
| **ZettelApp-Archiv** | `.zip` | Alles, einschließlich Bildern: Notizen, typisierte Links, Linktypen (mit Farben, Linienstilen und Pfeilspitzen), Lernkarten und Mindmaps. Importieren Sie das Archiv auf einem beliebigen Computer wieder in ZettelApp. Am besten für Sicherungen und zum Verschieben von Tresoren. |
| **Markdown-Dateien** | `.zip` | Eine `.md`-Datei pro Notiz mit YAML-Frontmatter (ID, Titel, Tags, Quellenlink, Daten, typisierte Links, Mindmap) und `[[Wiki-Links]]` zwischen den Dateien. Links, die nicht im Text stehen, sind unter *Links* im Format `type:: [[Note]]` aufgeführt; manuelle Lernkarten unter *Lernkarten* im Format `Q:`/`A:`. Bilder liegen in `assets/`. Lässt sich in Obsidian und anderen Markdown-Editoren öffnen. |
| **Website** | `.zip` | Eine eigenständige statische Website: ein Index mit Graphübersicht, ein Tagindex und eine Seite pro Notiz. Links sind in den Farben und Linienstilen ihrer Typen dargestellt; hinzu kommen Mindmaps und Lernkarten (Antworten werden per Klick eingeblendet). Keine Skripte; funktioniert offline, indem Sie `index.html` öffnen. Helle und dunkle Designs. |
| **JSON** | `.json` | Strukturierte Daten für Skripte und andere Tools (Bilder werden referenziert, aber nicht mitgeliefert). |
| **GraphML** | `.graphml` | Der Linkgraph für Gephi, yEd, Cytoscape oder NetworkX, mit Titeln, Tags und Daten auf den Knoten und Linktypen auf den Kanten (gerichtet oder ungerichtet), einschließlich Farbe, Linienstil und Pfeilspitze jedes Typs. |
| **Graphviz DOT** | `.dot` | Der Graph als Graphviz-Diagramm mit farblich gekennzeichneten, beschrifteten und gestalteten Linktypen: durchgezogene, gestrichelte oder gepunktete Linien (Graphviz stellt Strich-Punkt und lange Striche gestrichelt dar) und Pfeilspitzen je Typ; ungerichtete Typen haben keine Pfeile. |
| **Anki-Deck** | `.apkg` | Die Lernkarten der exportierten Notizen. Siehe [Anki](review-and-anki.md#anki). |

Exporte werden in eine temporäre Datei geschrieben und erst nach vollständiger Erstellung an den
Zielspeicherort verschoben. Ein abgebrochener Export hinterlässt daher nie eine unvollständige Datei. Der
Export läuft im Hintergrund; **Im Ordner anzeigen** öffnet das Ergebnis im Datei-Explorer.

Mindmaps können außerdem in der Registerkarte **Mindmap** als PNG, SVG oder FreeMind-Datei (`.mm`)
exportiert werden. Der Graph lässt sich als PNG-Bild speichern.

## Importieren

*Datei ▸ Importieren…* akzeptiert:

- **ZettelApp-Archive** (`.zip`) und **JSON**-Exporte;
- **Markdown-Dateien** (`.md`) oder ein **`.zip`-Archiv mit Markdown-Dateien**;
- *Datei ▸ Markdown-Ordner importieren…* für einen Ordner mit Markdown-Dateien, zum Beispiel einen **Obsidian-Tresor**.

Was erhalten bleibt:

- **Aus ZettelApp-Archiven und JSON**: Notizen behalten ihre IDs, typisierten Links, Lernkarten, Mindmaps und Bilder. Linktypen, die im Tresor noch nicht vorhanden sind, werden samt Farben und Stilen hinzugefügt; vorhandene Typen behalten ihre Einstellungen. Beim erneuten Import desselben Archivs werden unveränderte Notizen übersprungen. Wird eine ID bereits von einer anderen Notiz verwendet, erhält der Import eine neue ID und aktualisiert die Links entsprechend.
- **Aus Markdown**:
  - Der Titel stammt aus dem Frontmatter-Feld `title`, der ersten `# Überschrift` oder dem Dateinamen.
  - Tags stammen aus dem Frontmatter-Feld `tags` und Inline-`#hashtags`.
  - Der Quellenlink stammt aus `url` oder `source`, das Erstellungsdatum aus `created`.
  - `[[Wiki-Links]]` (einschließlich Obsidian-Links mit Dateinamen) und `type:: [[Links]]` werden zu Links.
  - Bilder, die mit `![](path)` oder Obsidian-`![[image.png]]` referenziert werden, werden in den Tresor kopiert.
  - Versteckte Ordner wie `.obsidian` und `.trash` werden übersprungen.
  - ZettelApps eigener Markdown-Export wird mit typisierten Links, Lernkarten und Mindmaps wieder importiert.

### Sicherheit

Importierte Dateien werden als nicht vertrauenswürdig behandelt:

- Archivpfade werden geprüft, damit keine Dateien außerhalb des Importziels geschrieben werden können (kein „Zip Slip“).
- Archive mit zu vielen Dateien, zu großen Datenmengen oder verdächtigen Kompressionsverhältnissen („Dekompressionsbomben“) werden abgelehnt.
- Jedes Feld wird auf den richtigen Typ geprüft und in der Größe begrenzt.
- Bilder werden anhand ihres Inhalts erneut geprüft.
- Entfernte Bilder und Links zu anderen Orten auf der Festplatte werden nicht importiert.

Beim Öffnen eines Tresors wird täglich eine Sicherung erstellt. Sie können jederzeit über *Datei ▸ Tresor
jetzt sichern* eine erstellen. Siehe [Datenschutz und Sicherheit](privacy-and-security.md).
