# Linkvorschläge

Während Sie schreiben, listet der Bereich **Linkvorschläge** Notizen auf, die wahrscheinlich zu der gerade
bearbeiteten Notiz passen. Klicken Sie auf **Verknüpfen**, um sie zu verbinden (mit dem Pfeil daneben
wählen Sie den Linktyp), oder auf **✕**, um einen Vorschlag zu verwerfen. Beides bringt dem Modell etwas
bei. Wenn Sie auf einen Vorschlag zeigen, sehen Sie, *warum* er vorgeschlagen wurde.

Die Vorschläge werden etwa eine Sekunde, nachdem Sie mit dem Tippen aufgehört haben, im Hintergrund
aktualisiert. Der Editor muss nicht darauf warten. Auch ungespeicherter Text wird berücksichtigt.

## Funktionsweise

ZettelApp behandelt die Frage „Sollten diese beiden Notizen verknüpft werden?“ als Klassifizierungsproblem
und beantwortet sie mit einem **Naive-Bayes-Klassifikator**. Für eine Notiz *q* und jeden möglichen
Kandidaten *c* berechnet der Klassifikator acht Ähnlichkeitsmerkmale und kombiniert die Belege zu einer
Wahrscheinlichkeit.

### Merkmale

| Merkmal | Was es misst |
|---|---|
| **Semantische Ähnlichkeit (LSA)** | Kosinusähnlichkeit in einem latenten semantischen Raum: eine gekürzte SVD der TF-IDF-Matrix (randomisierte SVD mit bis zu 64 Dimensionen). Notizen mit verwandtem Vokabular liegen nahe beieinander, selbst wenn sie nur wenige identische Wörter enthalten. |
| **Gemeinsame Stichwörter (TF-IDF-Kosinus)** | Kosinusähnlichkeit der TF-IDF-Vektoren (sublineare Termhäufigkeit, geglättete inverse Dokumenthäufigkeit). Titel zählen doppelt; Tags werden einbezogen. |
| **Titelähnlichkeit (Levenshtein)** | 1 − Bearbeitungsabstand ÷ Länge des längeren Titels. |
| **Titelähnlichkeit (Jaro-Winkler)** | Jaro-Winkler-Ähnlichkeit der Titel, die einen gemeinsamen Anfang stärker gewichtet. |
| **Textähnlichkeit (Levenshtein)** | Normalisierter Bearbeitungsabstand zwischen den ersten 400 Zeichen der beiden Texte. |
| **Gemeinsame Tags (Jaccard)** | Gemeinsame Tags ÷ alle Tags. |
| **Titel im Text erwähnt** | 1, wenn der Titel einer Notiz im Text der anderen als ganzes Wort vorkommt; andernfalls 0. |
| **Gemeinsame Links (Jaccard)** | Überschneidung zwischen den verknüpften Notizen beider Notizen (schließt Dreiecke im Graph). |

Text wird kleingeschrieben, Akzente werden vereinheitlicht (sodass *informação* zu *informacao* passt),
Markdown-Syntax wird entfernt und häufige englische, portugiesische und spanische Stoppwörter werden
ignoriert. Bearbeitungsabstände werden mit [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) berechnet;
wenn es nicht verfügbar ist, liefert ein reiner Python-Bitparallelalgorithmus dieselben Ergebnisse.

### Von Merkmalen zu einer Wahrscheinlichkeit

Jeder Merkmalswert (zwischen 0 und 1) wird einem von **8 Intervallen** zugeordnet. Für jedes Merkmal merkt
sich das Modell, wie häufig verknüpfte und nicht verknüpfte Paare in jedes Intervall fallen, und schätzt:

```text
P(link | f1 … f8)  ∝  P(link) × Π P(fi | link)
```

Der **Belegwert** eines Merkmals ist das logarithmische Wahrscheinlichkeitsverhältnis:
log P(bin | link) − log P(bin | no link). Die angezeigte Wahrscheinlichkeit ist die logistische Funktion
der vorherigen Log-Odds plus der (gewichteten) Summe der Belegwerte.

**Woher die Anzahlen stammen.** Das Modell trainiert jedes Mal mit Ihrem Tresor, wenn sich dieser deutlich
verändert:

- **Positive Beispiele**: jedes Paar verknüpfter Notizen sowie angenommene Vorschläge (in sehr großen Tresoren werden bis zu 600 Paare ausgewählt);
- **Negative Beispiele**: zufällige Paare nicht verknüpfter Notizen, drei pro positivem Beispiel, sowie jeder von Ihnen **abgelehnte** Vorschlag, der doppelt zählt.

**Ein Prior, der vom ersten Tag an funktioniert.** Bevor Daten vorhanden sind, beginnt jedes Intervall mit
Dirichlet-**Pseudozählungen** (standardmäßig 10 pro Merkmal und Klasse). Sie kodieren eine schwache
Annahme: Bei verknüpften Paaren steigen die Zählungen mit der Ähnlichkeit, bei nicht verknüpften Paaren
fallen sie stark ab. Das reicht aus, um Vorschläge in einem neuen Tresor zu sortieren. Wenn Sie Notizen
verknüpfen, überwiegen echte Zählungen den Prior und das Modell passt sich an *Ihre* Verknüpfungsweise an.
Da positive und negative Beispiele im Verhältnis eins zu drei ausgewählt werden, liegt der Klassenprior
P(link) (bei passenden Pseudozählungen) bei etwa einem Viertel.

**Zwei Korrekturen sorgen für verlässliche Schätzungen:**

1. **Keine Informationslecks durch Labels.** `[[Wiki links]]` werden aus dem Text entfernt, bevor Merkmale berechnet werden. Andernfalls würde ein Inline-Link den Titel des Ziels in den Text aufnehmen und das Modell würde bestehende Links statt verwandter Ideen erkennen lernen. Aus demselben Grund ignoriert das Merkmal „gemeinsame Links“ beim Training mit einem verknüpften Paar den Link zwischen den beiden Notizen.
2. **Gewichtung korrelierter Belege.** Naive Bayes setzt unabhängige Merkmale voraus, einige sind es aber nicht: TF-IDF und LSA überschneiden sich, ebenso die drei Zeichenkettenabstände. Wenn korrelierte Belege als unabhängig gezählt werden, wird gewöhnliches Naive Bayes übermäßig selbstsicher. Deshalb multipliziert ZettelApp jeden Belegwert mit **0.6** (merkmalgewichtetes Naive Bayes); so bleiben die Wahrscheinlichkeiten realistisch.

**Fehlende oder deaktivierte Merkmale liefern keinen Beleg.** Wenn Sie ein Merkmal ausschalten oder es nicht
berechnet werden kann, trägt es nichts bei – genau so behandelt Naive Bayes fehlende Werte auf natürliche
Weise.

### Schnelles Sortieren

Der Vergleich langer Texte per Levenshtein-Abstand ist der langsamste Schritt; deshalb wird in zwei Stufen
sortiert. Zunächst werden alle Kandidaten ohne das Merkmal Textähnlichkeit bewertet, und nur die besten
150 erhalten die vollständige Bewertung. Bereits verknüpfte Kandidaten und Paare, die Sie abgelehnt haben,
werden nie vorgeschlagen.

## Den Tooltip „Warum“ lesen

Zeigen Sie auf einen Vorschlag, um die Schätzung des Modells und den Belegwert jedes Merkmals zu sehen.
Positive Zahlen sprechen für einen Link, negative dagegen. Die Beschriftung neben dem Balken fasst die
Wahrscheinlichkeit zusammen: **stark** (50 % oder mehr), **wahrscheinlich** (25 % oder mehr) oder **möglich**.

Die Wahrscheinlichkeiten sind ehrliche Schätzungen. In einem spärlich gefüllten Tresor sind die meisten
Notizpaare tatsächlich nicht verknüpft; 15–30 % können also ein guter Vorschlag sein. Am wichtigsten ist
die Reihenfolge.

## Abstimmen

Unter *Werkzeuge ▸ Optionen ▸ Linkvorschläge*:

| Option | Standard | Wirkung |
|---|---|---|
| Beim Schreiben Links vorschlagen | ein | Schaltet die Vorschläge im Bereich vollständig aus. |
| Merkmale | alle acht | Deaktivieren Sie Merkmale, die nicht berücksichtigt werden sollen. |
| Höchstens anzeigen | 8 | Anzahl der angezeigten Vorschläge. |
| Mindestübereinstimmung | 10% | Blendet Vorschläge unterhalb dieser Wahrscheinlichkeit aus. |
| Priorstärke | 10 | Anzahl der Pseudobeobachtungen, auf die sich der Prior stützt. Höhere Werte bedeuten, dass der Prior länger gilt; niedrigere Werte führen dazu, dass das Modell sich schneller an Ihre Links anpasst. |

- **Modelldetails…** zeigt die Anzahl der verknüpften und nicht verknüpften Paare, mit denen das Modell trainiert wurde, und wie informativ jedes Merkmal ist (die symmetrische Kullback–Leibler-Divergenz zwischen den Verteilungen für verknüpfte und nicht verknüpfte Paare).
- **Abgelehnte Vorschläge vergessen** löscht Ihre Ablehnungen. Diese Paare können dann wieder vorgeschlagen werden und zählen nicht mehr als negative Beispiele.
