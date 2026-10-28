# Ihre Notizen befragen (KI)

Die Seite **Fragen** (Ctrl+5) beantwortet Fragen **anhand Ihrer Notizen** und enthält anklickbare Zitate.
Sie verwendet einen KI-Anbieter Ihrer Wahl mit Ihrem eigenen API-Schlüssel. Die Funktion ist vollständig
optional: Erst wenn Sie eine Frage stellen, werden Daten gesendet.

![Ihre Notizen befragen](../website/assets/screenshots/ask-light.png)

## Einrichten

1. Besorgen Sie sich einen API-Schlüssel bei einem der unterstützten Anbieter.
2. Öffnen Sie *Werkzeuge ▸ Optionen ▸ KI-Assistent*. Wählen Sie den **Anbieter**, fügen Sie den **API-Schlüssel** ein und wählen Sie ein **Modell** aus (*Liste aktualisieren* fragt beim Anbieter ab, welche Modelle Ihr Schlüssel verwenden darf).
   Sie können mehrere Schlüssel pro Anbieter speichern (zum Beispiel einen privaten und einen beruflichen).
   Verwenden Sie *Hinzufügen…*, *Umbenennen…* und *Entfernen* neben der Schlüsselliste. Der ausgewählte
   Schlüssel wird für „Fragen“ verwendet.
3. Klicken Sie auf **Verbindung testen** und dann auf **OK**.

| Anbieter | Standardmodell | Weitere empfohlene Modelle | Endpunkt |
|---|---|---|---|
| **Anthropic Claude** (Standard) | `claude-opus-5-5` | `claude-sonnet-5-5`, `claude-haiku-5-5` | `https://api.anthropic.com` |
| **OpenAI** | `gpt-6.1-sol` | `gpt-6-astra`, `gpt-6-luna` | `https://api.openai.com/v1` |
| **Z.ai (GLM)** | `glm-5.3` | `glm-5.3-flash`, `glm-4.7-flash` | `https://api.z.ai/api/paas/v4` |

Sie können eine beliebige Modell-ID eingeben, auf die Ihr Schlüssel Zugriff hat. Unter **Endpunkt (optional)**
können Sie die Adresse überschreiben, zum Beispiel für einen Z.ai-Coding-Plan-Endpunkt, einen
OpenAI-kompatiblen Proxy oder ein Modell auf Ihrem eigenen Computer (`http://localhost:…`). Adressen
müssen `https://` verwenden; `http://` wird nur für `localhost` akzeptiert.

Mit Claude können Sie außerdem den **Aufwand** (niedrig bis maximal) festlegen: Ein höherer Aufwand
bedeutet, dass vor der Antwort mehr nachgedacht wird, und verursacht höhere Kosten. Standardmäßig ist
*mittel* eingestellt.

## Eigenes LLM verwenden

„Fragen“ verwendet **Ihr eigenes Konto** beim ausgewählten Anbieter; dieser rechnet die Nutzung direkt mit
Ihnen ab. ZettelApp hat keinen eigenen KI-Dienst. Ihr API-Schlüssel wird im **Windows-Anmeldeinformations-
Manager** gespeichert, niemals in Einstellungsdateien.

- **Anbieter**: Anthropic Claude, OpenAI und Z.ai (GLM) unter *Werkzeuge ▸ Optionen ▸ KI-Assistent ▸ Anbieter*. Wählen Sie ein **Modell** aus der Liste (*Liste aktualisieren* fragt ab, welche Modelle Ihr Schlüssel verwenden darf) oder geben Sie eine beliebige erreichbare Modell-ID ein.
- **Eigener Server**: Jeder Dienst mit einer **OpenAI-kompatiblen Chat-Completions-API** funktioniert. Wählen Sie **OpenAI** und geben Sie unter **Endpunkt (optional)** die Basisadresse ein, etwa `https://my-proxy.example.com/v1`, `http://localhost:11434/v1` (Ollama) oder `http://localhost:1234/v1` (LM Studio). `http://` wird nur für `localhost`, `127.0.0.1` und `::1` akzeptiert; alle anderen Adressen müssen `https://` verwenden. Bei diesen lokalen Adressen darf das Feld **API-Schlüssel** leer bleiben.
- **Prüfen**: Klicken Sie auf **Verbindung testen**. Bei einem lokalen Modell verlassen Ihre Frage und Notizen den Computer nicht.
- **Was gesendet wird**: Nur Ihre Frage und die relevantesten Notizen, die lokal ermittelt werden. Die Anzahl ist das Feld **Anzahl der Notizen** auf der Seite „Fragen“ (standardmäßig 8). Die Liste *Gesendete Quellen* zeigt genau, welche Notizen gesendet wurden.

## Eine Frage stellen

Geben Sie eine Frage ein und drücken Sie **Fragen** (Ctrl+Enter). Unter **Suchen in** wählen Sie, wo
gesucht wird: in der gesamten Sammlung, der geöffneten Notiz und ihren verknüpften Notizen oder in den
Notizen mit einem Tag. Legen Sie die **Anzahl der Notizen** fest, die gesendet werden sollen.

So funktioniert es:

1. ZettelApp findet **auf Ihrem Computer** die relevantesten Notizen. Dafür verwendet es dieselbe TF-IDF- und LSA-Ähnlichkeit wie der [Linkvorschlag](link-suggestions.md). Bei *Aktuelle Notiz und verknüpfte Notizen* steht die geöffnete Notiz immer an erster Stelle.
2. Ihre Frage und diese Notizen werden an den Anbieter gesendet; es werden höchstens 120.000 Zeichen aus Notizen übertragen. Eine gekürzte Notiz endet mit dem sichtbaren Hinweis „[note truncated]“. Die Liste **Gesendete Quellen** zeigt genau, welche Notizen gesendet wurden.
3. Die Antwort wird während des Schreibens angezeigt. Zitate wie `[[20261027153012]]` erscheinen als Links zu den Notizen. Mit **Stoppen** brechen Sie die Erstellung ab.

Das Modell wird angewiesen, nur anhand Ihrer Notizen zu antworten und mitzuteilen, wenn diese keine Antwort
enthalten. Mit **Kopieren** kopieren Sie die Antwort als Markdown. **Als Notiz speichern** legt sie als neue
Notiz mit dem Tag `ai-answer` und `cites::`-Links zu ihren Quellen ab.

## Datenschutz und Sicherheit

- **Nur Ihre Anfrage wird gesendet**: Ihre Frage und die Notizen unter *Gesendete Quellen*. Vor dem Senden erinnert Sie ein Hinweis daran (aktivieren Sie *Nicht erneut anzeigen*, um ihn zu überspringen).
- Ihr **API-Schlüssel** wird im **Windows-Anmeldeinformations-Manager** (`ZettelApp/llm/<provider>`) gespeichert, niemals in Einstellungsdateien oder Protokollen. Er wird aus jeder angezeigten Fehlermeldung entfernt. Mit *Schlüssel entfernen* löschen Sie ihn.
- **Das Modell hat keine Tools.** Es kann weder im Web suchen noch Code ausführen oder Ihre Notizen ändern. In einer Notiz (oder importierten Datei) versteckte Anweisungen können deshalb nichts auslösen. Die Antwort wird mit demselben sicheren Renderer wie Notizen angezeigt, ohne HTML oder Skripte.
- Bei Claude verwendet ZettelApp das offizielle Anthropic-SDK und aktiviert **serverseitigen Ausweichmechanismus bei Ablehnung**: Lehnt ein Sicherheitsklassifikator eine Anfrage ab, wiederholt Anthropic sie mit dem empfohlenen Ausweichmodell. Dies gilt für Claude Opus 5.5, Opus 5, Sonnet 5.5 und Fable 5.1.
- Für die von Ihnen gesendeten Daten gelten die Nutzungsbedingungen und Datenschutzrichtlinien des jeweiligen Anbieters.

## Einen weiteren Anbieter hinzufügen

Anbieter sind in einer kleinen Registry eingetragen (`PROVIDERS` in `zettelapp/core/llm.py`). Ein Dienst,
der ein vorhandenes Protokoll unterstützt (Anthropic Messages API oder OpenAI-kompatible
Chat-Completions, die viele Anbieter anbieten), benötigt **einen Eintrag**: Name, Endpunkt,
Standardmodell und die Seite, auf der Nutzer einen Schlüssel erhalten. Für ein neues Protokoll ist eine
kleine Adapterklasse nötig. Siehe [Entwicklung](development.md).
