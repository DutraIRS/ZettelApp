# Zotero

ZettelApp se connecte à [Zotero](https://www.zotero.org/), le gestionnaire de références gratuit, pour citer des références dans vos notes et rédiger des **notes de lecture** liées à l’élément et à son PDF dans votre bibliothèque.

## Configuration

1. Utilisez **Zotero 7 ou une version ultérieure** et laissez-le ouvert.
2. Dans Zotero, ouvrez *Paramètres ▸ Avancé* et activez **« Autoriser les autres applications de cet ordinateur à communiquer avec Zotero »**.
3. Dans ZettelApp, *Outils ▸ Options ▸ Zotero ▸ Tester la connexion* doit afficher *Connecté to Zotero*.

ZettelApp lit votre bibliothèque à l’aide de l’**API locale** de Zotero sur cet ordinateur (`127.0.0.1`, port 23119 par défaut). L’application ne fait que lire : elle ne modifie jamais votre bibliothèque Zotero et aucune donnée n’est transmise par Internet. La recherche porte sur votre bibliothèque personnelle (*My Library*), pas encore sur les bibliothèques de groupe.

## Citer une référence

*Insertion ▸ Référence Zotero…*, ou le bouton en forme de livres dans la barre d’outils de l’éditeur, ouvre un champ de recherche. Saisissez une partie d’un titre, un nom d’auteur ou une année. Si le champ est vide, les éléments modifiés récemment s’affichent. Sélectionnez un élément pour consulter ses détails, puis :

- **Insertion citation** (ou double-cliquez) ajoute une citation auteur-année qui ouvre l’élément dans Zotero :

  ```markdown
  [Ebbinghaus (1885)](zotero://select/library/items/ABCD2345)
  ```

- **Nouvelle literature note** crée une note pour l’élément, contenant :
  - le titre de l’élément ;
  - une ligne de référence (auteurs, année, titre, publication, DOI) ;
  - des liens vers *Ouvrir in Zotero*, *Ouvrir PDF* (si l’élément possède une pièce jointe PDF) et le DOI ;
  - le résumé ;
  - des sections *Idées clés* et *Mes réflexions* à compléter ;
  - le tag `literature` ainsi que les tags Zotero de l’élément ;
  - l’élément Zotero comme **lien source** de la note.

Les notes de lecture sont le lien classique entre le Zettelkasten et vos notes permanentes : formulez les idées essentielles avec vos propres mots, puis reliez-les aux notes qu’elles étayent, prolongent ou contredisent.

## Liens Zotero

Cliquer sur un lien Zotero dans une note ouvre l’élément dans Zotero ou son PDF dans le lecteur Zotero. Par sécurité, ZettelApp ne suit que deux types de liens Zotero et refuse toute autre adresse `zotero://` :

```text
zotero://select/library/items/<KEY>
zotero://open-pdf/library/items/<KEY>?page=<N>
```

Les liens de bibliothèque de groupe (`zotero://select/groups/<ID>/items/<KEY>`) sont également acceptés. Vous pouvez aussi coller un lien Zotero dans le champ **lien source** d’une note. Dans Zotero, faites un clic droit sur un élément et copiez son lien (ou utilisez une extension telle que Zutilo), puis collez-le.

## Dépannage

| Message | Solution |
|---|---|
| *Impossible de joindre Zotero* | Démarrez Zotero 7 ou une version ultérieure. Vérifiez le port dans *Options ▸ Zotero* (23119 par défaut). |
| *Zotero a refusé la requête* | Activez le réglage *Allow other applications…* (étape 2 ci-dessus). |
| *Cette version de Zotero n’a pas d’API locale* | Mettez Zotero à jour vers la version 7 ou ultérieure. |
