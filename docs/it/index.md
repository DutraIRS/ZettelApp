# Documentazione di ZettelApp

ZettelApp è uno Zettelkasten per Windows: una rete di piccole note, ciascuna con una sola idea, collegate
da link che dicono *come* le idee sono in relazione. Suggerisce collegamenti mentre scrivi, disegna la tua conoscenza come un
grafo 2D o 3D, trasforma le note in flashcard e quiz e funziona con Anki, Zotero e assistenti IA.

Tutto resta sul tuo computer, a meno che tu non chieda qualcosa che richiede la rete.

## Sei alle prime armi?

- **[Che cos'è uno Zettelkasten?](what-is-zettelkasten.md)**: il metodo, da dove viene e come
  ZettelApp lo supporta.
- **[Tutorial: i tuoi primi 30 minuti](tutorial.md)**: un tour pratico dalla prima nota fino al grafo 3D.

## Indice

- [Per iniziare](getting-started.md): installazione, il primo vault e un giro della finestra
- [Note e collegamenti](notes-and-links.md): Markdown, collegamenti wiki, collegamenti tipizzati e orientati, tag, immagini,
  mappe mentali, flashcard, ricerca e Cestino
- [Suggerimenti di collegamento](link-suggestions.md): come funziona il suggeritore Naive Bayes e come regolarlo
- [Grafo e Statistiche](graph-and-insights.md): grafi 2D e 3D, clustering, raggruppamento e grafici
- [Ripasso, quiz e Anki](review-and-anki.md): ripetizione dilazionata, modalità quiz, sincronizzazione con Anki e mazzi
- [Zotero](zotero.md): cita riferimenti e scrivi note bibliografiche
- [Chiedi alle tue note (IA)](ai-assistant.md): risposte da Claude, OpenAI o Z.ai, basate sulle tue note
- [Server MCP](mcp-server.md): lascia che Claude Desktop, Claude Code e altri client MCP leggano il tuo vault
- [Riferimento API MCP](mcp-reference.md): il protocollo, gli strumenti e gli errori, per chi sviluppa client MCP
- [Esportazione e importazione](export-import.md): l'intera raccolta o qualsiasi sottografo, in sette formati
- [Scorciatoie da tastiera](keyboard-shortcuts.md)
- [Privacy e sicurezza](privacy-and-security.md): cosa lascia il tuo computer, dove risiedono i dati e
  come ZettelApp li protegge
- [Sviluppo](development.md): compilare dai sorgenti, eseguire i test, creare un pacchetto di rilascio
- [FAQ](faq.md)

## Le idee alla base

Uno **Zettelkasten** («schedario») è un metodo di presa di appunti reso celebre dal sociologo Niklas Luhmann.
Ogni nota è *atomica* (una sola idea, con parole tue) e ha un ID permanente. Il valore nasce dalle
connessioni: quando colleghi una nuova nota a quelle esistenti, sei costretto a pensare a come le idee si relazionano,
e in seguito puoi seguire quei collegamenti per trovare combinazioni inaspettate.

ZettelApp mantiene quella disciplina ma elimina l'attrito:

- **Gli ID sono automatici**: ogni nota riceve un ID basato sulla data e ora, come `20261027153012`.
- **I collegamenti possono dire come le note si relazionano**: *supporta*, *contraddice*, *estende*, *esempio di*, *parte di*,
  *cita*, o tipi di collegamento tuoi.
- **I suggerimenti fanno emergere le connessioni che ti sono sfuggite**: un classificatore confronta una nota con il resto del vault
  e impara dai collegamenti che accetti e scarti.
- **Il ripasso è integrato**: le note diventano flashcard e quiz, con ripetizione dilazionata o Anki.
