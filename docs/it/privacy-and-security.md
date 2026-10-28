# Privacy e sicurezza

## Cosa lascia il tuo computer

**Niente, a meno che tu non lo richieda, a parte un piccolo controllo degli aggiornamenti.** ZettelApp non ha account,
telemetria né pubblicità e non carica nulla da Internet mentre lavori. Queste sono tutte le richieste di
rete che può effettuare:

| Quando… | ZettelApp contatta | Cosa viene inviato |
|---|---|---|
| Circa 4 secondi dopo l'avvio di ZettelApp (può essere disattivato) | `https://dutrairs.github.io/ZettelApp/version.json` | Una richiesta HTTPS per quel file, con l'intestazione `User-Agent: ZettelApp/<version>`. Nient'altro: niente note, impostazioni o identificatori. Qualsiasi errore è silenzioso. Vedi [Aggiornamenti](getting-started.md#updates). |
| Fai una domanda nella pagina **Chiedi** | Il provider di IA che hai configurato (Anthropic, OpenAI, Z.ai o il tuo endpoint) | La tua domanda e le note elencate sotto *Fonti inviate* |
| Provi la connessione IA o aggiorni l'elenco dei modelli | Lo stesso provider | La tua chiave API, per l'autenticazione |
| Usi **Sincronizza con Anki** | AnkiConnect su **questo computer** (`127.0.0.1`) | Le flashcard dell'ambito scelto |
| Usi **Inserisci ▸ Riferimento Zotero** o *Prova connessione* nelle opzioni di Zotero | Zotero su **questo computer** (`127.0.0.1`) | Le parole della tua ricerca (sola lettura) |
| Clicchi un collegamento web, usi *Aiuto ▸ Sito web / Documentazione / Cerca aggiornamenti* oppure il pulsante **Scarica** dell'avviso di aggiornamento | Il tuo browser web apre la pagina | Niente da ZettelApp |

Per fermare il controllo degli aggiornamenti, deseleziona *Strumenti ▸ Opzioni ▸ Generale ▸ Cerca aggiornamenti all'avvio di ZettelApp*;
da quel momento ZettelApp non effettua richieste finché non fai una domanda o usi una delle altre funzioni sopra indicate.

Le connessioni locali ad Anki e Zotero non usano mai un proxy, quindi non possono essere reindirizzate fuori dal tuo computer.
Il server MCP non effettua alcuna richiesta di rete.

## Dove risiedono i tuoi dati

| Cosa | Dove |
|---|---|
| Note, collegamenti, flashcard, cronologia dei ripassi | La cartella del tuo vault: `zettel.db` (SQLite). Per impostazione predefinita **Documenti\ZettelApp**. |
| Immagini | La cartella `assets` del vault. |
| Preferenze | Il registro di sistema, sotto `HKEY_CURRENT_USER\Software\ZettelApp\ZettelApp`. |
| Chiavi API | **Gestione credenziali di Windows** (`ZettelApp/llm/…`), mai in file o nel registro. |
| Log | `%LOCALAPPDATA%\ZettelApp\Logs` (a rotazione, al massimo pochi MB). Registrano errori, non le tue note, e non includono mai le chiavi API. |
| Backup automatici | `%LOCALAPPDATA%\ZettelApp\Backups` |
| Piccola cache dell'interfaccia | `%LOCALAPPDATA%\ZettelApp\Cache` |

Il vault è una normale cartella: puoi copiarla, farne il backup o tenerla in OneDrive. ZettelApp scrive il
database con sincronizzazione completa, un'impostazione scelta per adattarsi alle cartelle sincronizzate. Evita di aprire lo stesso vault su due
computer contemporaneamente.

## Backup e annullamento

- **Backup giornalieri:** la prima volta che un vault viene aperto ogni giorno, viene salvata una copia coerente del suo database.
  Vengono conservate le 10 più recenti (*Opzioni ▸ Backup*). *File ▸ Esegui backup del vault ora* ne crea una in qualsiasi momento.
  Le immagini sono archiviate per contenuto e non vengono mai eliminate automaticamente.
- **Cestino:** le note eliminate vanno prima nel Cestino e possono essere ripristinate finché non lo svuoti.
- **Salvataggio automatico:** le note si salvano mentre scrivi. Una finestra di dialogo di arresto anomalo segnala gli errori imprevisti e scrive i dettagli nel
  log.

## Come ZettelApp ti protegge

Le note possono provenire da importazioni, dal web o da risposte dell'IA, quindi ZettelApp tratta i loro contenuti come non attendibili:

- **Nessun contenuto attivo.** L'HTML grezzo nelle note viene mostrato come testo, mai interpretato; nulla in una nota può eseguire
  script. L'anteprima della nota carica le immagini **solo dalla cartella `assets` del vault**, mai dal
  web o da altre posizioni del disco.
- **Elenco di collegamenti consentiti.** Cliccare un collegamento apre solo pagine web (`http`/`https`), e-mail (`mailto`), note,
  collegamenti Zotero *seleziona elemento* / *apri PDF* e collegamenti a file locali (sotto). `javascript:` e altri
  schemi vengono rifiutati.
- **I collegamenti a file locali rivelano soltanto il file.** Un collegamento `file:///` apre **Esplora file con il file
  selezionato**; il file in sé non viene mai aperto né eseguito. Sono consentiti solo percorsi su un'unità locale. I percorsi
  di rete (UNC) come `\\server\share` vengono rifiutati, perché cercarne uno può inviare le tue credenziali
  Windows a quel server.
- **Le immagini sono verificate in base al contenuto**, non al nome del file. Sono accettati solo PNG, JPEG, GIF, WebP e BMP fino a 25 MB;
  SVG è rifiutato perché può contenere script. La verifica riguarda la firma del file e la
  dimensione compressa; le dimensioni in pixel vengono controllate quando l'immagine è mostrata per la prima volta.
- **Importazioni sicure.** Gli archivi vengono controllati per trucchi sui percorsi («zip-slip») e bombe di decompressione. Ogni campo
  è validato e limitato in dimensione, le importazioni Markdown non possono uscire dalla cartella importata e un'importazione
  non riuscita lascia invariato il vault: le importazioni vengono eseguite in un'unica transazione del database, annullata in caso di
  qualsiasi errore.
- **Esportazioni sicure.** I siti web esportati non contengono script e includono una Content-Security-Policy rigorosa. I file
  vengono scritti in modo atomico.
- **Sicurezza del database.** Tutte le query al database usano parametri vincolati e il testo di ricerca non viene mai interpretato come
  sintassi di query.
- **I collegamenti `zettelapp://`** (usati dalle schede Anki) possono solo *aprire una nota tramite il suo ID*. Qualsiasi altra richiesta viene
  ignorata.
- **Una sola istanza per utente.** Un secondo avvio passa la sua richiesta all'app in esecuzione tramite una named pipe di Windows
  accessibile solo dal tuo account utente.
- **Sicurezza dell'IA.** Il modello di IA non ha strumenti, quindi le istruzioni nascoste in una nota non possono farlo agire, e la sua
  risposta viene mostrata con lo stesso renderer sicuro. Le chiavi API restano in Gestione credenziali e sono rimosse dai
  messaggi di errore.
- **Il server MCP e il suo interruttore.** I client MCP possono raggiungere le tue note solo mentre ZettelApp è aperto **e**
  l'interruttore MCP nella sua barra di stato è attivo. L'interruttore è disattivato a ogni avvio di ZettelApp e non viene mai salvato.
  Il server è in sola lettura per impostazione predefinita, viene eseguito solo quando il tuo client MCP lo avvia e usa standard
  input/output senza alcuna porta di rete. Vedi [Server MCP](mcp-server.md).

## Disinstallazione

Disinstalla da *Impostazioni di Windows ▸ App ▸ App installate ▸ ZettelApp ▸ Disinstalla*. Il programma di disinstallazione offre
un'opzione non selezionata, **Elimina anche le impostazioni e i dati di ZettelApp**. Se la selezioni, rimuove le tue
impostazioni, le chiavi API salvate in Gestione credenziali, i log, la cache e i backup automatici
(`%LOCALAPPDATA%\ZettelApp`) **e tutte le tue note** (il database e gli allegati dei tuoi vault). Se non la selezioni,
le tue note restano dove sono.

Hai trovato un problema di sicurezza? Segnalalo in privato; vedi
[SECURITY.md](https://github.com/DutraIRS/ZettelApp/blob/main/SECURITY.md).
