# Per iniziare

## Installazione

ZettelApp funziona su **Windows 10 (21H2 o successivo) e Windows 11, a 64 bit**. Scaricalo dall'
[ultima versione](https://github.com/DutraIRS/ZettelApp/releases/latest):

| Download | Usalo quando |
|---|---|
| `ZettelApp-Setup.exe` | Vuoi una normale installazione con una voce nel menu Start, un programma di disinstallazione in *Impostazioni ▸ App* e collegamenti `zettelapp://` che aprono le note da Anki. Non servono privilegi di amministratore: viene installato solo per il tuo account. |
| `ZettelApp-Portable.zip` | Non puoi installare software, oppure vuoi eseguirlo da una chiavetta USB. Decomprimilo ovunque ed esegui `ZettelApp.exe`. |

Il programma di installazione chiede quale lingua usare e propone la lingua di visualizzazione di Windows. Il programma di installazione
e l'app sono tradotti in 11 lingue; cambia la lingua dell'app in *Opzioni*.

Ogni versione elenca i checksum SHA-256 (`SHA256SUMS.txt`). Per verificare un download in PowerShell:

```powershell
Get-FileHash .\ZettelApp-Setup.exe -Algorithm SHA256
```

### «Windows ha protetto il PC»

Le build non sono ancora firmate digitalmente, quindi Microsoft Defender SmartScreen potrebbe mostrare un avviso la prima volta che esegui
il programma di installazione. Se lo hai scaricato dalla pagina ufficiale delle versioni e il checksum corrisponde, scegli
**Ulteriori informazioni ▸ Esegui comunque**. La firma del codice è nella [roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

## Il tuo primo vault

Un **vault** è una cartella che contiene le tue note: un file di database (`zettel.db`) e una cartella `assets` per le immagini.
Al primo avvio ZettelApp ne crea uno in **Documenti\ZettelApp** con undici note iniziali collegate. La nota
*Benvenuto in ZettelApp* guida attraverso collegamenti, tag, immagini, mappe mentali, flashcard e il resto dell'app. Un'
avventura facoltativa di dieci minuti offre lo stesso tour attraverso azioni reali. I nuovi vault creati con
*File ▸ Nuovo vault…* o *File ▸ Apri vault…* ricevono lo stesso materiale iniziale, così puoi lavorare altrove,
per esempio in una cartella di OneDrive.
*File ▸ Apri recenti* elenca i vault usati per ultimi.

Le note si salvano automaticamente mentre scrivi. Non c'è nessun pulsante Salva.

## Un giro della finestra

![La pagina Note](../website/assets/screenshots/notes-light.png)

La **barra di navigazione** a sinistra passa da una pagina all'altra (Ctrl+1 – Ctrl+5):

- **Note**: l'elenco delle note, l'editor e un pannello laterale.
  - L'*elenco* ha la ricerca (funzionano anche i filtri `tag:nome`), un filtro per tag, l'ordinamento e il Cestino.
  - L'*editor* ha il titolo, i tag, un collegamento alla fonte facoltativo e le schede per la **Nota** (Markdown, con le
    modalità Modifica, Divisa e Anteprima), la sua **Mappa mentale** e le sue **Flashcard**.
  - Il *pannello laterale* mostra i **Collegamenti suggeriti**, i **Collegamenti** della nota e i suoi **Collegamenti entranti**.
- **Grafo**: le tue note come una rete in 2D o 3D, colorate per tag o per cluster tematico.
- **Statistiche**: statistiche e grafici sul tuo vault.
- **Ripasso**: ripassi a ripetizione dilazionata, quiz e Anki.
- **Chiedi**: fai domande sulle tue note usando un provider di IA a tua scelta (facoltativo).

**Opzioni** (in fondo alla barra, oppure *Strumenti ▸ Opzioni…*, Ctrl+,) contiene le preferenze: tema, dimensione
del testo dell'editor, suggerimenti di collegamento, tipi di collegamento, IA, server MCP, Anki, Zotero, integrazione con Windows e backup.

L'app segue l'impostazione **chiaro/scuro** e il **colore di accento** di Windows. Puoi forzare un tema in
*Visualizza ▸ Tema*.

## Aggiornamenti

Circa quattro secondi dopo l'avvio, ZettelApp effettua una sola richiesta HTTPS a
`https://dutrairs.github.io/ZettelApp/version.json` per conoscere la versione più recente. Non invia nient'altro
(solo uno user-agent `ZettelApp/<version>`) e, se la richiesta fallisce, non vedrai nulla. Quando esiste una versione più recente,
compare un piccolo avviso nell'angolo in basso a destra, al massimo una volta per versione. Non prende mai il
focus. **Scarica** apre la pagina delle versioni nel browser, **✕** chiude l'avviso e
**Non cercare aggiornamenti** disattiva il controllo. Puoi riattivarlo in
*Strumenti ▸ Opzioni ▸ Generale ▸ Cerca aggiornamenti all'avvio di ZettelApp*. ZettelApp non installa mai
nulla da solo.

## Disinstallazione

Usa *Impostazioni di Windows ▸ App ▸ App installate ▸ ZettelApp ▸ Disinstalla*. Dopo la conferma, una finestra di dialogo offre
un'opzione, non selezionata, **Elimina anche le impostazioni e i dati di ZettelApp**. Rimuove le tue impostazioni, le chiavi
API salvate, i log, la cache e i backup automatici (`%LOCALAPPDATA%\ZettelApp`) **e tutte le tue note** (il database
e gli allegati dei tuoi vault). Lasciala deselezionata per conservare le note. Per la versione portatile, elimina la sua cartella.

## Prossimi passi

- Impara la sintassi delle note in [Note e collegamenti](notes-and-links.md).
- Leggi come funzionano i [suggerimenti di collegamento](link-suggestions.md).
- Premi **F1** in qualsiasi momento per aprire questa documentazione, oppure consulta le [scorciatoie da tastiera](keyboard-shortcuts.md).
