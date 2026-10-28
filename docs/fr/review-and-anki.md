# Révision, quiz et Anki

Les notes sont faites pour nourrir la réflexion, et s’en souvenir est utile. ZettelApp transforme les notes en [cartes mémoire](notes-and-links.md#flashcards) et permet de les réviser dans l’application ou avec Anki.

## Répétition espacée

La page **Révision** (Ctrl+4) indique le nombre de cartes **à réviser aujourd’hui**. **Commencer la révision** les fait défiler :

1. Lisez la question et essayez de retrouver la réponse.
2. Appuyez sur **Espace** (ou *Afficher la réponse*).
3. Évaluez votre réponse : **Encore (1)**, **Difficile (2)**, **Bien (3)** ou **Facile (4)**. Survolez un bouton pour voir quand la carte réapparaîtra.

La planification utilise l’algorithme **SM-2** (l’algorithme SuperMemo dont Anki est issu) :

- Les nouvelles cartes réapparaissent après 1 jour, puis 6 jours, puis selon des intervalles qui augmentent avec leur *facteur de facilité* (2,5 au départ).
- *Encore* ramène la carte à 1 jour et réduit son facteur de facilité. *Difficile* raccourcit l’intervalle suivant et *Facile* l’allonge.

Les cartes à trous produisent une révision pour chaque suppression (`{{c1::…}}`, `{{c2::…}}`, …). Chaque question affiche un lien **From:** vers sa note.

## Quiz

**Quiz d’entraînement** crée un quiz à partir d’un périmètre : toute la collection, la note ouverte et ses notes liées (avec une profondeur donnée), ou les notes portant un tag. Choisissez un format et le nombre de questions :

| Format | Fonctionnement |
|---|---|
| **Cartes mémoire (répétition espacée)** | Comme une révision ; vos évaluations mettent à jour le calendrier. |
| **Choix multiple** | Choisissez la bonne réponse parmi quatre. Les mauvaises réponses proviennent d’autres cartes et ont une longueur similaire, ce qui les rend plausibles. Utilisez les touches 1–4. |
| **Saisir la réponse** | Saisissez la réponse et appuyez sur Entrée. La correction mesure la similarité d’édition (Levenshtein), sans tenir compte de la casse, des accents ni de la mise en forme : 85 % ou plus est correct, 60 % ou plus est « presque », afin que de petites fautes de frappe ne vous pénalisent pas. |
| **Nommez cette note** | Le texte d’une note s’affiche, mais les mots de son titre sont masqués ; choisissez le bon titre. Les mauvaises propositions sont les **notes les plus similaires** (TF-IDF) pour vous apprendre à distinguer des idées liées. Aucune carte mémoire n’est nécessaire. |

*Outils ▸ Quiz sur l'entourage de cette note* lance un quiz sur la note ouverte et les notes situées à deux liens de distance. Vous pouvez aussi faire un clic droit sur une note du graphe.

## Anki

ZettelApp fonctionne avec [Anki](https://apps.ankiweb.net/) de deux façons. Dans les deux cas, deux types de note sont utilisés : **ZettelApp Basic** et **ZettelApp Texte à trous**, avec les champs suivants :

- *Recto* et *Retour* (ou *Text* et *Extra* pour les cartes à trous), affichés à partir du Markdown ;
- *Source*, un lien vers la note ;
- *ZettelID* et *CardKey*.

Les tags de vos notes deviennent des tags Anki (les tags imbriqués deviennent `parent::child`), auxquels s’ajoute `zettelapp`. Les images des cartes sont incluses comme médias.

### Synchroniser avec AnkiConnect

1. Dans Anki, installez l’extension **AnkiConnect** (*Outils ▸ Add-ons ▸ Get Add-ons…*, code **2055492159**), puis redémarrez Anki.
2. Avec Anki ouvert, accédez à **Révision** dans ZettelApp, choisissez le nom du paquet (**Default deck** dans *Options ▸ Anki*, `ZettelApp` au départ) et le périmètre, puis cliquez sur **Synchroniser avec Anki** (ou *Outils ▸ Synchroniser avec Anki*). *Tester la connexion* vérifie la connexion.

ZettelApp mémorise la note Anki associée à chaque carte. Une nouvelle synchronisation **met à jour** les cartes au lieu d’en créer des doublons ; une carte peut être retrouvée grâce à son *CardKey* même si cette association a été perdue. Les cartes supprimées dans ZettelApp ne sont pas supprimées d’Anki.

ZettelApp communique uniquement avec AnkiConnect sur cet ordinateur (`127.0.0.1`, port 8765 par défaut, modifiable dans *Options ▸ Anki*).

### Exporter un paquet (.apkg)

**Exporter deck (.apkg)…** (ou *Fichier ▸ Exporter…* avec le format *Anki deck*) crée un paquet à importer dans Anki avec *Fichier ▸ Import*. Aucune extension n’est nécessaire. Les types de note, le paquet et l’identité de chaque carte sont stables : l’importation d’un nouvel export **met à jour** les cartes déjà importées.

### D’Anki vers vos notes

Le champ **Source** de chaque carte contient un lien `zettelapp://note/<id>`. Cliquez dessus dans Anki pour ouvrir la note dans ZettelApp. L’installateur configure cette association. Avec la version portable, utilisez *Options ▸ Intégration Windows ▸ Enregistrer les liens*. Le gestionnaire de liens n’accepte que les liens d’ouverture de note ; consultez [Confidentialité et sécurité](privacy-and-security.md).
