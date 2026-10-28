# Confidentialité et sécurité

## Ce qui quitte votre ordinateur

**Rien, sauf si vous le demandez, hormis une petite vérification des mises à jour.** ZettelApp ne possède ni compte, ni télémétrie, ni publicité et ne charge rien depuis Internet pendant que vous travaillez. Voici toutes les requêtes réseau possibles :

| Quand… | ZettelApp contacte… | Données envoyées |
|---|---|---|
| Environ 4 secondes après le démarrage (désactivable) | `https://dutrairs.github.io/ZettelApp/version.json` | Une requête HTTPS pour ce fichier, avec l’en-tête `User-Agent: ZettelApp/<version>`. Rien d’autre : ni notes, ni paramètres, ni identifiants. Les échecs sont silencieux. Consultez [Mises à jour](getting-started.md#updates). |
| Vous posez une question dans la page **Ask** | Le fournisseur d’IA configuré (Anthropic, OpenAI, Z.ai ou votre propre adresse) | Votre question et les notes sous *Sources envoyées* |
| Vous testez la connexion à l’IA ou actualisez la liste des modèles | Le même fournisseur | Votre clé API, pour l’authentification |
| Vous cliquez sur **Synchroniser avec Anki** | AnkiConnect sur **cet ordinateur** (`127.0.0.1`) | Les cartes mémoire du périmètre choisi |
| Vous utilisez *Insertion ▸ Zotero Reference* ou *Tester la connexion* dans les options Zotero | Zotero sur **cet ordinateur** (`127.0.0.1`) | Les termes recherchés (lecture seule) |
| Vous cliquez sur un lien Web, utilisez *Aide ▸ Website / Documentation / Rechercher des mises à jour* ou cliquez sur **Télécharger** dans la notification | Votre navigateur ouvre la page | Aucune donnée provenant de ZettelApp |

Pour arrêter la vérification des mises à jour, décochez *Outils ▸ Options ▸ Général ▸ Vérifier les mises à jour au démarrage de ZettelApp*. ZettelApp n’enverra alors aucune requête, sauf lorsque vous posez une question ou utilisez l’une des autres fonctions ci-dessus.

Les connexions locales à Anki et Zotero n’utilisent jamais de proxy et ne peuvent donc pas être redirigées hors de votre ordinateur. Le serveur MCP n’envoie aucune requête réseau.

## Emplacement des données

| Données | Emplacement |
|---|---|
| Notes, liens, cartes mémoire, historique des révisions | Dossier du coffre : `zettel.db` (SQLite). Par défaut : **Documents\ZettelApp**. |
| Images | Dossier `assets` du coffre. |
| Préférences | Registre, sous `HKEY_CURRENT_USER\Software\ZettelApp\ZettelApp`. |
| Clés API | **Gestionnaire d’identifiants Windows** (`ZettelApp/llm/…`), jamais dans des fichiers ou le registre. |
| Journaux | `%LOCALAPPDATA%\ZettelApp\Logs` (rotation, quelques Mo au maximum). Ils consignent les erreurs, pas vos notes, et ne contiennent jamais de clés API. |
| Sauvegardes automatiques | `%LOCALAPPDATA%\ZettelApp\Backups` |
| Petit cache de l’interface | `%LOCALAPPDATA%\ZettelApp\Cache` |

Le coffre est un dossier ordinaire : vous pouvez le copier, le sauvegarder ou le placer dans OneDrive. ZettelApp écrit dans la base de données avec une synchronisation complète, adaptée aux dossiers synchronisés. Évitez d’ouvrir le même coffre simultanément sur deux ordinateurs.

## Sauvegardes et annulation

- **Sauvegardes quotidiennes :** la première ouverture d’un coffre chaque jour en enregistre une copie cohérente de la base de données. Les 10 plus récentes sont conservées (*Options ▸ Backups*). *Fichier ▸ Sauvegarder le coffre maintenant* en crée une à tout moment. Les images sont stockées par contenu et ne sont jamais supprimées automatiquement.
- **Corbeille :** les notes supprimées y sont d’abord déplacées et peuvent être restaurées tant que la Corbeille n’est pas vidée.
- **Enregistrement automatique :** les notes sont enregistrées pendant la saisie. Une boîte de dialogue signale les erreurs inattendues et en consigne les détails dans le journal.

## Protections de ZettelApp

Les notes peuvent provenir d’importations, du Web ou de réponses d’IA. ZettelApp traite donc leur contenu comme non fiable :

- **Aucun contenu actif.** Le HTML brut d’une note est affiché comme texte, jamais rendu ; aucune note ne peut exécuter de script. L’aperçu ne charge des images **que depuis le dossier `assets` du coffre**, jamais depuis le Web ou un autre emplacement du disque.
- **Liste d’autorisations de liens.** Un clic ouvre uniquement les pages Web (`http`/`https`), e-mails (`mailto`), notes, liens Zotero *select item* / *open PDF* et fichiers locaux ci-dessous. `javascript:` et les autres schémas sont refusés.
- **Les liens locaux révèlent le fichier, sans l’ouvrir.** Un lien `file:///` ouvre **l’Explorateur de fichiers avec le fichier sélectionné** ; le fichier lui-même n’est ni ouvert ni exécuté. Seuls les chemins sur un disque local sont permis. Les chemins réseau (UNC) comme `\\server\share` sont refusés : leur consultation peut transmettre vos identifiants Windows au serveur.
- **Les images sont vérifiées par leur contenu**, et non par leur nom. Seuls les formats PNG, JPEG, GIF, WebP et BMP de 25 Mo maximum sont acceptés ; le format SVG est refusé car il peut contenir des scripts. La vérification contrôle la signature du fichier et sa taille compressée ; les dimensions en pixels sont contrôlées au premier affichage.
- **Importations sûres.** Les archives sont vérifiées contre les détournements de chemins (« zip-slip ») et les bombes de décompression. Chaque champ est validé et sa taille limitée ; les imports Markdown ne peuvent pas accéder aux fichiers hors du dossier importé. Une importation échouée ne modifie pas le coffre : chaque import s’effectue dans une transaction de base de données annulée en cas d’erreur.
- **Exportations sûres.** Les sites Web exportés ne contiennent aucun script et ont une politique CSP stricte. Les fichiers sont écrits de manière atomique.
- **Sécurité de la base de données.** Toutes les requêtes utilisent des paramètres liés et le texte de recherche n’est jamais interprété comme une syntaxe de requête.
- Les liens **`zettelapp://`** (utilisés par les cartes Anki) peuvent uniquement *ouvrir une note par son identifiant*. Toute autre demande est ignorée.
- **Instance unique par utilisateur.** Un second lancement transmet sa demande à l’application active par un canal nommé Windows accessible uniquement à votre compte.
- **Sécurité de l’IA.** Le modèle d’IA ne dispose d’aucun outil ; une instruction cachée dans une note ne peut donc pas le faire agir. Sa réponse utilise le même rendu sécurisé. Les clés API restent dans le Gestionnaire d’identifiants et sont retirées des messages d’erreur.
- **Serveur MCP et commutateur.** Les clients MCP n’accèdent à vos notes que si ZettelApp est ouvert **et** que le commutateur MCP de sa barre d’état est activé. Il est désactivé à chaque démarrage et n’est jamais mémorisé. Le serveur est en lecture seule par défaut, ne s’exécute que lorsque le client MCP le lance, et communique par entrée/sortie standard sans ouvrir de port réseau. Consultez [Serveur MCP](mcp-server.md).

## Désinstallation

Désinstallez via *Paramètres Windows ▸ Applications ▸ Applications installées ▸ ZettelApp ▸ Désinstaller*. Le programme propose l’option décochée **Supprimer aussi mes paramètres et données ZettelApp**. Si vous la cochez, elle supprime vos paramètres, les clés API enregistrées dans le Gestionnaire d’identifiants, les journaux, le cache et les sauvegardes automatiques (`%LOCALAPPDATA%\ZettelApp`), **ainsi que toutes vos notes** (bases de données et pièces jointes de vos coffres). Si elle reste décochée, vos notes restent à leur emplacement.

Vous avez trouvé un problème de sécurité ? Signalez-le de façon confidentielle ; consultez [SECURITY.md](https://github.com/DutraIRS/ZettelApp/blob/main/SECURITY.md).
