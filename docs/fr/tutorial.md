# Tutoriel : vos 30 premières minutes

Une visite pratique : chaque étape indique quoi faire et ce que vous devriez voir. Les étapes marquées *facultatif* nécessitent Zotero,
une clé d’IA ou Anki ; ignorez-les si vous ne les utilisez pas.

Vous découvrez la méthode ? Lisez d’abord [Qu’est-ce qu’un Zettelkasten ?](what-is-zettelkasten.md). Cela prend cinq minutes.

## 1. Installer et ouvrir le coffre de bienvenue

1. Téléchargez **ZettelApp-Setup.exe** depuis la [dernière version](https://github.com/DutraIRS/ZettelApp/releases/latest)
   et exécutez-le, ou décompressez **ZettelApp-Portable.zip** et lancez `ZettelApp.exe`.
2. Démarrez ZettelApp.

**Vous devriez voir** la page Notes avec onze notes de démarrage reliées dans un nouveau coffre situé dans
*Documents\ZettelApp*. La note « Welcome to ZettelApp » est ouverte dans l’éditeur. Après quelques instants, ZettelApp propose
également l’aventure facultative *Lost Prince of the Archive* ; choisissez **Pas maintenant** si vous préférez suivre ce guide écrit.

## 2. Créer une note

1. Appuyez sur **Ctrl+N**.
2. Saisissez un titre, par exemple *Répétition espacée*, puis appuyez sur **Entrée** pour passer au texte.
3. Formulez une idée avec vos propres mots, en deux ou trois phrases :
   *Réviser des informations à intervalles croissants favorise la mémoire à long terme, car chaque révision a lieu juste avant l’oubli.*

**Vous devriez voir** la note apparaître en haut de la liste. Il n’y a pas de bouton Enregistrer : les notes sont sauvegardées pendant
la saisie. L’identifiant sous le titre (par exemple `20261027153012`) est l’adresse permanente de la note.

## 3. Ajouter des tags

Cliquez sur **Ajouter un tag** sous le titre, saisissez `learning` et appuyez sur **Entrée**. Ajoutez aussi `memory`.

**Vous devriez voir** deux pastilles, *#learning* et *#mémoire*. Le filtre de tags au-dessus de la liste les propose désormais, et la
recherche `tag:memory` retrouve la note.

## 4. Relier une autre note

1. Créez une deuxième note (**Ctrl+N**) intitulée *Forgetting curve*, avec une phrase : *La mémoire s’efface rapidement si l’on ne révise pas.*
2. Revenez à *Répétition espacée* (cliquez dessus dans la liste). Dans le texte, saisissez `[[`, puis `Forg`.
3. Choisissez **Forgetting curve** dans la liste de complétion et appuyez sur **Entrée**.

**Vous devriez voir** `[[Forgetting curve]]` souligné dans le texte. Dans le panneau latéral, *Forgetting curve* apparaît sous **Liens**.
Cliquez sur le bouton en forme d’œil (**Split**) de la barre d’outils : l’aperçu affiche un lien cliquable.

## 5. Préciser *comment* les notes sont liées

Transformez le lien en lien typé en ajoutant `supports::` devant :

```markdown
supports:: [[Forgetting curve]]
```

**Vous devriez voir** le lien répertorié sous *Soutient* dans le panneau latéral. Ouvrez *Forgetting curve* : ses **Rétroliens** affichent
*Répétition espacée : **Soutenu par***, car *supports* est un type de lien orienté. Un simple `[[lien]]` signifie *Lié à*.

## 6. Utiliser une suggestion de lien

Rédigez quelques autres notes sur des idées apparentées, par exemple *Active recall* et *Interleaving*, avec une ou deux phrases et le tag
`learning`. Ouvrez ensuite l’une d’elles et consultez les **Suggestions de liens** dans le panneau latéral.

- Cliquez sur **Lier** pour accepter une suggestion. La petite flèche voisine permet de choisir un type de lien.
- Cliquez sur **✕** pour rejeter une suggestion inadaptée.
- Survolez une suggestion pour comprendre **pourquoi** elle a été proposée : chaque mesure fournit des indices pour ou contre le lien.

**Ce qu’apprend le modèle :** les suggestions acceptées deviennent des liens et entraînent le classificateur comme exemples positifs. Les
suggestions rejetées sont mémorisées comme exemples négatifs et ne sont plus proposées pour cette paire. Les suggestions s’améliorent à
mesure que vous utilisez cette fonction. Consultez [Suggestions de liens](link-suggestions.md).

![Notes avec des suggestions de liens](../website/assets/screenshots/notes-light.png)

## 7. Ajouter une image

Copiez une image (par exemple avec *Win+Shift+S*), cliquez dans le texte de la note et appuyez sur **Ctrl+V**. Vous pouvez aussi faire
glisser un fichier image dans la note ou utiliser *Insertion ▸ Image…*.

**Vous devriez voir** `![…](asset:…)` dans le texte et l’image dans l’aperçu. Comme il s’agit de la première image de la note, elle devient
aussi son **image de titre**, affichée près du titre et dans le cercle de la note sur le graphe.

## 8. Esquisser une carte mentale

1. Ouvrez l’onglet **Carte mentale** et cliquez sur **Ajouter une idée**.
2. Appuyez sur **Tab** pour ajouter une idée enfant, sur **Entrée** pour une idée sœur, sur **F2** pour renommer et sur **Suppr** pour supprimer.
   Les touches fléchées permettent de passer d’une idée à l’autre.
3. Cliquez maintenant sur **À partir des liens** et confirmez que la carte que vous venez de dessiner peut être remplacée.

**Vous devriez voir** une carte mentale construite à partir des liens de la note, regroupés par type, avec un niveau supplémentaire
correspondant aux liens propres à chaque note liée. Faites un clic droit sur une idée pour la relier à une note. Le bouton d’exportation
permet d’enregistrer la carte en PNG, SVG ou FreeMind.

![Une carte mentale](../website/assets/screenshots/mindmap-light.png)

## 9. Créer des cartes mémoire et les réviser

Ajoutez ces lignes au texte de *Répétition espacée* :

```markdown
Q: Why space reviews out?
A: Each effortful retrieval just before forgetting strengthens the memory.

{{c1::Hermann Ebbinghaus}} described the forgetting curve.
```

**Vous devriez voir** **Cartes mémoire (2)** dans l’onglet : une carte question-réponse et une carte à trous. Ouvrez ensuite **Révision**
(**Ctrl+4**) et cliquez sur **Commencer la révision**.

- Appuyez sur **Espace** pour afficher la réponse.
- Évaluez votre réponse avec **1–4** (*Encore, Difficile, Bien, Facile*).

Le calendrier SM-2 détermine quand chaque carte revient. Essayez aussi **Quiz d’entraînement ▸ Choix multiple** ou **Nommez cette note**.

![Un quiz à choix multiple](../website/assets/screenshots/quiz-light.png)

## 10. Explorer le graphe

Ouvrez **Graphe** (**Ctrl+2**).

1. Déplacez les notes par glisser-déposer, utilisez la molette pour zoomer et survolez une note pour mettre ses voisines en évidence.
2. Sélectionnez une note sur la page Notes, revenez au graphe et cliquez sur **Local**, puis réglez **Depth** sur 1, 2 ou 3.
3. Réglez **Couleur by** sur **Clusters: k-means**. Les notes sont regroupées par sens, et la légende nomme chaque cluster à partir de ses mots-clés.
4. Activez **Group** pour rapprocher les éléments de chaque groupe sur un fond ombré.
5. Cliquez sur **3D**, faites glisser pour pivoter et essayez **Rotate automatically**.

![Le graphe, coloré par tag et regroupé](../website/assets/screenshots/graph-light.png)

## 11. Consulter Insights

Ouvrez **Insights** (**Ctrl+3**) pour voir le nombre de notes, les notes par mois, les tags principaux, les liens par type et les notes les
plus connectées. **Notes sans lien** constitue votre liste de tâches : reliez ces notes à d’autres. Chaque graphique dispose d’une vue en tableau.

## 12. Citer un élément Zotero et rédiger une note de lecture (facultatif)

Zotero 7 ou une version ultérieure doit être ouvert, et l’option *Autoriser les autres applications de cet ordinateur à communiquer avec Zotero*
doit être activée dans *Paramètres ▸ Avancé* :

1. Choisissez *Insertion ▸ Référence Zotero…*, recherchez un élément et cliquez sur **Insertion citation** : un lien tel que *Ebbinghaus (1885)*
   qui ouvre l’élément dans Zotero est ajouté.
2. Recommencez et cliquez sur **Nouvelle literature note**.

**Vous devriez voir** une nouvelle note contenant la référence, les liens *Ouvrir in Zotero* et *Ouvrir PDF*, le résumé, les sections
*Idées clés* / *Mes réflexions* et le tag `literature`. Consultez [Zotero](zotero.md).

## 13. Interroger vos notes (facultatif)

1. Dans *Outils ▸ Options ▸ Assistant IA*, choisissez un fournisseur (Anthropic, OpenAI ou Z.ai), collez votre clé API et cliquez sur
   **Tester la connexion**.
2. Ouvrez **Ask** (**Ctrl+5**) et posez la question : *Comment l’espacement et la récupération en mémoire agissent-ils ensemble ?*

**Vous devriez voir** une réponse citant vos notes sous forme de liens, ainsi que la liste exacte des **sources envoyées**. Seules ces
notes et votre question quittent votre ordinateur. Consultez [Interroger vos notes](ai-assistant.md).

## 14. Exporter un sous-graphe et synchroniser avec Anki (facultatif)

1. Ouvrez une note, choisissez *Fichier ▸ Exporter…* (**Ctrl+Shift+E**), sélectionnez **Note actuelle et notes liées**, définissez la
   profondeur sur 2 et choisissez le format **Website**.
2. Ouvrez le fichier `index.html` de l’archive zip dans votre navigateur : il présente une petite partie de votre Zettelkasten.
3. Avec Anki ouvert et l’extension AnkiConnect (code `2055492159`) installée, ouvrez **Révision** et cliquez sur **Synchroniser avec Anki**.
   Le lien source de chaque carte ouvre la note dans ZettelApp.

Consultez [Exporter et importer](export-import.md) et [Anki](review-and-anki.md#anki).

## 15. Savoir où se trouvent vos données

- Vos notes sont dans le dossier du coffre (*Fichier ▸ Show Vault in File Explorer*) : `zettel.db` et `assets`.
- Une sauvegarde est créée automatiquement chaque jour ; *Fichier ▸ Sauvegarder le coffre maintenant* en crée une à tout moment.
- Les notes supprimées vont dans la **Corbeille**, sous la liste des notes, où vous pouvez les restaurer.

Consultez [Confidentialité et sécurité](privacy-and-security.md).

**Voilà !** Continuez à rédiger une idée par note, à justifier chaque nouveau lien et à laisser les suggestions et le graphe vous révéler
ce que vous avez construit. Les raccourcis figurent dans [Raccourcis clavier](keyboard-shortcuts.md).
