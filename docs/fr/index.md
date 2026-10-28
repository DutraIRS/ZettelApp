# Documentation de ZettelApp

ZettelApp est un Zettelkasten pour Windows : un réseau de petites notes, chacune portant une idée, reliées par des liens qui précisent *comment* les idées sont liées. L’application suggère des liens pendant que vous écrivez, représente vos connaissances sous forme de graphe 2D ou 3D, transforme les notes en cartes mémoire et quiz, et fonctionne avec Anki, Zotero et des assistants d’IA.

Tout reste sur votre ordinateur, sauf si vous demandez une fonctionnalité qui nécessite Internet.

## Vous débutez ?

- **[Qu’est-ce qu’un Zettelkasten ?](what-is-zettelkasten.md)** : la méthode, son origine et la façon dont ZettelApp la met en pratique.
- **[Tutoriel : vos 30 premières minutes](tutorial.md)** : une visite guidée, de votre première note au graphe 3D.

## Sommaire

- [Bien démarrer](getting-started.md) : installation, premier coffre et découverte de la fenêtre
- [Notes et liens](notes-and-links.md) : Markdown, liens wiki, liens typés et orientés, tags, images, cartes mentales, cartes mémoire, recherche et Corbeille
- [Suggestions de liens](link-suggestions.md) : fonctionnement du classificateur Naive Bayes et réglages
- [Graphe et Insights](graph-and-insights.md) : graphes 2D et 3D, regroupement, clusters et graphiques
- [Révision, quiz et Anki](review-and-anki.md) : répétition espacée, modes quiz, synchronisation Anki et paquets
- [Zotero](zotero.md) : citer des références et rédiger des notes de lecture
- [Interroger vos notes (IA)](ai-assistant.md) : réponses de Claude, OpenAI ou Z.ai fondées sur vos notes
- [Serveur MCP](mcp-server.md) : permettre à Claude Desktop, Claude Code et aux autres clients MCP de lire votre coffre
- [Référence de l’API MCP](mcp-reference.md) : protocole, outils et erreurs, pour les personnes qui créent des clients MCP
- [Exporter et importer](export-import.md) : toute la collection ou un sous-graphe, dans sept formats
- [Raccourcis clavier](keyboard-shortcuts.md)
- [Confidentialité et sécurité](privacy-and-security.md) : données qui quittent votre ordinateur, emplacement des données et protections de ZettelApp
- [Développement](development.md) : compiler depuis les sources, lancer les tests et préparer une version
- [FAQ](faq.md)

## Les idées à la base de l’application

Un **Zettelkasten** (« boîte à fiches ») est une méthode de prise de notes rendue célèbre par le sociologue Niklas Luhmann. Chaque note est *atomique* (une idée, formulée avec vos propres mots) et possède un identifiant permanent. La valeur vient des connexions : relier une nouvelle note à des notes existantes vous oblige à réfléchir aux liens entre les idées, puis vous pouvez suivre ces liens pour découvrir des associations inattendues.

ZettelApp conserve cette discipline tout en supprimant les frictions :

- **Les identifiants sont automatiques** : chaque note reçoit un identifiant horodaté, par exemple `20261027153012`.
- **Les liens précisent les relations entre les notes** : *étaye*, *contredit*, *prolonge*, *exemple de*, *fait partie de*, *cite*, ou vos propres types de liens.
- **Les suggestions révèlent des connexions oubliées** : un classificateur compare une note au reste de votre coffre et apprend des liens que vous acceptez ou rejetez.
- **La révision est intégrée** : vos notes deviennent des cartes mémoire et des quiz, avec répétition espacée ou Anki.
