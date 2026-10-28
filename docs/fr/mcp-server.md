# Serveur MCP

Le [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) est une norme ouverte qui permet aux assistants d’IA d’utiliser les outils et données d’autres programmes. ZettelApp comprend un serveur MCP : des assistants comme **Claude Desktop** et **Claude Code** peuvent ainsi rechercher dans votre Zettelkasten, lire des notes, suivre des liens typés et demander des suggestions de liens pendant qu’ils vous aident.

## Fonctionnement

Le serveur est un petit programme distinct, **`zettelapp-mcp.exe`**, installé à côté de `ZettelApp.exe`. Depuis les sources, le serveur s’exécute avec `python -m zettelapp.mcp_main`. Votre client MCP le démarre au besoin et communique avec lui par l’entrée et la sortie standard. **Aucun port réseau n’est ouvert.**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

Sans `--vault`, il utilise le dernier coffre ouvert dans ZettelApp. Les modifications effectuées via MCP apparaissent dans l’application après quelques secondes.

## Commutateur MCP

Les clients MCP n’accèdent à vos notes que lorsque **ZettelApp est ouvert et que le commutateur MCP de sa barre d’état est activé**. Le commutateur est **désactivé à chaque démarrage de ZettelApp** : vous décidez à chaque session si les assistants peuvent lire vos notes. Désactivez-le ou fermez ZettelApp : le serveur s’arrête en une seconde environ. Sans ce commutateur, le serveur refuse de démarrer et en indique la raison. Consultez la [référence de l’API MCP](mcp-reference.md) pour le fonctionnement détaillé.

## Connecter Claude Desktop

Ouvrez *Outils ▸ Options ▸ MCP server* et cliquez sur **Ajouter à Claude Desktop…**. ZettelApp s’ajoute à `%APPDATA%\Claude\claude_desktop_config.json` (une copie de sauvegarde de l’ancien fichier est conservée). Redémarrez ensuite Claude Desktop. Activez le **commutateur MCP** dans la barre d’état de ZettelApp avant de lancer Claude Desktop ; si vous l’activez plus tard, reconnectez ZettelApp dans Claude Desktop ou redémarrez-le. Pour le faire manuellement, copiez dans le fichier l’extrait affiché sur cette page. Il ressemble à ceci :

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

## Connecter Claude Code

La même page Options indique la commande à copier :

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

Les autres clients MCP ont besoin de la même commande et des mêmes arguments. Comme avec Claude Desktop, activez d’abord MCP dans ZettelApp et reconnectez le serveur ensuite (dans Claude Code, `/mcp`).

## Outils

| Outil | Fonction |
|---|---|
| `search_notes` | Recherche en texte intégral dans les titres, le texte et les tags (les filtres `tag:name` fonctionnent). Une recherche vide répertorie les notes récemment modifiées. |
| `get_note` | Texte intégral, tags, lien source, dates, liens typés dans les deux sens, cartes mémoire et plan de la carte mentale d’une note. |
| `list_tags` | Tous les tags et le nombre de notes associées à chacun. |
| `get_subgraph` | Notes situées à 1–4 liens d’une note et liens typés entre elles (avec la possibilité de limiter les types). |
| `suggest_links` | Notes probablement liées à une note mais qui ne le sont pas encore, classées par le [suggesteur Naive Bayes](link-suggestions.md). |
| `list_link_types` | Types de liens du coffre, par exemple *supports*, *contradicts* et *part of*. |
| `create_note` | *(écriture)* Créer une note. `[[Titre]]` dans le corps renvoie aux notes existantes. |
| `add_link` | *(écriture)* Ajouter un lien typé entre deux notes. |

## Lecture seule par défaut

Le serveur ouvre votre coffre **en lecture seule**. Les deux outils d’écriture ne sont proposés que si les conditions suivantes sont réunies :

1. **Autoriser les clients MCP à créer des notes et des liens** est coché dans *Options ▸ MCP server* ;
2. le serveur a été lancé avec `--allow-writes`. L’extrait de la page Options inclut cet argument lorsque vous cochez l’option.

Le réglage est vérifié à chaque écriture : le décocher prend donc effet immédiatement. L’activer nécessite de redémarrer le serveur depuis le client MCP.

Le contenu des notes est transmis à l’assistant comme des données, et le serveur lui indique de ne pas les traiter comme des instructions. Les entrées sont validées (identifiants, tailles et limites) et le serveur ne touche jamais aux fichiers situés hors du coffre.

## Dépannage

- **Le client indique que le serveur n’a pas démarré, ou que le commutateur est désactivé.** Ouvrez ZettelApp, activez MCP dans la barre d’état, puis reconnectez le serveur dans votre client.
- **Le serveur ne démarre toujours pas.** Vérifiez le chemin de `zettelapp-mcp.exe`. Exécutez vous-même la commande dans un terminal : la cause de l’erreur (par exemple « No ZettelApp vault found ») s’affiche sur la sortie d’erreur standard.
- **Les outils d’écriture sont absents.** Cochez l’option, ajoutez `--allow-writes`, puis redémarrez le client.
