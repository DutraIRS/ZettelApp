# Pergunte às suas notas (IA)

A página **Perguntar** (Ctrl+5) responde a perguntas **a partir das suas notas**, com citações nas quais você pode clicar. Ela usa um
provedor de IA à sua escolha, com a sua própria chave de API. É totalmente opcional: nada é enviado a lugar algum até
você fazer uma pergunta.

![Pergunte às suas notas](../website/assets/screenshots/ask-light.png)

## Configuração

1. Obtenha uma chave de API de um dos provedores compatíveis.
2. Abra *Ferramentas ▸ Opções ▸ Assistente de IA*. Escolha o **provedor**, cole a **chave de API** e escolha um
   **modelo** (*Atualizar lista* pergunta ao provedor quais modelos a sua chave pode usar).

   Você pode salvar várias chaves por provedor (por exemplo pessoal e de trabalho). Use *Adicionar…*, *Renomear…* e
   *Remover* ao lado da lista de chaves; a chave selecionada é a usada pelo Perguntar.
3. Pressione **Testar conexão** e depois **OK**.

| Provedor | Modelo padrão | Outros modelos sugeridos | Endpoint |
|---|---|---|---|
| **Anthropic Claude** (padrão) | `claude-opus-5-5` | `claude-sonnet-5-5`, `claude-haiku-5-5` | `https://api.anthropic.com` |
| **OpenAI** | `gpt-6.1-sol` | `gpt-6-astra`, `gpt-6-luna` | `https://api.openai.com/v1` |
| **Z.ai (GLM)** | `glm-5.3` | `glm-5.3-flash`, `glm-4.7-flash` | `https://api.z.ai/api/paas/v4` |

Você pode digitar qualquer ID de modelo ao qual a sua chave tenha acesso. **Endpoint (opcional)** substitui o endereço, por
exemplo para usar um endpoint de plano de programação da Z.ai, um proxy compatível com a OpenAI ou um modelo rodando no seu próprio
computador (`http://localhost:…`). Os endereços devem usar `https://`; `http://` simples é aceito apenas para
`localhost`.

Com o Claude você também pode definir o **esforço** (de baixo a máximo): um esforço maior pensa mais antes de responder e
custa mais. O padrão é *médio*.

## Traga seu próprio LLM

O Perguntar usa **a sua própria conta** no provedor que você escolher, então qualquer uso é cobrado a você por esse provedor.
O ZettelApp não tem um serviço de IA próprio. Sua chave de API é salva no **Gerenciador de Credenciais do Windows**, nunca em
arquivos de configuração.

- **Provedores**: Anthropic Claude, OpenAI e Z.ai (GLM), em *Ferramentas ▸ Opções ▸ Assistente de IA ▸ Provedor*.
  Escolha um **Modelo** na lista (*Atualizar lista* pergunta ao provedor quais modelos a sua chave pode usar) ou digite
  qualquer ID de modelo ao qual a sua chave tenha acesso.
- **Seu próprio servidor**: qualquer serviço que ofereça uma API de **chat completions no estilo OpenAI** funciona. Escolha
  **OpenAI** e defina **Endpoint (opcional)** com o endereço base dele, por exemplo
  `https://my-proxy.example.com/v1`, `http://localhost:11434/v1` (Ollama) ou `http://localhost:1234/v1`
  (LM Studio). `http://` simples é aceito apenas para `localhost`, `127.0.0.1` e `::1`; todo o resto
  deve usar `https://`. Para esses endereços locais, a **chave de API** pode ficar vazia.
- **Verifique**: pressione **Testar conexão**. Com um modelo local, sua pergunta e suas notas nunca saem do seu
  computador.
- **O que é enviado**: apenas sua pergunta e as notas mais relevantes, encontradas no seu computador. O número de
  notas é a caixa **quantas notas** na página Perguntar (8 por padrão), e a lista *Fontes enviadas* mostra
  exatamente quais foram.

## Faça uma pergunta

Digite uma pergunta e pressione **Perguntar** (Ctrl+Enter). Escolha onde procurar em **Buscar em**: a coleção
inteira, a nota aberta e suas notas ligadas ou as notas com uma tag. Escolha **quantas notas** enviar.

O que acontece:

1. O ZettelApp encontra as notas mais relevantes **no seu computador**, usando a mesma similaridade TF-IDF e LSA
   do [sugeridor de links](link-suggestions.md). Com *Nota atual e notas ligadas*, a nota aberta
   vem sempre primeiro.
2. Sua pergunta e essas notas são enviadas ao provedor, com no máximo 120.000 caracteres de notas. Uma nota
   cortada para caber termina com um marcador visível "[note truncated]". A lista **Fontes enviadas** mostra exatamente quais
   notas foram enviadas.
3. A resposta chega aos poucos, conforme é escrita. Citações como `[[20261027153012]]` aparecem como links para as
   notas. **Parar** a cancela.

O modelo é instruído a responder somente a partir das suas notas e a dizer quando elas não contêm a resposta. **Copiar**
copia a resposta como Markdown. **Salvar como nota** a guarda como uma nova nota com a tag `ai-answer`, com links `cites::`
para suas fontes.

## Privacidade e segurança

- **Somente o que você pergunta é enviado**: sua pergunta e as notas listadas em *Fontes enviadas*. Um aviso
  lembra você disso antes de perguntar (marque *Não mostrar novamente* para ignorá-lo).
- **Sua chave de API** é armazenada no **Gerenciador de Credenciais do Windows** (como `ZettelApp/llm/<provider>`), nunca em
  arquivos de configuração nem em logs, e é removida de qualquer mensagem de erro exibida a você. *Remover chave* a exclui.
- **O modelo não tem ferramentas.** Ele não pode pesquisar na web, executar código nem alterar suas notas, então instruções
  escondidas em uma nota (ou em um arquivo importado) não conseguem fazê-lo fazer nada. A resposta é exibida pelo mesmo
  renderizador seguro das notas, sem HTML nem scripts.
- Com o Claude, o ZettelApp usa o SDK oficial da Anthropic e opta pelo **fallback de recusa no lado do servidor**: se
  uma requisição for recusada por um classificador de segurança, a Anthropic a tenta novamente no modelo de fallback recomendado.
  Isso vale para o Claude Opus 5.5, Opus 5, Sonnet 5.5 e Fable 5.1.
- Os termos e as políticas de dados de cada provedor se aplicam ao que você envia.

## Adicionando outro provedor

Os provedores ficam em um pequeno registro (`PROVIDERS` em `zettelapp/core/llm.py`). Um serviço que fala um
protocolo existente (a Messages API da Anthropic, ou chat completions no estilo OpenAI, que muitos provedores
oferecem) é **uma entrada**: seu nome, endpoint, modelo padrão e a página onde os usuários obtêm uma chave. Um novo
protocolo precisa de uma pequena classe adaptadora. Veja [Desenvolvimento](development.md).
