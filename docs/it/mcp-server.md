# Server MCP

Il [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) è uno standard aperto che permette agli
assistenti IA di usare strumenti e dati di altri programmi. ZettelApp include un server MCP, così assistenti come
**Claude Desktop** e **Claude Code** possono cercare nel tuo Zettelkasten, leggere note, seguire collegamenti tipizzati
e chiedere suggerimenti di collegamento mentre ti aiutano.

## Come viene eseguito

Il server è un piccolo programma separato, **`zettelapp-mcp.exe`**, installato accanto a `ZettelApp.exe`.
Dai sorgenti, lo stesso server si esegue con `python -m zettelapp.mcp_main`. Il tuo client MCP lo avvia quando
serve e comunica con esso tramite standard input/output. **Non viene aperta alcuna porta di rete.**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

Senza `--vault`, serve il vault che hai aperto per ultimo in ZettelApp. Le modifiche fatte tramite MCP compaiono
nell'app entro pochi secondi.

## L'interruttore MCP

I client MCP possono raggiungere le tue note solo mentre **ZettelApp è aperto e l'interruttore MCP nella sua barra di stato è
attivo**. L'interruttore è **disattivato a ogni avvio di ZettelApp**, così decidi, a ogni sessione, se gli assistenti
possono leggere le tue note. Disattivalo, o chiudi ZettelApp, e il server si ferma entro circa un secondo.
Senza l'interruttore il server si rifiuta di avviarsi e ne spiega il motivo. Per il comportamento esatto, vedi il
[Riferimento API MCP](mcp-reference.md).

## Collega Claude Desktop

Apri *Strumenti ▸ Opzioni ▸ Server MCP* e clicca **Aggiungi a Claude Desktop…**. ZettelApp si aggiunge a
`%APPDATA%\Claude\claude_desktop_config.json` (conservando un backup del vecchio file). Poi riavvia Claude
Desktop. Attiva l'**interruttore MCP** nella barra di stato di ZettelApp prima di avviare Claude Desktop; se lo attivi
più tardi, ricollega ZettelApp in Claude Desktop oppure riavvialo. Per farlo a mano, copia lo snippet mostrato
in quella pagina nel file. Ha questo aspetto:

```json
{
  "mcpServers": {
    "zettelapp": {
      "command": "C:\\Users\\me\\AppData\\Local\\Programs\\ZettelApp\\zettelapp-mcp.exe",
      "args": ["--vault", "C:\\Users\\me\\Documents\\ZettelApp"]
    }
  }
}
```

## Collega Claude Code

La stessa pagina Opzioni mostra il comando da copiare:

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

Gli altri client MCP richiedono lo stesso comando e gli stessi argomenti. Come con Claude Desktop, attiva prima MCP in ZettelApp
e ricollega il server (in Claude Code, `/mcp`) se lo attivi in seguito.

## Strumenti

| Strumento | Cosa fa |
|---|---|
| `search_notes` | Ricerca full-text su titoli, testi e tag (funzionano i filtri `tag:nome`). Una query vuota elenca le note modificate di recente. |
| `get_note` | Il testo completo di una nota, tag, collegamento alla fonte, date, collegamenti tipizzati in entrambe le direzioni, flashcard e struttura della mappa mentale. |
| `list_tags` | Tutti i tag, con il numero di note che usano ciascuno. |
| `get_subgraph` | Le note entro 1–4 collegamenti da una nota e i collegamenti tipizzati tra di esse (facoltativamente solo alcuni tipi di collegamento). |
| `suggest_links` | Note probabilmente correlate a una nota ma non ancora collegate, ordinate dal [suggeritore Naive Bayes](link-suggestions.md). |
| `list_link_types` | I tipi di collegamento nel vault, come *supports*, *contradicts* e *part of*. |
| `create_note` | *(scrittura)* Crea una nota. `[[Titolo]]` nel corpo collega alle note esistenti. |
| `add_link` | *(scrittura)* Aggiunge un collegamento tipizzato da una nota a un'altra. |

## Sola lettura per impostazione predefinita

Il server apre il tuo vault in **sola lettura**. I due strumenti di scrittura sono offerti solo quando **entrambe** queste condizioni
sono vere:

1. **Consenti ai client MCP di creare note e collegamenti** è selezionato in *Opzioni ▸ Server MCP*;
2. il server è stato avviato con `--allow-writes`. Lo snippet nella pagina Opzioni include questo flag non appena
   selezioni l'opzione.

L'impostazione viene ricontrollata a ogni scrittura, quindi deselezionarla ha effetto immediato. Attivarla
richiede che il client MCP riavvii il server.

I contenuti delle note vengono passati all'assistente come dati e il server dice all'assistente di non trattarli
come istruzioni. Gli input sono validati (ID, dimensioni e limiti) e il server non tocca mai i file
al di fuori del vault.

## Risoluzione dei problemi

- **Il client dice che il server non è riuscito ad avviarsi, oppure le chiamate agli strumenti dicono che l'interruttore è disattivato.** Apri ZettelApp
  e attiva MCP nella sua barra di stato, poi ricollega il server nel tuo client.
- **Il server continua a non avviarsi.** Controlla che il percorso di `zettelapp-mcp.exe` sia corretto.
  Esegui tu stesso il comando in un terminale: segnala cosa non va (per esempio «No ZettelApp vault
  found») sullo standard error.
- **Mancano gli strumenti di scrittura.** Seleziona l'opzione *e* aggiungi `--allow-writes`, poi riavvia il client.
