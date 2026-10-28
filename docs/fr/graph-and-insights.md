# Graphe et Insights

## Le graphe

La page **Graphe** (Ctrl+2) représente vos notes en réseau : chaque cercle correspond à une note, sa taille dépend du nombre de liens qu’elle possède, et chaque ligne représente un lien.

![Le graphe, coloré par tag](../website/assets/screenshots/graph-light.png)

### Commandes

| Commande | Fonction |
|---|---|
| **Toutes les notes / Local** | Afficher toute la collection ou uniquement la note ouverte et les notes situées à **Profondeur** liens ou moins (en suivant les liens dans les deux sens). *Afficher dans le graphe* dans le menu ⋯ d’une note ouvre le graphe local. |
| **2D / 3D** | Passer d’une disposition plane déplaçable à une vue 3D pivotante. |
| **Couleur by** | Colorer par tag, par *Clusters: k-means*, par *Clusters: hierarchical* ou sans coloration. |
| **k** | Nombre de clusters. *Auto k* le choisit automatiquement (voir ci-dessous). |
| **Groupe** | Rapprocher les notes d’un même groupe et ombrer la zone de chaque groupe. |
| **Libellés** | Afficher les titres des notes. Dans les grands graphes, seuls les titres des notes les plus connectées apparaissent jusqu’au survol. |
| **Types de lien** | Masquer ou afficher certains types de liens. |
| **Rechercher dans le graphe** | Saisir une partie d’un titre et appuyer sur Entrée pour accéder à la note. |

En bas à droite se trouvent les commandes de zoom et d’ajustement, **recalculer la disposition**, **enregistrer comme image** (PNG) et **exporter ces notes** (ouvre la boîte de dialogue d’[exportation](export-import.md) avec les notes affichées).

**En 2D**, faites glisser une note pour la déplacer, l’arrière-plan pour effectuer un panoramique, et utilisez la molette pour zoomer. Double-cliquez sur une note pour l’ouvrir ; faites un clic droit pour accéder aux autres actions (ouvrir, graphe local, quiz sur ce voisinage, exporter avec les notes liées). L’image d’une note apparaît dans son cercle.

Plusieurs liens entre deux mêmes notes sont dessinés sous forme de **courbes distinctes**, chacune avec sa propre pointe de flèche le long de la courbe, afin qu’aucune ne masque les autres. Le survol ou la sélection d’une note **atténue les autres liens**, conserve les couleurs de type des liens de cette note et étiquette chaque voisine avec le type de lien **tel qu’il se lit depuis cette note**, par exemple *Soutient · Étendu par*. Le comportement est identique en 2D et en 3D.

**En 3D**, faites glisser pour pivoter, utilisez la molette pour zoomer et double-cliquez sur une note pour l’ouvrir. **Rotation automatique** fait tourner la vue. Les notes les plus proches sont plus grandes et plus lumineuses, ce qui facilite la perception de la profondeur ; chaque groupe apparaît comme un halo coloré diffus.

La disposition utilise un algorithme à forces (Fruchterman–Reingold) : les liens rapprochent les notes, toutes les notes se repoussent et une légère gravité maintient les composantes distinctes à l’écran. Le calcul s’exécute en arrière-plan et le résultat est mis en cache pour chaque vue.

### Coloration par tag

Chaque note prend la couleur de son **tag le plus courant**, celui utilisé par le plus grand nombre de notes affichées. Les grands thèmes du coffre obtiennent ainsi des couleurs distinctes.

### Coloration par cluster

Le clustering regroupe les notes **par sens**, qu’elles soient liées ou non. Chaque note devient un vecteur dans un espace sémantique calculé par analyse sémantique latente (LSA) à partir de son titre, de son texte et de ses tags. L’une des deux méthodes regroupe ensuite les vecteurs :

- **k-means** : algorithme de Lloyd avec initialisation k-means++, meilleur résultat de plusieurs exécutions. Rapide, il produit des groupes réguliers et de taille équilibrée.
- **Hiérarchique** : clustering agglomératif par liaison moyenne sur la distance cosinus, calculé avec l’algorithme de chaîne de plus proches voisins (O(n²)). Il convient mieux aux sujets imbriqués et aux groupes de tailles inégales. Au-delà de 4 000 notes, le coffre utilise k-means.

Avec **k automatique**, ZettelApp essaie les valeurs de k de 2 jusqu’à environ √(n/2) + 2 (12 au maximum) et retient celle qui donne le meilleur **score de silhouette**. Affiché sous la légende, ce score mesure la séparation des clusters : 1 correspond à une séparation parfaite ; autour de 0, les groupes se chevauchent. Chaque cluster porte le nom de ses mots les plus caractéristiques, c’est-à-dire ceux qui y sont plus fréquents que dans le reste du coffre.

### Groupes et couleurs

Lorsque **Groupe** est activé, les notes portant le même tag ou appartenant au même cluster sont rapprochées, et chaque groupe reçoit une zone légèrement ombrée avec son nom. La légende indique la taille des groupes. Cliquez sur l’un d’eux pour mettre ses notes en évidence.

Les couleurs des groupes et graphiques proviennent d’une palette **validée pour les déficiences de la vision des couleurs**, en mode clair comme en mode sombre. Elles sont attribuées dans un ordre fixe et ne sont jamais réutilisées : au-delà du huitième groupe, les suivants partagent la couleur grise neutre « Other ». Les **types de liens** utilisent aussi la forme des lignes : chacune possède son propre style (plein, tireté, pointillé, etc.) et les liens orientés ont une pointe (triangle, losange…). Choisissez-les dans *Outils ▸ Options ▸ Types de lien* (voir [Vos propres types de liens](notes-and-links.md#your-own-link-types)). La légende nomme toujours chaque élément ; l’information ne dépend donc pas uniquement des couleurs.

## Insights

La page **Insights** (Ctrl+3) résume votre coffre :

- **Tuiles** : notes (et nombre de notes dans la Corbeille), liens (et liens par note), tags, *notes sans lien* (bonnes candidates pour créer des liens), cartes mémoire et cartes à réviser aujourd’hui.
- **Notes ajoutées par mois** au cours des 12 derniers mois.
- **Tags principaux**, **Liens par type** et **Notes les plus connectées** (cliquez sur une barre pour ouvrir la note).
- **Sujets** : clusters k-means des notes, avec leurs mots-clés et leur taille.

Chaque graphique possède un bouton **Afficher sous forme de tableau** (icône de liste) qui affiche les mêmes valeurs sous forme de tableau ; survolez les barres pour voir leur valeur.
