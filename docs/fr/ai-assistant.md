# Interroger vos notes (IA)

La page **Ask** (Ctrl+5) répond à vos questions **à partir de vos notes**, avec des citations cliquables. Elle utilise le fournisseur d’IA de votre choix et votre propre clé API. La fonction est entièrement facultative : aucune donnée n’est envoyée tant que vous ne posez pas de question.

![Interroger vos notes](../website/assets/screenshots/ask-light.png)

## Configuration

1. Obtenez une clé API auprès de l’un des fournisseurs pris en charge.
2. Ouvrez *Outils ▸ Options ▸ Assistant IA*. Choisissez le **fournisseur**, collez la **clé API** et sélectionnez un **modèle** (*Actualiser la liste* demande au fournisseur quels modèles sont accessibles avec votre clé).

   Vous pouvez enregistrer plusieurs clés par fournisseur (par exemple, une clé personnelle et une clé professionnelle). Utilisez *Ajouter…*, *Renommer…* et *Retirer* à côté de la liste des clés ; Ask utilise la clé sélectionnée.
3. Cliquez sur **Tester la connexion**, puis sur **OK**.

| Fournisseur | Modèle par défaut | Autres modèles suggérés | Point de terminaison |
|---|---|---|---|
| **Anthropic Claude** (par défaut) | `claude-opus-5-5` | `claude-sonnet-5-5`, `claude-haiku-5-5` | `https://api.anthropic.com` |
| **OpenAI** | `gpt-6.1-sol` | `gpt-6-astra`, `gpt-6-luna` | `https://api.openai.com/v1` |
| **Z.ai (GLM)** | `glm-5.3` | `glm-5.3-flash`, `glm-4.7-flash` | `https://api.z.ai/api/paas/v4` |

Vous pouvez saisir n’importe quel identifiant de modèle accessible avec votre clé. **Point d'accès (facultatif)** remplace l’adresse, par exemple pour utiliser un point de terminaison de forfait de programmation Z.ai, un proxy compatible OpenAI ou un modèle exécuté sur votre ordinateur (`http://localhost:…`). Les adresses doivent utiliser `https://` ; `http://` est accepté uniquement pour `localhost`.

Avec Claude, vous pouvez également régler l’**effort** (de faible à maximale) : plus il est élevé, plus la réflexion avant réponse est longue et coûteuse. La valeur par défaut est *moyen*.

## Utiliser votre propre LLM

Ask utilise **votre propre compte** chez le fournisseur choisi ; celui-ci vous facture l’utilisation. ZettelApp n’a pas de service d’IA propre. Votre clé API est enregistrée dans le **Gestionnaire d’identifiants Windows**, jamais dans les fichiers de paramètres.

- **Fournisseurs** : Anthropic Claude, OpenAI et Z.ai (GLM), dans *Outils ▸ Options ▸ Assistant IA ▸ Fournisseur*. Choisissez un **Modèle** dans la liste (*Actualiser la liste* demande au fournisseur les modèles accessibles avec votre clé) ou saisissez un identifiant de modèle disponible.
- **Votre propre serveur** : tout service proposant une API **complétion de conversation compatible avec OpenAI** est compatible. Choisissez **OpenAI** et indiquez son adresse de base dans **Point d'accès (facultatif)**, par exemple `https://my-proxy.example.com/v1`, `http://localhost:11434/v1` (Ollama) ou `http://localhost:1234/v1` (LM Studio). `http://` est accepté uniquement pour `localhost`, `127.0.0.1` et `::1` ; les autres adresses doivent utiliser `https://`. Pour ces adresses locales, la **clé API** peut rester vide.
- **Vérifier la connexion** : cliquez sur **Tester la connexion**. Avec un modèle local, votre question et vos notes ne quittent pas votre ordinateur.
- **Données transmises** : uniquement votre question et les notes les plus pertinentes, trouvées sur votre ordinateur. Le nombre de notes est défini par le champ **nombre de notes** de la page Ask (8 par défaut) ; la liste *Sources envoyées* montre précisément lesquelles ont été envoyées.

## Poser une question

Saisissez une question et appuyez sur **Ask** (Ctrl+Enter). Choisissez où chercher dans **Rechercher dans** : toute la collection, la note ouverte et ses notes liées, ou les notes portant un tag. Choisissez le nombre de notes à envoyer.

Déroulement :

1. ZettelApp trouve les notes les plus pertinentes **sur votre ordinateur**, en utilisant les mêmes similarités TF-IDF et LSA que le [suggesteur de liens](link-suggestions.md). Avec *Note actuelle et notes liées*, la note ouverte apparaît toujours en premier.
2. Votre question et ces notes sont envoyées au fournisseur ; le texte des notes est limité à 120 000 caractères. Une note tronquée pour respecter cette limite se termine par le marqueur visible « [note truncated] ». La liste **Sources envoyées** indique exactement quelles notes ont été transmises.
3. La réponse s’affiche au fur et à mesure. Les citations telles que `[[20261027153012]]` sont des liens vers les notes. **Arrêter** annule la génération.

Le modèle reçoit pour instruction de répondre uniquement à partir de vos notes et de signaler quand elles ne contiennent pas la réponse. **Copier** copie la réponse au format Markdown. **Enregistrer comme note** l’enregistre dans une nouvelle note portant le tag `ai-answer` et des liens `cites::` vers ses sources.

## Confidentialité et sécurité

- **Seules les données nécessaires à votre demande sont envoyées** : votre question et les notes figurant sous *Sources envoyées*. Un avis vous le rappelle avant la question (cochez *Ne plus afficher* pour ne plus l’afficher).
- **Votre clé API** est stockée dans le **Gestionnaire d’identifiants Windows** (sous `ZettelApp/llm/<provider>`), jamais dans les fichiers de paramètres ou les journaux ; elle est supprimée des messages d’erreur affichés. *Retirer key* la supprime.
- **Le modèle ne dispose d’aucun outil.** Il ne peut ni chercher sur le Web, ni exécuter de code, ni modifier vos notes. Des instructions cachées dans une note (ou un fichier importé) ne peuvent donc pas lui faire effectuer d’action. La réponse utilise le même affichage sécurisé que les notes, sans HTML ni scripts.
- Avec Claude, ZettelApp utilise le SDK officiel d’Anthropic et active le **repli de refus côté serveur** : si un classificateur de sécurité refuse une requête, Anthropic la réessaie avec son modèle de repli recommandé. Cela concerne Claude Opus 5.5, Opus 5, Sonnet 5.5 et Fable 5.1.
- Les conditions et politiques de données de chaque fournisseur s’appliquent aux données que vous lui envoyez.

## Ajouter un autre fournisseur

Les fournisseurs sont déclarés dans un registre simple (`PROVIDERS` dans `zettelapp/core/llm.py`). Un service utilisant un protocole déjà pris en charge (l’API Messages d’Anthropic ou les complétions de chat au format OpenAI, proposées par de nombreux fournisseurs) ne nécessite qu’**une entrée** : son nom, son point de terminaison, son modèle par défaut et la page permettant d’obtenir une clé. Un nouveau protocole nécessite une petite classe d’adaptation. Consultez [Développement](development.md).
