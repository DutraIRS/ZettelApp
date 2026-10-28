# Exporter et importer

## Exporter

*Fichier ▸ Exporter…* (Ctrl+Shift+E) exporte **toute la collection ou une partie de celle-ci** :

| Périmètre | Contenu exporté |
|---|---|
| **Collection entière** | Toutes les notes (sauf celles de la Corbeille). |
| **Note actuelle et notes liées** | La note ouverte et les notes situées à **Depth** liens ou moins, en suivant les liens dans les deux sens : un *sous-graphe*. |
| **Notes avec un tag** | Les notes portant le tag, y compris les tags imbriqués (`math` inclut `math/algebra`). |

La boîte de dialogue indique le nombre de notes, de liens et de cartes mémoire dans le périmètre. Vous pouvez aussi exporter depuis la liste des notes (clic droit ▸ *Exporter with linked notes…*), le menu ⋯ d’une note, le graphe (le bouton d’exportation inclut les notes affichées) ou le menu d’un nœud du graphe.

### Formats

| Format | Fichier | Contenu |
|---|---|---|
| **Archive ZettelApp** | `.zip` | Tout, y compris les images : notes, liens typés, types de liens (avec leurs couleurs, styles de ligne et pointes de flèche), cartes mémoire et cartes mentales. Réimportez-la dans ZettelApp sur n’importe quel ordinateur. Idéale pour les sauvegardes et le transfert de coffres. |
| **Fichiers Markdown** | `.zip` | Un fichier `.md` par note, avec front matter YAML (id, titre, tags, lien source, dates, liens typés, carte mentale) et des `[[liens wiki]]` entre fichiers. Les liens absents du texte sont répertoriés sous *Liens* sous la forme `type:: [[Note]]`, et les cartes mémoire manuelles sous *Cartes mémoire* au format `Q:`/`A:`. Les images se trouvent dans `assets/`. Ouvrable dans Obsidian et d’autres éditeurs Markdown. |
| **Site Web** | `.zip` | Un site statique autonome : un index avec un aperçu du graphe, un index des tags et une page par note. Les liens y sont dessinés avec les couleurs et styles de ligne de leur type ; le site comprend aussi les cartes mentales et cartes mémoire (réponses révélées au clic). Aucun script : il fonctionne hors ligne en ouvrant `index.html`. Thèmes clair et sombre. |
| **JSON** | `.json` | Données structurées destinées aux scripts et autres outils (les images sont référencées, mais pas incluses). |
| **GraphML** | `.graphml` | Le graphe des liens pour Gephi, yEd, Cytoscape ou NetworkX, avec titres, tags et dates sur les nœuds, types de liens sur les arêtes (orientées ou non), et couleur, style de ligne et pointe de flèche pour chaque type. |
| **Graphviz DOT** | `.dot` | Le graphe sous forme de diagramme Graphviz, avec des types de liens colorés, nommés et stylisés : lignes pleines, tiretées ou pointillées (Graphviz représente les lignes tiret-point et tirets longs par des tirets), ainsi que la pointe de flèche de chaque type ; les types non orientés n’ont pas de flèche. |
| **Paquet Anki** | `.apkg` | Les cartes mémoire des notes exportées. Consultez [Anki](review-and-anki.md#anki). |

Les exportations sont écrites dans un fichier temporaire, puis déplacées à leur emplacement définitif uniquement une fois terminées : une interruption ne laisse donc jamais de fichier incomplet. Elles s’exécutent en arrière-plan ; **Show in folder** ouvre le résultat dans l’Explorateur de fichiers.

Les cartes mentales disposent également de leur propre exportation (PNG, SVG ou FreeMind `.mm`) dans l’onglet **Carte mentale**. Le graphe peut être enregistré en image PNG.

## Importer

*Fichier ▸ Importer…* accepte :

- les **archives ZettelApp** (`.zip`) et les exportations **JSON** ;
- les **fichiers Markdown** (`.md`) ou une **archive `.zip` de fichiers Markdown** ;
- *Fichier ▸ Importer un dossier Markdown…* pour importer un dossier de fichiers Markdown, par exemple un **coffre Obsidian**.

Éléments conservés :

- **Archives ZettelApp et JSON :** les notes conservent leurs identifiants, liens typés, cartes mémoire, cartes mentales et images. Les types de liens absents du coffre sont ajoutés avec leurs couleurs et styles ; ceux qui existent déjà conservent leurs propres réglages. La réimportation d’une archive identique ignore les notes inchangées. Si un identifiant est déjà attribué à une autre note, l’importation en crée un nouveau et met à jour les liens.
- **Markdown :**
  - le titre provient du front matter `title`, du premier `# heading` ou du nom du fichier ;
  - les tags proviennent du front matter `tags` et des `#hashtags` dans le texte ;
  - le lien source provient de `url` ou `source`, et la date de création de `created` ;
  - les `[[liens wiki]]` (y compris les liens de nom de fichier d’Obsidian) et les `type:: [[liens]]` deviennent des liens ;
  - les images référencées par `![](path)` ou `![[image.png]]` dans Obsidian sont copiées dans le coffre ;
  - les dossiers masqués tels que `.obsidian` et `.trash` sont ignorés ;
  - l’export Markdown de ZettelApp peut être réimporté avec ses liens typés, cartes mémoire et cartes mentales.

### Sécurité

Les fichiers importés sont considérés comme non fiables :

- les chemins des archives sont vérifiés afin qu’aucun fichier ne puisse être écrit hors du dossier d’importation (« zip-slip ») ;
- les archives contenant trop de fichiers ou de données, ou présentant des taux de compression suspects (des « bombes » de décompression), sont refusées ;
- le type et la taille de chaque champ sont contrôlés ;
- le contenu des images est vérifié à nouveau ;
- les images distantes et les liens vers d’autres emplacements du disque ne sont pas importés.

Une sauvegarde quotidienne est créée à l’ouverture d’un coffre. Vous pouvez aussi en créer une à tout moment avec *Fichier ▸ Sauvegarder le coffre maintenant*. Consultez [Confidentialité et sécurité](privacy-and-security.md).
