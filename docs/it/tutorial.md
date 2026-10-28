# Tutorial: i tuoi primi 30 minuti

Un tour pratico. Ogni passaggio dice cosa fare e cosa dovresti vedere. I passaggi contrassegnati come *facoltativi* richiedono Zotero,
una chiave IA o Anki; saltali se non usi questi strumenti.

Non conosci il metodo in sé? Leggi prima [Che cos'è uno Zettelkasten?](what-is-zettelkasten.md). Bastano cinque
minuti.

## 1. Installa e apri il vault di benvenuto

1. Scarica **ZettelApp-Setup.exe** dall'[ultima versione](https://github.com/DutraIRS/ZettelApp/releases/latest)
   ed eseguilo, oppure decomprimi **ZettelApp-Portable.zip** ed esegui `ZettelApp.exe`.
2. Avvia ZettelApp.

**Dovresti vedere** la pagina Note con undici note iniziali collegate in un nuovo vault in
*Documenti\ZettelApp*. «Benvenuto in ZettelApp» è aperta nell'editor. Dopo un momento, ZettelApp propone anche l'
avventura facoltativa *Il Principe perduto dell'Archivio*; scegli **Non ora** se preferisci questo tour scritto.

## 2. Crea una nota

1. Premi **Ctrl+N**.
2. Scrivi un titolo, per esempio *Ripetizione dilazionata*, e premi **Enter** per passare al testo.
3. Scrivi un'idea con parole tue, in due o tre frasi:
   *Ripassare il materiale a intervalli crescenti aiuta la memoria a lungo termine, perché ogni ripasso avviene appena
   prima di dimenticare.*

**Dovresti vedere** la nota comparire in cima all'elenco. Non c'è nessun pulsante Salva: le note si salvano mentre
scrivi. L'ID sotto il titolo (per esempio `20261027153012`) è l'indirizzo permanente della nota.

## 3. Aggiungi dei tag

Clicca **Aggiungi tag** sotto il titolo, scrivi `learning` e premi **Enter**. Aggiungi anche `memory`.

**Dovresti vedere** due chip, *#learning* e *#memory*. Il filtro tag sopra l'elenco ora li propone,
e scrivendo `tag:memory` nella casella di ricerca trovi la nota.

## 4. Collega un'altra nota

1. Crea una seconda nota (**Ctrl+N**) intitolata *Curva dell'oblio*, con una frase: *La memoria svanisce
   rapidamente se le informazioni non vengono ripassate.*
2. Torna a *Ripetizione dilazionata* (cliccala nell'elenco). Nel testo, scrivi `[[` e poi `Curv`.
3. Scegli **Curva dell'oblio** dall'elenco di completamento e premi **Enter**.

**Dovresti vedere** `[[Curva dell'oblio]]` sottolineato nel testo. Nel pannello laterale, *Curva dell'oblio*
compare sotto **Collegamenti**. Clicca il pulsante a forma di occhio (**Vista divisa**) nella barra degli strumenti: l'anteprima mostra un
collegamento cliccabile.

## 5. Di' *come* le note sono in relazione

Trasforma il collegamento in un collegamento tipizzato anteponendo `supports::`:

```markdown
supports:: [[Curva dell'oblio]]
```

**Dovresti vedere** il collegamento elencato come *Supporta* nel pannello laterale. Apri *Curva dell'oblio*: i suoi
**Collegamenti entranti** riportano *Ripetizione dilazionata: **Supportata da***, perché *supports* è un tipo di collegamento orientato.
I semplici `[[collegamenti]]` significano *Correlata a*.

## 6. Usa un collegamento suggerito

Scrivi qualche altra nota su idee correlate, per esempio *Richiamo attivo* e *Alternanza*, ciascuna con una
o due frasi e il tag `learning`. Poi aprine una e guarda i **Collegamenti suggeriti** nel
pannello laterale.

- Clicca **Collega** per accettare un suggerimento. La piccola freccia accanto sceglie un tipo di collegamento.
- Clicca **✕** per scartarne uno che non è adatto.
- Passa il mouse su un suggerimento per vedere **perché** è stato proposto: le prove a favore o contro di ogni misura.

**Cosa impara il modello:** i suggerimenti accettati diventano collegamenti, che addestrano il classificatore come esempi
positivi. Quelli scartati vengono ricordati come esempi negativi e non vengono mai più suggeriti per quella coppia.
I suggerimenti migliorano quanto più li usi. Vedi [Suggerimenti di collegamento](link-suggestions.md).

![Note con collegamenti suggeriti](../website/assets/screenshots/notes-light.png)

## 7. Aggiungi un'immagine

Copia un'immagine qualsiasi (per esempio con *Win+Shift+S*), clicca nel testo della nota e premi **Ctrl+V**. Puoi
anche trascinare un file immagine oppure usare *Inserisci ▸ Immagine…*.

**Dovresti vedere** `![…](asset:…)` nel testo e l'immagine nell'anteprima. Poiché è la prima
immagine della nota, diventa anche l'**immagine della nota**, mostrata accanto al titolo e dentro il cerchio della nota
nel grafo.

## 8. Abbozza una mappa mentale

1. Apri la scheda **Mappa mentale** e clicca **Aggiungi idea**.
2. Premi **Tab** per aggiungere un'idea figlia, **Enter** per una sorella, **F2** per rinominare e **Del** per eliminare.
   I tasti freccia si spostano tra le idee.
3. Ora clicca **Dai collegamenti** e conferma che può sostituire la mappa che hai appena disegnato.

**Dovresti vedere** una mappa mentale creata dai collegamenti della nota, raggruppati per tipo di collegamento, con i collegamenti
di ciascuna nota collegata un livello più in profondità. Clic destro su qualsiasi idea per collegarla a una nota. Il pulsante di esportazione salva in PNG, SVG
o FreeMind.

![Una mappa mentale](../website/assets/screenshots/mindmap-light.png)

## 9. Crea flashcard e ripassale

Aggiungi queste righe al testo di *Ripetizione dilazionata*:

```markdown
Q: Why space reviews out?
A: Each effortful retrieval just before forgetting strengthens the memory.

{{c1::Hermann Ebbinghaus}} described the forgetting curve.
```

**Dovresti vedere** **Flashcard (2)** sulla scheda: una scheda domanda e una scheda cloze. Ora apri **Ripasso**
(**Ctrl+4**) e clicca **Inizia ripasso**.

- Premi **Space** per mostrare la risposta.
- Valutati con **1–4** (*Ancora, Difficile, Bene, Facile*).

La pianificazione SM-2 decide quando ogni scheda ritorna. Prova anche **Quiz di esercitazione ▸ Scelta multipla** o **Dai un nome a
quella nota**.

![Un quiz a scelta multipla](../website/assets/screenshots/quiz-light.png)

## 10. Esplora il grafo

Apri **Grafo** (**Ctrl+2**).

1. Trascina le note, usa la rotellina per lo zoom e passa il mouse su una nota per evidenziare le sue vicine.
2. Seleziona una nota nella pagina Note, torna indietro e clicca **Locale**, poi cambia **Profondità** in 1, 2 o 3.
3. Imposta **Colora per** su **Cluster: k-means**. Le note vengono raggruppate per significato e la legenda dà un nome a ogni
   cluster con le sue parole chiave.
4. Attiva **Raggruppa** per avvicinare ogni gruppo su uno sfondo ombreggiato.
5. Clicca **3D**, trascina per orbitare e prova **Ruota automaticamente**.

![Il grafo, colorato per tag e raggruppato](../website/assets/screenshots/graph-light.png)

## 11. Controlla le tue Statistiche

Apri **Statistiche** (**Ctrl+3**) per vedere conteggi, note per mese, tag principali, collegamenti per tipo e le note più
connesse. **Note non collegate** è la tua lista di cose da fare: collegale a qualcosa. Ogni grafico ha una vista
a tabella.

## 12. Cita un elemento di Zotero e scrivi una nota bibliografica (facoltativo)

Con Zotero 7+ in esecuzione e l'opzione *Consenti ad altre applicazioni su questo computer di comunicare con Zotero* attivata
in *Impostazioni ▸ Avanzate*:

1. Scegli *Inserisci ▸ Riferimento Zotero…*, cerca un elemento e clicca **Inserisci citazione**: un collegamento come
   *Ebbinghaus (1885)* che apre l'elemento in Zotero.
2. Ripeti l'operazione e clicca **Nuova nota bibliografica**.

**Dovresti vedere** una nuova nota con il riferimento, i collegamenti *Apri in Zotero* e *Apri PDF*, l'abstract e
le sezioni *Idee chiave* / *I miei pensieri*, con il tag `literature`. Vedi [Zotero](zotero.md).

## 13. Chiedi alle tue note (facoltativo)

1. In *Strumenti ▸ Opzioni ▸ Assistente IA*, scegli un provider (Anthropic, OpenAI o Z.ai), incolla la tua chiave API
   e clicca **Prova connessione**.
2. Apri **Chiedi** (**Ctrl+5**) e chiedi: *In che modo distanziamento e richiamo lavorano insieme?*

**Dovresti vedere** una risposta che cita le tue note come collegamenti e l'elenco esatto delle **fonti inviate**. Solo
quelle note e la tua domanda lasciano il tuo computer. Vedi [Chiedi alle tue note](ai-assistant.md).

## 14. Esporta un sottografo e sincronizza con Anki (facoltativo)

1. Apri una nota, scegli *File ▸ Esporta…* (**Ctrl+Shift+E**), seleziona **Nota corrente e note collegate**,
   profondità 2 e il formato **Sito web**.
2. Apri l'`index.html` dello zip nel browser: un piccolo sito web di quella parte del tuo Zettelkasten.
3. Con Anki in esecuzione e il componente aggiuntivo AnkiConnect (codice `2055492159`) installato, apri **Ripasso** e clicca
   **Sincronizza con Anki**. Il collegamento alla fonte di ogni scheda apre la nota in ZettelApp.

Vedi [Esportazione e importazione](export-import.md) e [Anki](review-and-anki.md#anki).

## 15. Sai dove risiedono i tuoi dati

- Le tue note risiedono nella cartella del vault (*File ▸ Mostra vault in Esplora file*): `zettel.db` più `assets`.
- Un backup viene creato automaticamente una volta al giorno e *File ▸ Esegui backup del vault ora* ne crea uno in qualsiasi momento.
- Le note eliminate vanno nel **Cestino** sotto l'elenco delle note, dove puoi ripristinarle.

Dettagli in [Privacy e sicurezza](privacy-and-security.md).

**Ecco fatto.** Continua a scrivere un'idea per nota, collega ogni nuova nota con un motivo e lascia che i suggerimenti e
il grafo ti mostrino ciò che hai. Le scorciatoie sono in [Scorciatoie da tastiera](keyboard-shortcuts.md).
