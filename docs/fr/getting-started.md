# Bien démarrer

## Installation

ZettelApp fonctionne sous **Windows 10 (21H2 ou version ultérieure) et Windows 11, en 64 bits**. Téléchargez l’application depuis la [dernière version](https://github.com/DutraIRS/ZettelApp/releases/latest) :

| Téléchargement | À utiliser si… |
|---|---|
| `ZettelApp-Setup.exe` | Vous souhaitez une installation standard avec une entrée dans le menu Démarrer, un programme de désinstallation dans *Paramètres ▸ Applications* et des liens `zettelapp://` qui ouvrent des notes depuis Anki. Aucun droit d’administrateur n’est requis : l’installation concerne uniquement votre compte. |
| `ZettelApp-Portable.zip` | Vous ne pouvez pas installer de logiciel ou souhaitez lancer l’application depuis une clé USB. Décompressez l’archive où vous voulez et exécutez `ZettelApp.exe`. |

L’installateur demande la langue souhaitée et suggère la langue d’affichage de Windows. L’application et l’installateur sont traduits en 11 langues ; vous pouvez changer la langue de l’application dans *Options*.

Chaque version indique les sommes de contrôle SHA-256 (`SHA256SUMS.txt`). Pour vérifier un téléchargement dans PowerShell :

```powershell
Get-FileHash .\ZettelApp-Setup.exe -Algorithm SHA256
```

### « Windows a protégé votre ordinateur »

Les versions ne sont pas encore signées ; Microsoft Defender SmartScreen peut donc afficher un avertissement lors du premier lancement de l’installateur. Si vous l’avez téléchargé depuis la page officielle et que la somme de contrôle correspond, choisissez **Plus d’informations ▸ Exécuter quand même**. La signature de code figure sur la [feuille de route](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

## Votre premier coffre

Un **coffre** est un dossier contenant vos notes : un fichier de base de données (`zettel.db`) et un dossier `assets` pour les images. Au premier démarrage, ZettelApp en crée un dans **Documents\ZettelApp**, avec onze notes de démarrage reliées entre elles. La note *Bienvenue dans ZettelApp* présente les liens, tags, images, cartes mentales, cartes mémoire et le reste de l’application. Une aventure facultative d’une dizaine de minutes propose la même visite sous forme d’actions concrètes. Les nouveaux coffres créés avec *Fichier ▸ Nouvelle Vault…* ou *Fichier ▸ Ouvrir un coffre…* reçoivent les mêmes notes de démarrage ; vous pouvez donc travailler ailleurs, par exemple dans un dossier OneDrive. *Fichier ▸ Ouvrir Recent* répertorie les coffres récemment utilisés.

Les notes sont enregistrées automatiquement pendant la saisie. Il n’y a pas de bouton Enregistrer.

## Découverte de la fenêtre

![La page Notes](../website/assets/screenshots/notes-light.png)

La **barre de navigation** à gauche permet de passer d’une page à l’autre (Ctrl+1 à Ctrl+5) :

- **Notes** : liste des notes, éditeur et panneau latéral.
  - La *liste* comporte la recherche (les filtres `tag:name` fonctionnent aussi), un filtre par tag, le tri et la Corbeille.
  - L’*éditeur* contient le titre, les tags, un lien source facultatif et des onglets pour la **Note** (Markdown, modes Edit, Split et Preview), sa **carte mentale** et ses **cartes mémoire**.
  - Le *panneau latéral* affiche les **Suggestions de liens**, les **Liens** de la note et ses **rétroliens**.
- **Graphe** : représentation de vos notes en réseau 2D ou 3D, avec couleurs par tag ou par cluster de sujets.
- **Insights** : statistiques et graphiques sur votre coffre.
- **Révision** : révisions espacées, quiz et Anki.
- **Ask** : posez des questions sur vos notes avec le fournisseur d’IA de votre choix (facultatif).

**Options** (en bas de la barre ou dans *Outils ▸ Options…*, Ctrl+,) regroupe les préférences : thème, taille du texte de l’éditeur, suggestions de liens, types de liens, IA, serveur MCP, Anki, Zotero, intégration Windows et sauvegardes.

L’application suit le réglage **clair/sombre** et la **couleur d’accentuation** de Windows. Vous pouvez imposer un thème dans *Affichage ▸ Thème*.

## Mises à jour

Environ quatre secondes après le démarrage, ZettelApp envoie une requête HTTPS à `https://dutrairs.github.io/ZettelApp/version.json` pour connaître la version la plus récente. Rien d’autre n’est envoyé (seul l’agent utilisateur `ZettelApp/<version>` est transmis) ; en cas d’échec, aucun message ne s’affiche. Si une nouvelle version existe, une petite notification apparaît dans le coin inférieur droit, au plus une fois par version. Elle ne prend jamais le focus. **Télécharger** ouvre la page des versions dans votre navigateur, **✕** ferme la notification et **Ne pas rechercher les mises à jour** désactive la recherche. Vous pouvez la réactiver dans *Outils ▸ Options ▸ Général ▸ Vérifier les mises à jour au démarrage de ZettelApp*. ZettelApp n’installe jamais de mise à jour automatiquement.

## Désinstallation

Utilisez *Paramètres Windows ▸ Applications ▸ Applications installées ▸ ZettelApp ▸ Désinstaller*. Après confirmation, une boîte de dialogue propose l’option **Supprimer aussi mes paramètres et données ZettelApp**, décochée par défaut. Elle supprime vos paramètres, clés API enregistrées, journaux, cache et sauvegardes automatiques (`%LOCALAPPDATA%\ZettelApp`), **ainsi que toutes vos notes** (base de données et pièces jointes de vos coffres). Laissez-la décochée pour conserver vos notes. Pour la version portable, supprimez son dossier.

## Étapes suivantes

- Découvrez la syntaxe des notes dans [Notes et liens](notes-and-links.md).
- Découvrez le fonctionnement des [suggestions de liens](link-suggestions.md).
- Appuyez sur **F1** à tout moment pour ouvrir cette documentation ou consultez les [raccourcis clavier](keyboard-shortcuts.md).
