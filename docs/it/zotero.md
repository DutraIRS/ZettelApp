# Zotero

ZettelApp si connette a [Zotero](https://www.zotero.org/), il gestore di riferimenti gratuito, così puoi citare
riferimenti nelle tue note e scrivere **note bibliografiche** collegate all'elemento, e al suo PDF, nella tua libreria.

## Configurazione

1. Usa **Zotero 7 o successivo** e tienilo in esecuzione.
2. In Zotero, apri *Impostazioni ▸ Avanzate* e attiva **«Consenti ad altre applicazioni su questo computer di
   comunicare con Zotero»**.
3. In ZettelApp, *Strumenti ▸ Opzioni ▸ Zotero ▸ Prova connessione* dovrebbe dire *Connesso a Zotero*.

ZettelApp legge la tua libreria tramite l'**API locale** di Zotero su questo computer (`127.0.0.1`, porta 23119 per
impostazione predefinita). Legge soltanto: non modifica mai la tua libreria Zotero e nulla passa da Internet.
Viene cercata la tua libreria personale (*La mia libreria*); le librerie di gruppo, per ora, no.

## Citare un riferimento

*Inserisci ▸ Riferimento Zotero…*, o il pulsante con i libri nella barra degli strumenti dell'editor, apre una casella di ricerca. Scrivi parte di
un titolo, di un autore o un anno. Con una ricerca vuota vengono elencati gli elementi modificati più di recente. Seleziona
un elemento per vederne i dettagli, poi:

- **Inserisci citazione** (o doppio clic) aggiunge una citazione autore–anno che apre l'elemento in Zotero:

  ```markdown
  [Ebbinghaus (1885)](zotero://select/library/items/ABCD2345)
  ```

- **Nuova nota bibliografica** crea una nota per l'elemento, con:
  - il titolo dell'elemento;
  - una riga di riferimento (autori, anno, titolo, pubblicazione, DOI);
  - i collegamenti *Apri in Zotero*, *Apri PDF* (quando l'elemento ha un allegato PDF) e al DOI;
  - l'abstract;
  - le sezioni *Idee chiave* e *I miei pensieri* da compilare;
  - il tag `literature` più i tag Zotero dell'elemento;
  - l'elemento Zotero come **collegamento alla fonte** della nota.

Le note bibliografiche sono il classico ponte dello Zettelkasten tra la lettura e le tue note permanenti: scrivi
le idee chiave con parole tue, poi collegale alle note che supportano, estendono o contraddicono.

## Collegamenti Zotero

Cliccando un collegamento Zotero in una nota si apre Zotero sull'elemento, oppure si apre il PDF nel lettore di Zotero. Per sicurezza,
ZettelApp segue solo due tipi di collegamento Zotero e rifiuta qualsiasi altro indirizzo `zotero://`:

```text
zotero://select/library/items/<KEY>
zotero://open-pdf/library/items/<KEY>?page=<N>
```

Sono accettati anche i collegamenti alle librerie di gruppo (`zotero://select/groups/<ID>/items/<KEY>`). Puoi anche incollare un
collegamento Zotero nel campo **collegamento alla fonte** di una nota. In Zotero, fai clic destro su un elemento e copia il suo collegamento (oppure usa
un componente aggiuntivo come Zutilo), poi incollalo.

## Risoluzione dei problemi

| Messaggio | Cosa fare |
|---|---|
| *Impossibile raggiungere Zotero* | Avvia Zotero 7 o successivo. Controlla la porta in *Opzioni ▸ Zotero* (predefinita 23119). |
| *Zotero ha rifiutato la richiesta* | Attiva l'impostazione *Consenti ad altre applicazioni…* (passaggio 2 sopra). |
| *Questa versione di Zotero non ha un'API locale* | Aggiorna Zotero alla versione 7 o successiva. |
