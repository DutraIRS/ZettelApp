# Esportazione e importazione

## Esportazione

*File ▸ Esporta…* (Ctrl+Shift+E) esporta **l'intera raccolta o una sua parte qualsiasi**:

| Ambito | Cosa viene esportato |
|---|---|
| **Intera raccolta** | Ogni nota (esclusa quella nel Cestino). |
| **Nota corrente e note collegate** | La nota aperta e le note entro **Profondità** collegamenti da essa, seguendo i collegamenti in entrambe le direzioni: un *sottografo*. |
| **Note con tag** | Le note con il tag, inclusi i tag annidati (`math` include `math/algebra`). |

La finestra di dialogo mostra quante note, collegamenti e flashcard contiene l'ambito. Puoi esportare anche dall'
elenco delle note (clic destro ▸ *Esporta con le note collegate…*), dal menu ⋯ di una nota, dal grafo (il pulsante di
esportazione esporta le note sullo schermo) e dal menu di un nodo del grafo.

### Formati

| Formato | File | Contenuto |
|---|---|---|
| **Archivio ZettelApp** | `.zip` | Tutto, comprese le immagini: note, collegamenti tipizzati, tipi di collegamento (con i loro colori, stili di linea e punte di freccia), flashcard, mappe mentali. Reimportalo in ZettelApp su qualsiasi computer. Ideale per backup e per spostare i vault. |
| **File Markdown** | `.zip` | Un file `.md` per nota con front matter YAML (id, titolo, tag, collegamento alla fonte, date, collegamenti tipizzati, mappa mentale) e `[[collegamenti wiki]]` tra i file. I collegamenti non scritti nel testo sono elencati sotto *Links* come `type:: [[Note]]` e le flashcard manuali sotto *Flashcards* come `Q:`/`A:`. Le immagini sono in `assets/`. Si apre in Obsidian e in altri editor Markdown. |
| **Sito web** | `.zip` | Un sito web statico autonomo: un indice con una panoramica del grafo, un indice dei tag e una pagina per nota, con collegamenti disegnati nei colori e negli stili di linea dei loro tipi, mappe mentali e flashcard (risposte rivelate con un clic). Nessuno script; funziona offline aprendo `index.html`. Temi chiaro e scuro. |
| **JSON** | `.json` | Dati strutturati per script e altri strumenti (immagini referenziate, non incluse). |
| **GraphML** | `.graphml` | Il grafo dei collegamenti per Gephi, yEd, Cytoscape o NetworkX, con titoli, tag e date sui nodi e tipi di collegamento sugli archi (orientati o no), con colore, stile di linea e punta di freccia di ciascun tipo. |
| **Graphviz DOT** | `.dot` | Il grafo come diagramma Graphviz, con i tipi di collegamento colorati, etichettati e stilizzati: linee continue, tratteggiate o punteggiate (Graphviz disegna tratteggiate le linee tratto-punto e a tratto lungo) e la punta di freccia di ciascun tipo; i tipi non orientati non hanno frecce. |
| **Mazzo Anki** | `.apkg` | Le flashcard delle note esportate. Vedi [Anki](review-and-anki.md#anki). |

Le esportazioni vengono scritte in un file temporaneo e spostate al loro posto solo quando sono complete, quindi un'esportazione
interrotta non lascia mai un file scritto a metà. Vengono eseguite in background e **Mostra nella cartella** rivela il
risultato in Esplora file.

Le mappe mentali hanno anche una propria esportazione (PNG, SVG o FreeMind `.mm`) nella scheda **Mappa mentale**, e il grafo
può essere salvato come immagine PNG.

## Importazione

*File ▸ Importa…* accetta:

- **archivi ZettelApp** (`.zip`) ed esportazioni **JSON**;
- **file Markdown** (`.md`) o uno **`.zip` di file Markdown**;
- *File ▸ Importa cartella Markdown…* per una cartella di file Markdown, come un **vault di Obsidian**.

Cosa viene mantenuto:

- **Da archivi ZettelApp e JSON:** le note mantengono i loro ID, collegamenti tipizzati, flashcard, mappe mentali e
  immagini. I tipi di collegamento che il vault non ha ancora vengono aggiunti con i loro colori e stili; quelli che ha
  mantengono i propri. Importare due volte lo stesso archivio salta le note che non sono cambiate. Se un ID è già
  usato da un'altra nota, l'importazione riceve un nuovo ID e i collegamenti vengono aggiornati.
- **Da Markdown:**
  - il titolo proviene dal `title` del front matter, dal primo `# titolo` o dal nome del file;
  - i tag provengono dai `tags` del front matter e dagli `#hashtag` nel testo;
  - il collegamento alla fonte proviene da `url` o `source` e la data di creazione da `created`;
  - `[[collegamenti wiki]]` (compresi i collegamenti per nome di file di Obsidian) e `type:: [[collegamenti]]` diventano collegamenti;
  - le immagini referenziate con `![](path)` o con `![[image.png]]` di Obsidian vengono copiate nel vault;
  - le cartelle nascoste come `.obsidian` e `.trash` vengono saltate;
  - l'esportazione Markdown di ZettelApp si reimporta con i suoi collegamenti tipizzati, flashcard e mappe mentali.

### Sicurezza

I file importati sono trattati come non attendibili:

- i percorsi degli archivi vengono controllati, così i file non possono essere scritti fuori dall'importazione (nessun «zip-slip»);
- gli archivi con troppi file, troppi dati o rapporti di compressione sospetti (le «bombe» di decompressione)
  vengono rifiutati;
- ogni campo è controllato per tipo e limitato in dimensione;
- le immagini vengono riverificate in base al contenuto;
- le immagini remote e i collegamenti ad altre posizioni del disco non vengono importati.

Un backup giornaliero viene creato quando si apre un vault e puoi crearne uno in qualsiasi momento con *File ▸ Esegui backup del vault
ora*. Vedi [Privacy e sicurezza](privacy-and-security.md).
