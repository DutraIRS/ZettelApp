# Qu’est-ce qu’un Zettelkasten ?

Un **Zettelkasten** (en allemand, « boîte à fiches ») est une façon de prendre des notes pour qu’elles continuent à vous être utiles. Vous ne classez pas les notes par sujet : vous consignez chaque idée dans sa propre note et vous la **reliez** aux notes qui s’y rapportent. Au fil du temps, les liens forment un réseau. Le parcourir vous aide à réfléchir, à écrire et à découvrir des connexions que vous n’aviez pas prévues.

Vous découvrez la méthode ? Lisez cette page, puis essayez le [tutoriel](tutorial.md).

## Origines

La méthode est étroitement associée à **Niklas Luhmann (1927–1998)**, sociologue allemand surtout connu pour sa théorie des systèmes sociaux. Pendant près de quatre décennies, il a conservé une boîte d’environ **90 000 fiches**. Deux caractéristiques en faisaient bien plus qu’un simple fichier de fiches :

- **Chaque fiche avait une adresse fixe**, par exemple `21/3d7a`. Une nouvelle fiche consacrée à une pensée existante était placée juste après, avec une adresse ramifiée (`21/3d7a` → `21/3d7a1`), ce qui permettait aux raisonnements de se développer dans toutes les directions sans rien réorganiser.
- **Les fiches renvoyaient à d’autres fiches par leur adresse.** La boîte devenait ainsi un réseau d’idées plutôt qu’un ensemble de catégories.

Luhmann attribuait à sa boîte une grande partie de sa production considérable : environ 70 livres et près de 400 articles (les chiffres varient selon le décompte). Il a même écrit un essai sur le travail avec sa boîte comme une sorte de partenaire de conversation, *Kommunikation mit Zettelkästen* (1981). Les fiches ont depuis été numérisées par les archives Niklas Luhmann de l’université de Bielefeld.

La méthode s’est fait connaître hors du milieu universitaire grâce à **Sönke Ahrens et son livre *How to Take Smart Notes* (2017)**, ainsi qu’à des communautés comme zettelkasten.de.

## Principes fondamentaux

1. **Des notes atomiques : une idée par note.** Une note doit contenir une seule idée, assez restreinte pour être reliée précisément et réutilisée dans de nombreux contextes. Si son titre ne permet pas de la résumer, elle contient probablement plusieurs idées.
2. **Avec vos propres mots.** C’est en reformulant une idée que vous la comprenez. Copier un passage donne une impression de productivité, mais évite le travail de réflexion.
3. **Reliez chaque note en donnant une raison.** Lorsque vous ajoutez une note, demandez-vous à quelles notes existantes elle se rapporte et *comment*. En étaye-t-elle une ? En contredit-elle une autre ? Donne-t-elle un exemple d’une troisième ? Un lien justifié vaut bien plus qu’un tas de notes simplement apparentées.
4. **Des identifiants uniques et permanents.** Les titres changent et les sujets évoluent, mais l’adresse d’une note doit rester stable pour que les liens ne se brisent jamais.
5. **Laissez la structure émerger.** Au lieu de décider d’avance des catégories à l’aide de dossiers, laissez les groupes d’idées se former à partir des liens que vous créez. La structure se construit de bas en haut.
6. **Des notes de structure (notes-pivots).** Lorsqu’un sujet prend de l’ampleur, rédigez une note qui le cartographie : un bref aperçu reliant les notes essentielles dans un ordre logique. C’est un point d’entrée, pas un dossier.
7. **Révisez et faites ressurgir les idées.** Revenez aux notes, suivez leurs liens et laissez les anciennes idées rencontrer les nouvelles. Un Zettelkasten n’est un partenaire de réflexion que si vous continuez à dialoguer avec lui.

## Trois types de notes

Ahrens décrit trois types de notes, chacune ayant une durée de vie différente :

| Type | Description | Que faire ? |
|---|---|---|
| **Notes éphémères** | Rappels rapides d’une pensée, saisis n’importe où. | Traitez-les dans les jours qui suivent, puis supprimez-les. |
| **Notes de lecture** | Notes courtes sur une source, rédigées avec vos propres mots et accompagnées de la référence. | Gardez-les avec la source (par exemple, liées à son entrée Zotero). |
| **Notes permanentes** | Notes autonomes contenant vos idées, écrites pour votre futur vous et intégrées au réseau. | Elles constituent le Zettelkasten. Rédigez-les soigneusement et reliez-les. |

## Pièges fréquents

- **Collectionner au lieu de réfléchir.** Enregistrer des articles et des surlignages semble productif, mais un Zettelkasten ne grandit qu’avec les notes que vous rédigez et reliez. Ce piège est souvent appelé « illusion du collectionneur ».
- **Copier des citations.** Une note constituée principalement d’une citation n’est pas encore assimilée. Gardez la citation dans une note de lecture si nécessaire, et rédigez la note permanente avec vos propres mots.
- **Multiplier les tags.** Des dizaines de tags par note recréent des dossiers sous un autre nom. Quelques tags généraux vous aident à retrouver les notes ; les liens portent le sens.
- **Les notes orphelines.** Une note sans lien est difficile à retrouver et n’ajoute rien au réseau. Reliez chaque nouvelle note à au moins une note existante.
- **La sur-ingénierie.** La méthode nécessite très peu de choses : une note, un identifiant et un lien. Commencez à écrire ; la structure viendra ensuite.

## Comment ZettelApp applique la méthode

| Principe | Dans ZettelApp |
|---|---|
| Identifiants uniques et permanents | Chaque note reçoit automatiquement un identifiant horodaté (par exemple `20261027153012`). Reliez-la par titre ou identifiant : les [liens wiki](notes-and-links.md#wiki-links) restent valides même si le titre change. |
| Notes atomiques | Création rapide (Ctrl+N), enregistrement automatique et notes courtes faciles à prévisualiser. |
| Justifier les liens | [Liens typés](notes-and-links.md#typed-links) : `supports:: [[…]]`, *contredit*, *étend*, *exemple de*, *fait partie de*, *cite*, ou vos propres types. Les types orientés se lisent naturellement dans les deux sens (*Soutenu par*). |
| Ne manquer aucune connexion | Les [suggestions de liens](link-suggestions.md) comparent chaque note à votre coffre et apprennent de vos acceptations et rejets. Les **rétroliens** indiquent quelles notes pointent vers une note. |
| Laisser la structure émerger | Le [graphe](graph-and-insights.md) : un **graphe local** autour de chaque note et des **clusters** qui révèlent des sujets que vous n’aviez pas classés. *Insights* répertorie les **notes sans lien** à traiter. |
| Notes de structure | Cartes mentales dans les notes, liées aux notes qu’elles organisent, et liens *fait partie de*. |
| Notes de lecture | L’intégration [Zotero](zotero.md) crée des notes de lecture liées à l’élément et à son PDF. |
| Réviser et faire ressurgir | [Cartes mémoire, répétition espacée et quiz](review-and-anki.md) créés à partir de vos notes ou synchronisés avec Anki. |
| Tout conserver | Les notes vont dans la **Corbeille** au lieu d’être supprimées directement, et des sauvegardes quotidiennes protègent votre historique. |

Prêt à essayer ? Commencez le [tutoriel](tutorial.md).
