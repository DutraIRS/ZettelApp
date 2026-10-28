# Foire aux questions

### ZettelApp est-il gratuit ?

Oui. Il est gratuit et open source, publié dans le domaine public sous licence [The Unlicense](https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE). La fonction d’IA facultative utilise votre propre clé API ; le fournisseur vous facture directement.

### Comment soutenir ZettelApp ?

Merci de poser la question ! Vous pouvez soutenir le développement sur [Ko-fi](https://ko-fi.com/dutrairs). Les entreprises peuvent parrainer un élément précis de la [feuille de route](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md) ; contactez-nous via [GitHub](https://github.com/DutraIRS/ZettelApp). Les sponsors sont remerciés dans les notes de version. Signaler des bogues, améliorer la documentation et faire connaître ZettelApp sont également utiles.

### Internet est-il nécessaire ?

Non. Tout fonctionne hors ligne. Internet n’est utilisé que pour une petite vérification des mises à jour au démarrage (désactivable), lorsque vous posez une question dans la page **Ask** et lorsque vous ouvrez un lien. Consultez [Confidentialité et sécurité](privacy-and-security.md).

### ZettelApp recherche-t-il les mises à jour ?

Oui, une fois au démarrage : une seule requête récupère un petit fichier sur le site du projet, sans aucune information vous concernant ou concernant vos notes. Si une nouvelle version existe, une notification apparaît en bas à droite. Désactivez-la avec *Outils ▸ Options ▸ Général ▸ Vérifier les mises à jour au démarrage de ZettelApp*, ou avec **Ne pas rechercher les mises à jour** dans la notification. Consultez [Bien démarrer](getting-started.md#updates).

### À quoi sert le bouton MCP dans la barre d’état ?

Il permet aux assistants d’IA tels que Claude Desktop ou Claude Code d’utiliser vos notes par l’intermédiaire de [MCP](mcp-server.md). Il est **désactivé à chaque démarrage de ZettelApp**. Tant qu’il est désactivé, ou que ZettelApp est fermé, les assistants ne peuvent pas accéder à vos notes. Après l’activation, reconnectez ZettelApp dans votre client MCP (ou redémarrez ce client).

### Puis-je utiliser un modèle sur mon ordinateur ?

Oui. Dans *Outils ▸ Options ▸ Assistant IA*, choisissez **OpenAI** et définissez **Point d’accès** sur votre serveur local, par exemple `http://localhost:11434/v1` (Ollama) ou `http://localhost:1234/v1` (LM Studio). Aucune clé API n’est nécessaire pour `localhost`. Consultez [Utiliser votre propre LLM](ai-assistant.md#bring-your-own-llm).

### Où sont mes notes ?

Dans votre dossier de coffre, par défaut **Documents\ZettelApp** : une base de données `zettel.db` et un dossier `assets`. *Fichier ▸ Show Vault in File Explorer* l’ouvre.

### Puis-je utiliser OneDrive, Dropbox ou Google Drive ?

Oui. Placez le coffre dans un dossier synchronisé (*Fichier ▸ Nouvelle Vault…*). Fermez ZettelApp sur un ordinateur avant d’ouvrir le même coffre sur un autre, car deux ordinateurs qui écrivent simultanément risquent de créer des conflits.

### Comment transférer mes données sur un autre ordinateur ?

Copiez le dossier du coffre, ou utilisez *Fichier ▸ Exporter…* ▸ **ZettelApp archive**, puis importez l’archive sur l’autre ordinateur.

### Puis-je utiliser mon coffre Obsidian ?

Oui. *Fichier ▸ Importer un dossier Markdown…* importe les fichiers Markdown avec leur front matter, leurs `#tags`, `[[liens]]` et images. Vos fichiers Obsidian ne sont pas modifiés. Dans l’autre sens, exportez en **Markdown files** et ouvrez le dossier dans Obsidian.

### Pourquoi les identifiants « Zettel » ressemblent-ils à 20261027153012 ?

Chaque note reçoit un identifiant permanent correspondant à son heure de création (année, mois, jour, heure, minute, seconde). Les titres peuvent changer, pas les identifiants : les liens basés sur un identifiant ne se brisent donc jamais. Vous avez rarement besoin de les consulter.

### Quelle différence entre un lien dans le texte et un lien dans le panneau latéral ?

Les deux sont de vrais liens. Les `[[liens]]` du texte font partie de votre rédaction et sont supprimés si vous les effacez du texte. Les liens ajoutés avec **Add link…** ou en acceptant une suggestion ne figurent pas dans le texte. Vous pouvez modifier leur type, inverser leur direction ou les supprimer dans le panneau latéral.

### Pourquoi une suggestion indique-t-elle seulement « 18 % · possible » ?

Il s’agit de l’estimation honnête du modèle concernant la probabilité que vous reliiez les deux notes. Dans un coffre récent ou peu fourni, la plupart des paires de notes ne sont pas liées ; même les bonnes suggestions commencent donc avec un score modeste. Le classement compte davantage, et les estimations s’améliorent à mesure que vous acceptez ou rejetez des liens. Consultez [Suggestions de liens](link-suggestions.md).

### L’application fonctionne-t-elle sur macOS ou Linux ?

Pas encore. Les paquets Linux (.deb, AppImage) et macOS figurent dans la [feuille de route](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

### L’application est-elle disponible dans d’autres langues ?

Oui. L’installateur et l’application sont traduits en espagnol, portugais (Brésil), français, allemand, italien, russe, chinois simplifié, japonais, coréen et arabe. Par défaut, l’application suit la langue de Windows ; vous pouvez la modifier dans *Options*. Les textes non traduits s’affichent en anglais.

### Comment désinstaller l’application et qu’adviendra-t-il de mes données ?

*Paramètres ▸ Applications ▸ Applications installées ▸ ZettelApp ▸ Désinstaller*. Le programme de désinstallation propose l’option **Supprimer aussi mes paramètres et données ZettelApp**, décochée par défaut. Si vous la cochez, elle supprime les préférences, les clés API enregistrées, les journaux, le cache et les sauvegardes automatiques, **ainsi que toutes vos notes** (bases de données et pièces jointes des coffres). Si elle reste décochée, vos notes sont conservées. Pour la version portable, supprimez son dossier ; les préférences se trouvent dans le registre sous `HKEY_CURRENT_USER\Software\ZettelApp`, et les journaux et sauvegardes dans `%LOCALAPPDATA%\ZettelApp`.

### Un problème est survenu. Où trouver les journaux ?

Dans `%LOCALAPPDATA%\ZettelApp\Logs`. Veuillez joindre la partie pertinente lorsque vous [signalez un problème](https://github.com/DutraIRS/ZettelApp/issues). Vérifiez d’abord qu’elle ne contient aucune information privée.
