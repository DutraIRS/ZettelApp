# Notes et liens

## Rédiger des notes

Les notes sont écrites en **Markdown** : `**gras**`, `*italique*`, `# titres`, listes, `> citations`,
`` `code` ``, blocs de code clôturés, tableaux et `~~texte barré~~`. La barre d’outils au-dessus de l’éditeur
insère les éléments courants, et Ctrl+B / Ctrl+I fonctionnent comme d’habitude. Les listes continuent
lorsque vous appuyez sur Entrée.

L’éditeur propose trois modes (Ctrl+E permet de passer de l’un à l’autre) : **Édition**, **Split** (texte et aperçu
côte à côte) et **Aperçu**.

Par sécurité, le HTML brut d’une note est affiché comme texte et n’est jamais rendu. Dans l’aperçu, les liens
ouvrent uniquement des pages Web (`http`, `https`), des e-mails (`mailto`), des notes, des éléments Zotero
et des fichiers locaux (affichés dans l’Explorateur de fichiers ; consultez [Liens vers des fichiers locaux](#links-to-local-files)). Consultez [Confidentialité et sécurité](privacy-and-security.md).

### Suivre des liens

- **Dans l’éditeur**, **Ctrl+clic** suit un `[[lien vers une note]]` (et crée la note si elle n’existe pas encore),
  un lien Web, e-mail ou Zotero, un lien vers un fichier local, ou un `#tag` (qui répertorie les notes portant ce tag).
  Survolez le texte pour afficher une infobulle décrivant l’action du clic. Un simple clic place le curseur afin que
  vous puissiez modifier le texte du lien.
- **Dans l’aperçu**, un clic normal suit les liens.

### Liens vers des fichiers locaux

*Insertion ▸ Lien vers un fichier…* (ou le bouton de dossier de la barre d’outils) permet de choisir un fichier et insère
un lien tel que `[report.pdf](file:///C:/Users/me/Documents/report.pdf)`. Vous pouvez aussi faire glisser dans
le texte de la note un fichier qui n’est pas une image. Le lien pointe vers l’emplacement d’origine ; rien n’est
copié dans le coffre.

Cliquer sur le lien dans l’aperçu ou faire Ctrl+clic dessus dans l’éditeur ouvre **l’Explorateur de fichiers avec
le fichier sélectionné**. Le fichier lui-même n’est jamais ouvert ni exécuté. Seuls les chemins sur un disque local
sont autorisés : les chemins réseau (UNC) comme `\\server\share\file.pdf` sont refusés, car leur consultation
pourrait transmettre vos identifiants Windows à ce serveur.

Chaque note possède :

- un **titre** (le grand champ en haut) ;
- un **identifiant**, horodaté, par exemple `20261027153012`, affiché sous le titre (*Plus ▸ Copier note ID*) ;
- éventuellement des **tags**, un **lien source**, une **image**, une **carte mentale** et des **cartes mémoire**.

## Liens entre les notes

### Liens wiki

Saisissez `[[` puis commencez à taper un titre : ZettelApp le complète à partir de vos notes. Dans une note, les
formes suivantes créent toutes un lien :

```markdown
See [[Forgetting curve]].
See [[20261027153012]].              (by ID)
See [[Forgetting curve|the curve]].  (custom link text)
```

Ctrl+K (*Insertion ▸ Lien vers une note…*) ouvre un sélecteur qui recherche dans les titres et le texte et permet de choisir
le type de lien. Dans l’aperçu, un lien vers un titre inexistant apparaît en gris ; cliquez dessus pour créer la note.
Lorsque vous créez ou renommez ensuite une note, les liens mentionnant son titre sont mis à jour.

### Liens typés

Les liens peuvent préciser **comment** deux notes sont liées. Placez le type de lien avant celui-ci, suivi de `::` :

```markdown
supports:: [[Forgetting curve]]
contradicts:: [[Rereading notes]]
part_of:: [[Zettelkasten method]]
```

Types de liens intégrés :

| Type | Nom | Nom inverse | Orienté | Ligne | Pointe de flèche |
|---|---|---|---|---|---|
| `related` | Lié à | Lié à | non | continue, grise | aucune |
| `supports` | Soutient | Soutenu par | oui | tiretée, verte | triangle plein |
| `contradicts` | Contredit | Contredit | non | pointillée, rouge | aucune |
| `extends` | Étend | Étendu par | oui | tiret-point, bleue | triangle plein |
| `example` | Exemple de | A pour exemple | oui | tiret-point-point, ambre | cercle |
| `part_of` | Fait partie de | Contient | oui | tirets longs, violette | losange |
| `cites` | Cite | Cité par | oui | continue, turquoise | flèche ouverte |

Voici les styles d’un nouveau coffre ; vous pouvez les modifier (voir ci-dessous). Un coffre créé avec une version
antérieure conserve ses lignes.

Un simple `[[lien]]` signifie *Lié à*.

### Liens orientés et non orientés

Un type **orienté** se lit différemment selon le côté. Si la note A *étaye* la note B, les rétroliens de B
présentent A comme *Soutenu par*. Les liens orientés ont des pointes de flèche dans le graphe et restent orientés
lors des exportations. Les types **non orientés**, comme *Lié à* et *Contredit*, se lisent de la même façon
dans les deux sens.

Pour inverser un lien orienté dans le mauvais sens, faites un clic droit dessus dans le panneau latéral et choisissez
**Reverse direction**. Pour inverser un lien écrit dans le texte, modifiez le texte.

### Liens dans le panneau latéral

Le panneau latéral répertorie les **Liens** sortants et les **Rétroliens** entrants de la note, chacun accompagné
de son type.

- **Ajouter un lien…** crée un lien sans l’écrire dans le texte.
- Faites un clic droit sur un lien pour ouvrir l’autre note, modifier le type, inverser le sens ou le supprimer.
  Les liens écrits dans le texte doivent être supprimés en modifiant celui-ci.
- Dans la liste des notes, faites un clic droit sur une autre note et choisissez **Lier depuis la note ouverte comme**.

### Vos propres types de liens

Ajoutez, renommez, redéfinissez le style ou supprimez des types de liens dans *Outils ▸ Options ▸ Types de lien*. Sélectionnez
un type dans la liste et modifiez ses propriétés à côté :

- **Nom** et **Nom inverse** : libellés du lien depuis sa source et sa cible. Le nom inverse ne s’utilise que pour
  les types orientés.
- **Orienté** : indique si le type se lit différemment dans les deux sens et possède une pointe de flèche.
- **Couleur** : cliquez sur le bouton de couleur pour choisir une couleur.
- **Ligne** : ligne continue, tiretée, pointillée, tiret-point, tiret-point-point ou à tirets longs.
- **Pointe de flèche** : pointe à l’arrivée d’un lien orienté : triangle plein, flèche ouverte, losange, cercle ou barre.

L’aperçu montre deux notes reliées, le nom du lien et sa lecture depuis l’autre côté. Le style est utilisé partout où
les liens apparaissent : dans le graphe, sa légende, le panneau latéral, le sélecteur de liens, ainsi que les
exportations vers le site Web, GraphML et Graphviz. Attribuez à chaque type un style de ligne et une couleur propres
pour les distinguer facilement, y compris par les personnes daltoniennes et sur papier. Lors de la création d’un type,
choisissez une couleur et une ligne peu utilisées par les autres.

Dans le texte, utilisez l’identifiant du type affiché sous l’aperçu (par exemple, un type nommé « Inspiré par » devient
`inspired_by::`). Cet identifiant est défini à la création ; renommer le type ne casse donc pas les liens déjà présents
dans vos notes. La suppression d’un type personnalisé transforme ses liens en liens *Lié à* : rien n’est perdu.
Les types intégrés peuvent être renommés et redéfinis, mais pas supprimés.

## Tags

Ajoutez des tags dans le champ sous le titre (appuyez sur Entrée après chacun) ou écrivez-les **dans le texte** avec
un signe dièse, par exemple `#welcome` ou `#math/algebra`. Les tags sont en minuscules et peuvent être imbriqués
avec une barre oblique, comme `math/algebra`. Un filtre sur `math` trouve également les notes portant `math/algebra`.
Utilisez le filtre de tags au-dessus de la liste des notes ou saisissez `tag:name` dans le champ de recherche.

Les tags écrits dans le texte sont de vrais tags, affichés sous forme de **pastilles au contour** près du champ *Ajouter un tag*.
Ils disparaissent lorsque vous supprimez le `#tag` du texte. Un `#tag` est ignoré dans le code, les cibles de liens et
les `[[#titres]]`. Les tags saisis dans le champ *Ajouter un tag* sont distincts : ils restent jusqu’à ce que vous les supprimiez
avec leur ✕. Dans l’éditeur, faites Ctrl+clic sur un `#tag` pour répertorier les notes qui le portent.

## Lien source

Le champ avec l’icône de globe contient la **source** de la note : une page Web (`https://…`), une adresse e-mail ou un
élément Zotero (`zotero://select/library/items/…`). Le bouton voisin ouvre le lien. Les autres types de lien sont refusés.
Consultez [Zotero](zotero.md) pour créer directement des notes depuis votre bibliothèque Zotero.

## Images

Insérez des images avec *Insertion ▸ Image…* (Ctrl+Shift+I), en les **collant** depuis le presse-papiers ou en faisant
**glisser** des fichiers image dans l’éditeur. Formats pris en charge : PNG, JPEG, GIF, WebP et BMP, jusqu’à 25 Mo.
Le format SVG est volontairement refusé, car les fichiers SVG peuvent contenir des scripts.

Les images sont vérifiées d’après leur contenu (et non leur nom), enregistrées une seule fois dans le dossier `assets`
du coffre sous un nom dérivé de leur contenu, puis référencées ainsi :

```markdown
![Diagram](asset:3f2a9c0b1d4e5f6a7b8c.png)
```

La première image ajoutée à une note devient son **image de titre**. Elle s’affiche sous forme de vignette arrondie dans
la liste et dans le cercle de la note sur le graphe. Faites un clic droit sur une image dans l’éditeur ou l’aperçu, puis
choisissez *Utiliser comme image du titre* pour en sélectionner une autre, ou *Retirer l’image du titre* pour n’en choisir aucune.
Supprimer l’image du titre du texte de la note la retire aussi comme image du titre.

## Listes de contrôle

Commencez une ligne par `- [ ]` (ou cliquez sur le bouton de liste de contrôle de la barre d’outils) pour créer une tâche.
`- [x]` indique une tâche terminée. Dans l’aperçu, cliquez sur la case pour la cocher ; appuyez sur Entrée à la fin d’une
tâche pour en commencer une autre, ou sur Entrée dans une tâche vide pour terminer la liste.

## Alarmes

Cliquez sur le bouton d’alarme (ou utilisez *Insertion ▸ Alarme…*) pour définir une date et, facultativement, une heure pour
une note. À l’échéance, ZettelApp affiche une notification ; cliquez dessus pour ouvrir la note. ZettelApp doit être ouvert
pour vous avertir. Les alarmes arrivées à échéance pendant sa fermeture se déclenchent peu après l’ouverture du coffre.
Les notes avec alarme portent une cloche dans la liste. Utilisez *Supprimer l’alarme* dans la même boîte de dialogue pour
supprimer l’alarme.

## Formules

Écrivez du LaTeX entre signes dollar : `$E = mc^2$` pour une formule en ligne et `$$\int_0^1 x^2\,dx$$` pour une formule
affichée. Le bouton de formule (*Insertion ▸ Insérer une formule*) ouvre une boîte de dialogue avec aperçu instantané. Les formules
s’affichent dans l’aperçu ; les exportations conservent le code source LaTeX.

## Cartes mentales

Chaque note peut contenir une carte mentale (onglet **Carte mentale** ou *Insertion ▸ Carte mentale*). Les branches sont colorées
automatiquement.

| Touche | Action |
|---|---|
| Tab | Ajouter une idée enfant |
| Enter | Ajouter une idée sœur |
| F2 ou double-clic | Renommer |
| Del | Supprimer l’idée sélectionnée |
| Touches fléchées | Déplacer la sélection |
| Molette / glisser | Zoom / panoramique |

Faites un clic droit sur une idée pour la **relier à une note** ; une idée liée affiche une icône de lien et ouvre cette note.
**Depuis les liens** crée une carte à partir des liens de la note, regroupés par type, et développe d’un niveau les liens propres aux
notes associées. **Exporter** enregistre la carte en image PNG ou SVG, ou en fichier FreeMind (`.mm`) ouvrable dans FreeMind,
Freeplane et XMind.

## Cartes mémoire

Les cartes mémoire transforment les notes en matériel de révision (voir [Révision, quiz et Anki](review-and-anki.md)).
Vous pouvez en créer de deux façons :

**Dans le texte de la note.** Les cartes sont créées automatiquement et mises à jour pendant vos modifications :

```markdown
Q: Who described the forgetting curve?
A: Hermann Ebbinghaus

{{c1::Retrieval practice}} is also called active recall.
```

Une question peut s’étendre sur plusieurs lignes, jusqu’à la ligne `A:`. Tout paragraphe contenant `{{c1::…}}` devient une
carte **à trous**, qui masque tour à tour chaque suppression. `{{c1::text::hint}}` affiche un indice au lieu de `[…]`.

**Dans l’onglet Cartes mémoire.** Utilisez *Insertion ▸ Carte mémoire…* (Ctrl+Shift+F) pour les cartes qui ne doivent pas apparaître
dans la note. Les cartes provenant du texte portent la mention *depuis le texte de la note* et se modifient dans le texte.

## Recherche

Le champ de recherche (Ctrl+F) effectue une recherche intégrale dans les titres, le texte et les tags, ignore les accents
et reconnaît les préfixes de mots : `forget` trouve ainsi *forgetting*. Ajoutez `tag:name` pour filtrer par tag, par
exemple `memory tag:psychology`. Les résultats sont triés par pertinence ; sans requête, les notes suivent le tri choisi
(*Dernière modification*, *Créée*, *Titre* ou *Les plus liées*).

## Corbeille

*Mettre à la corbeille* (Ctrl+Delete) masque une note sans la supprimer. Un bouton d’annulation apparaît immédiatement ; le bouton
**Corbeille** sous la liste des notes affiche les notes mises à la corbeille. Faites un clic droit pour **Restaurer** ou
**Supprimer définitivement**. **Vider la corbeille** supprime tout le contenu après confirmation. Les liens vers les notes dans la Corbeille sont masqués et réapparaissent lorsque la note est restaurée.
