# Graph und Einblicke

## Der Graph

Die Seite **Graph** (Ctrl+2) stellt Ihre Notizen als Netzwerk dar: Jeder Kreis steht für eine Notiz, seine
Größe hängt von der Anzahl ihrer Links ab, und jede Linie ist ein Link.

![Der nach Tags eingefärbte Graph](../website/assets/screenshots/graph-light.png)

### Steuerelemente

| Steuerelement | Funktion |
|---|---|
| **Alle Notizen / Lokal** | Zeigt die gesamte Sammlung oder nur die geöffnete Notiz und Notizen innerhalb von **Tiefe** Links (Links in beide Richtungen verfolgend). *Im Graph anzeigen* im ⋯-Menü einer Notiz öffnet den lokalen Graph. |
| **2D / 3D** | Wechselt zwischen einer flachen, verschiebbaren Anordnung und einer 3D-Ansicht, die Sie umlaufen können. |
| **Färben nach** | Tags, *Cluster: k-means*, *Cluster: hierarchisch* oder keine Einfärbung. |
| **k** | Anzahl der Cluster. *k automatisch* wählt den Wert selbst aus (siehe unten). |
| **Gruppieren** | Zieht Notizen derselben Gruppe zusammen und schattiert den Bereich der jeweiligen Gruppe. |
| **Beschriftungen** | Zeigt Notiztitel. In großen Graphen werden zunächst nur die am stärksten verknüpften Notizen beschriftet; weitere Beschriftungen erscheinen beim Darüberfahren. |
| **Linktypen** | Blendet einzelne Linktypen ein oder aus. |
| **Im Graph suchen** | Geben Sie einen Teil eines Titels ein und drücken Sie Enter, um zur Notiz zu springen. |

Unten rechts finden Sie Zoom, Einpassen, **Layout neu berechnen**, **Als Bild speichern** (PNG) und **Diese
Notizen exportieren** (öffnet den [Export](export-import.md)-Dialog mit den sichtbaren Notizen).

**In 2D** ziehen Sie eine Notiz, um sie zu verschieben, den Hintergrund zum Verschieben der Ansicht und
verwenden das Mausrad zum Zoomen. Ein Doppelklick auf eine Notiz öffnet sie; mit der rechten Maustaste
öffnen Sie weitere Aktionen (öffnen, lokaler Graph, Quiz über die Nachbarschaft, Export mit verknüpften
Notizen). Das Bild einer Notiz erscheint in ihrem Kreis.

Mehrere Links zwischen denselben zwei Notizen werden als **separate Kurven** mit jeweils eigener
Pfeilspitze entlang der Kurve gezeichnet, sodass keiner den anderen verdeckt. Wenn Sie auf eine Notiz
zeigen oder sie auswählen, werden **die übrigen Links abgeblendet**; die eigenen Links der Notiz behalten
ihre Linktypfarben und die Nachbarn werden mit den Linktypen **aus Sicht dieser Notiz** beschriftet, zum
Beispiel *Unterstützt · Wird erweitert von*. Das funktioniert in 2D und 3D gleich.

**In 3D** ziehen Sie zum Umlaufen, verwenden das Mausrad zum Zoomen und doppelklicken eine Notiz, um sie zu
öffnen. **Automatisch drehen** lässt die Ansicht rotieren. Näher gelegene Notizen sind größer und heller,
sodass sich die Tiefe leicht ablesen lässt; jede Gruppe erscheint als weich eingefärbter Lichtschein.

Das Layout ist kraftgerichtet (Fruchterman–Reingold): Links ziehen Notizen zusammen, alle Notizen stoßen
einander ab und eine sanfte Schwerkraft hält getrennte Komponenten im sichtbaren Bereich. Es wird im
Hintergrund berechnet und pro Ansicht zwischengespeichert.

### Nach Tags einfärben

Jede Notiz erhält die Farbe ihres **häufigsten Tags** – also des Tags, den die meisten Notizen in der
Ansicht tragen. So bekommen die großen Themen Ihres Tresors eigene Farben.

### Nach Clustern einfärben

Clustering gruppiert Notizen **nach Bedeutung**, unabhängig davon, ob sie miteinander verknüpft sind. Jede
Notiz wird anhand von Titel, Text und Tags mithilfe der latenten semantischen Analyse (LSA) in einen
semantischen Vektorraum übertragen. Anschließend gruppiert eine von zwei Methoden die Vektoren:

- **k-means**: Lloyd-Algorithmus mit k-means++-Initialisierung, bestes Ergebnis aus mehreren Durchläufen. Schnell und mit runden, gleich großen Gruppen.
- **Hierarchisch**: agglomeratives Clustering mit Average Linkage anhand der Kosinusdistanz, berechnet mit dem Nearest-Neighbour-Chain-Algorithmus (O(n²)). Eignet sich besser für ungleich große, ineinander verschachtelte Themen. Tresore mit mehr als 4.000 Notizen verwenden stattdessen k-means.

Mit **k automatisch** probiert ZettelApp k von 2 bis ungefähr √(n/2) + 2 (höchstens 12) aus und behält
den Wert mit dem besten **Silhouettenwert** bei. Der unter der Legende angezeigte Wert misst, wie gut die
Cluster voneinander getrennt sind: 1 bedeutet perfekt, ungefähr 0 steht für überlappende Gruppen. Jedes
Cluster erhält einen Namen aus seinen markantesten Wörtern – den Begriffen, die darin häufiger vorkommen
als im Rest des Tresors.

### Gruppen und Farben

Wenn **Gruppieren** aktiviert ist, werden Notizen mit demselben Tag oder Cluster zueinander gezogen und jede
Gruppe erhält einen leicht schattierten Bereich mit Namen. Die Legende führt die Gruppen samt Anzahl auf.
Klicken Sie auf eine Gruppe, um ihre Notizen hervorzuheben.

Die Farben für Gruppen und Diagramme stammen aus einer Palette, die für Farbsehschwächen in hellem und
dunklem Modus **geprüft** wurde. Die Farben werden in fester Reihenfolge zugeordnet und nie wiederverwendet:
Gruppen ab der neunten teilen sich ein neutrales Grau namens „Andere“. **Linktypen** werden nicht nur durch
Farbe unterschieden: Jeder Typ hat eine eigene Linie (durchgezogen, gestrichelt, gepunktet usw.); gerichtete
Typen haben eine Pfeilspitze, zum Beispiel ein Dreieck oder eine Raute. Wählen Sie diese unter *Werkzeuge ▸
Optionen ▸ Linktypen* aus (siehe [Eigene Linktypen](notes-and-links.md#your-own-link-types)). Die Legende
benennt alles, damit die Bedeutung nicht allein von der Farbe abhängt.

## Einblicke

Die Seite **Einblicke** (Ctrl+3) fasst Ihren Tresor zusammen:

- **Kacheln**: Notizen (und deren Anzahl im Papierkorb), Links (und Links pro Notiz), Tags, *unverknüpfte Notizen* (gute Kandidaten für neue Verknüpfungen), Lernkarten und heute fällige Karten.
- **Pro Monat hinzugefügte Notizen** der letzten 12 Monate.
- **Häufigste Tags**, **Links nach Typ** und **Am stärksten verknüpfte Notizen** (klicken Sie auf einen Balken, um die Notiz zu öffnen).
- **Themen**: k-means-Cluster Ihrer Notizen mit Stichwörtern und Anzahl.

Jedes Diagramm hat eine Schaltfläche **Als Tabelle anzeigen** (Listensymbol), die dieselben Werte als Tabelle
darstellt. Wenn Sie auf einen Balken zeigen, wird dessen Wert angezeigt.
