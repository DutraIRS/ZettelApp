# Suggestions de liens

Pendant que vous écrivez, le panneau **Suggestions de liens** répertorie les notes qui pourraient être liées à celle que
vous modifiez. Cliquez sur **Lier** pour les relier (la flèche voisine permet de choisir le type de lien) ou sur **✕** pour
rejeter une suggestion. Ces deux actions aident le modèle à apprendre. Survolez une suggestion pour comprendre *pourquoi*
elle a été proposée.

Les suggestions sont actualisées en arrière-plan environ une seconde après la fin de votre saisie, sans faire attendre
l’éditeur. Elles tiennent également compte du texte non enregistré.

## Fonctionnement

ZettelApp traite la question « faut-il relier ces deux notes ? » comme un problème de classification et y répond avec un
classificateur **Naive Bayes**. Pour une note *q* et chaque note candidate *c*, il calcule huit caractéristiques de
similarité et combine les indices en une probabilité.

### Caractéristiques

| Caractéristique | Mesure |
|---|---|
| **Similarité sémantique (LSA)** | Similarité cosinus dans un espace sémantique latent : SVD tronquée de la matrice TF-IDF (SVD randomisée, jusqu’à 64 dimensions). Des notes au vocabulaire apparenté sont proches même si elles partagent peu de mots exacts. |
| **Mots-clés communs (cosinus TF-IDF)** | Similarité cosinus des vecteurs TF-IDF (fréquence des termes sous-linéaire, fréquence inverse des documents lissée). Les titres comptent double ; les tags sont inclus. |
| **Similarité des titres (Levenshtein)** | 1 − distance d’édition ÷ longueur du titre le plus long. |
| **Similarité des titres (Jaro-Winkler)** | Similarité Jaro-Winkler des titres, qui favorise un début commun. |
| **Similarité du texte (Levenshtein)** | Distance d’édition normalisée entre les 400 premiers caractères des deux textes. |
| **Tags communs (Jaccard)** | Nombre de tags communs ÷ nombre total de tags. |
| **Titre mentionné dans le texte** | 1 si le titre de l’une des notes apparaît comme mot entier dans le texte de l’autre, sinon 0. |
| **Liens communs (Jaccard)** | Chevauchement des notes liées aux deux notes (triangles fermés dans le graphe). |

Le texte est converti en minuscules, les accents sont neutralisés (ainsi *informação* correspond à *informacao*), la
syntaxe Markdown est supprimée et les mots vides fréquents en anglais, portugais et espagnol sont ignorés. Les distances
d’édition utilisent [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) ; en son absence, un algorithme binaire parallèle
en Python pur produit les mêmes résultats.

### Des caractéristiques à une probabilité

Chaque valeur de caractéristique (entre 0 et 1) est classée dans l’une de **8 tranches**. Pour chaque caractéristique,
le modèle conserve le nombre de paires liées et non liées dans chaque tranche et estime :

```text
P(link | f1 … f8)  ∝  P(link) × Π P(fi | link)
```

L’**indice** d’une caractéristique est son rapport de vraisemblance logarithmique : log P(tranche | lien) − log P(tranche |
pas de lien). La probabilité affichée est la fonction logistique du log-rapport de cotes a priori, additionné à la somme
pondérée des indices.

**Origine des comptages.** Le modèle s’entraîne sur votre coffre à chaque changement notable :

- **exemples positifs** : chaque paire de notes liées, ainsi que les suggestions acceptées (jusqu’à 600 paires échantillonnées
dans les très grands coffres) ;
- **exemples négatifs** : paires aléatoires de notes non liées, à raison de trois par exemple positif, ainsi que toutes les
suggestions **rejetées**, comptées double.

**Un a priori opérationnel dès le premier jour.** Avant de disposer de données, chaque tranche commence avec des
*pseudo-comptages* de Dirichlet (10 par caractéristique et classe par défaut). Ils encodent une hypothèse faible : pour
les paires liées, les comptages augmentent avec la similarité ; pour les paires non liées, ils diminuent rapidement. Cela
suffit pour classer les suggestions d’un nouveau coffre. À mesure que vous créez des liens, les comptages réels prennent
le dessus et le modèle s’adapte à *votre* façon de relier les notes. Comme les exemples positifs et négatifs sont échantillonnés
dans un rapport de un à trois, la probabilité a priori P(link) est d’environ un quart (avec des pseudo-comptages correspondants).

**Deux corrections rendent les estimations plus fiables :**

1. **Aucune fuite d’étiquettes.** Les `[[liens wiki]]` sont retirés du texte avant le calcul des caractéristiques. Sinon, un lien
dans le texte ajouterait le titre de sa cible, et le modèle apprendrait à reconnaître les liens existants plutôt que les idées
connexes. Pour la même raison, lors de l’entraînement sur une paire liée, la caractéristique « liens communs » ignore le lien
entre les deux notes.
2. **Pondération des indices corrélés.** Naive Bayes suppose les caractéristiques indépendantes, mais certaines ne le sont pas :
TF-IDF et LSA se recoupent, comme les trois distances de chaînes. Traiter les indices corrélés comme indépendants rendrait
Naive Bayes trop confiant. ZettelApp multiplie donc chaque indice par **0,6** (Naive Bayes pondéré par caractéristique), ce qui
maintient des probabilités réalistes.

**Une caractéristique absente ou désactivée n’apporte aucun indice.** Si vous désactivez une caractéristique ou si elle ne peut
pas être calculée, elle ne contribue pas au résultat ; c’est le traitement naturel des valeurs manquantes par Naive Bayes.

### Classement rapide

La comparaison de longs textes par distance de Levenshtein est l’étape la plus lente ; le classement se fait donc en deux étapes.
Toutes les notes candidates sont d’abord évaluées sans la caractéristique de similarité du texte ; seules les 150 meilleures
reçoivent ensuite le score complet. Les notes déjà liées à la note courante et les paires rejetées ne sont jamais suggérées.

## Lire l’infobulle « pourquoi »

Survolez une suggestion pour voir l’estimation du modèle et l’indice de chaque caractéristique. Les valeurs positives plaident
en faveur d’un lien, les négatives contre. Le libellé près de la barre résume la probabilité : **forte** (50 % ou plus),
**probable** (25 % ou plus) ou **possible**.

Les probabilités sont des estimations honnêtes. Dans un coffre peu fourni, la plupart des paires ne sont pas liées ; une
suggestion à 15–30 % peut donc être bonne. Le classement est l’élément le plus important.

## Réglages

*Outils ▸ Options ▸ Suggestions de liens* :

| Option | Valeur par défaut | Effet |
|---|---|---|
| Suggérer des liens pendant la saisie | activé | Désactive complètement les suggestions du panneau. |
| Caractéristiques | les huit | Décochez les caractéristiques que vous ne souhaitez pas prendre en compte. |
| Afficher au maximum | 8 | Nombre de suggestions affichées. |
| Correspondance minimale | 10 % | Masque les suggestions dont la probabilité est inférieure. |
| Force de l’a priori | 10 | Nombre de pseudo-observations qui définissent l’a priori. Une valeur élevée lui fait davantage confiance plus longtemps ; une valeur basse permet au modèle de s’adapter plus rapidement à vos liens. |

- **Modèle details…** indique le nombre de paires liées et non liées utilisées pour l’entraînement ainsi que la capacité informative de
chaque caractéristique (divergence symétrique de Kullback–Leibler entre ses distributions pour les paires liées et non liées).
- **Forget dismissed suggestions** efface vos rejets : ces paires pourront être proposées à nouveau et ne compteront plus comme
exemples négatifs.
