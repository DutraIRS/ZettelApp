# Servidor MCP

O [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) é um padrão aberto que permite que assistentes de
IA usem ferramentas e dados de outros programas. O ZettelApp inclui um servidor MCP, para que assistentes como o
**Claude Desktop** e o **Claude Code** possam pesquisar seu Zettelkasten, ler notas, seguir links tipados
e pedir sugestões de links enquanto ajudam você.

## Como ele roda

O servidor é um pequeno programa separado, o **`zettelapp-mcp.exe`**, instalado ao lado do `ZettelApp.exe`.
A partir do código-fonte, o mesmo servidor roda com `python -m zettelapp.mcp_main`. Seu cliente MCP o inicia quando
necessário e conversa com ele pela entrada/saída padrão. **Nenhuma porta de rede é aberta.**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

Sem `--vault`, ele serve o cofre que você abriu por último no ZettelApp. As alterações feitas pelo MCP aparecem no
aplicativo em alguns segundos.

## O interruptor MCP

Os clientes MCP só alcançam suas notas enquanto o **ZettelApp está aberto e o interruptor MCP na barra de status dele
está ligado**. O interruptor fica **desligado toda vez que o ZettelApp inicia**, então você decide, a cada sessão, se os assistentes
podem ler suas notas. Desligue-o, ou feche o ZettelApp, e o servidor para em cerca de um segundo.
Sem o interruptor, o servidor se recusa a iniciar e diz o motivo. Para o comportamento exato, veja a
[Referência da API MCP](mcp-reference.md).

## Conectar o Claude Desktop

Abra *Ferramentas ▸ Opções ▸ Servidor MCP* e clique em **Adicionar ao Claude Desktop…**. O ZettelApp se adiciona ao
`%APPDATA%\Claude\claude_desktop_config.json` (mantendo um backup do arquivo antigo). Depois reinicie o Claude
Desktop. Ligue o **interruptor MCP** na barra de status do ZettelApp antes de iniciar o Claude Desktop; se você o ligar
depois, reconecte o ZettelApp no Claude Desktop ou reinicie-o. Para fazer isso à mão, copie o trecho mostrado
nessa página para o arquivo. Ele se parece com isto:

```json
{
  "mcpServers": {
    "zettelapp": {
      "command": "C:\\Users\\me\\AppData\\Local\\Programs\\ZettelApp\\zettelapp-mcp.exe",
      "args": ["--vault", "C:\\Users\\me\\Documents\\ZettelApp"]
    }
  }
}
```

## Conectar o Claude Code

A mesma página de Opções mostra o comando para copiar:

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

Outros clientes MCP precisam do mesmo comando e dos mesmos argumentos. Assim como no Claude Desktop, ligue o MCP no ZettelApp
primeiro e reconecte o servidor (no Claude Code, `/mcp`) se você o ligar depois.

## Ferramentas

| Ferramenta | O que faz |
|---|---|
| `search_notes` | Busca de texto completo em títulos, textos e tags (filtros `tag:nome` funcionam). Uma consulta vazia lista as notas editadas recentemente. |
| `get_note` | O texto completo de uma nota, tags, link de fonte, datas, links tipados nos dois sentidos, flashcards e estrutura do mapa mental. |
| `list_tags` | Todas as tags, com o número de notas que usam cada uma. |
| `get_subgraph` | As notas a 1–4 links de uma nota e os links tipados entre elas (opcionalmente apenas alguns tipos de link). |
| `suggest_links` | Notas provavelmente relacionadas a uma nota, mas ainda não ligadas, ordenadas pelo [sugeridor Naive Bayes](link-suggestions.md). |
| `list_link_types` | Os tipos de link do cofre, como *apoia*, *contradiz* e *parte de*. |
| `create_note` | *(escrita)* Cria uma nota. `[[Título]]` no corpo liga a notas existentes. |
| `add_link` | *(escrita)* Adiciona um link tipado de uma nota para outra. |

## Somente leitura por padrão

O servidor abre seu cofre **somente para leitura**. As duas ferramentas de escrita só são oferecidas quando **ambas** as condições abaixo
são verdadeiras:

1. **Permitir que clientes MCP criem notas e links** está marcado em *Opções ▸ Servidor MCP*;
2. o servidor foi iniciado com `--allow-writes`. O trecho na página de Opções inclui essa opção assim que
   você marca a configuração.

A configuração é verificada de novo a cada escrita, então desmarcá-la tem efeito imediato. Ativá-la
exige que o cliente MCP reinicie o servidor.

O conteúdo das notas é passado ao assistente como dados, e o servidor diz ao assistente para não tratá-lo
como instruções. As entradas são validadas (IDs, tamanhos e limites), e o servidor nunca toca em arquivos
fora do cofre.

## Solução de problemas

- **O cliente diz que o servidor falhou ao iniciar, ou as chamadas de ferramenta dizem que o interruptor está desligado.** Abra o ZettelApp
  e ligue o MCP na barra de status dele, depois reconecte o servidor no seu cliente.
- **O servidor ainda falha ao iniciar.** Verifique se o caminho para `zettelapp-mcp.exe` está certo.
  Execute o comando você mesmo em um terminal: ele informa o que está errado (por exemplo "No ZettelApp vault
  found") na saída de erro padrão.
- **As ferramentas de escrita não aparecem.** Marque a opção *e* adicione `--allow-writes`, depois reinicie o cliente.
