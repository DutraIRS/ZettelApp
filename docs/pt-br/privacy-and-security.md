# Privacidade e segurança

## O que sai do seu computador

**Nada, a menos que você peça, exceto uma pequena verificação de atualização.** O ZettelApp não tem contas,
telemetria nem anúncios, e não carrega nada da internet enquanto você trabalha. Estas são todas as requisições
de rede que ele pode fazer:

| Quando… | O ZettelApp contata | O que é enviado |
|---|---|---|
| Cerca de 4 segundos depois que o ZettelApp inicia (pode ser desativado) | `https://dutrairs.github.io/ZettelApp/version.json` | Uma requisição HTTPS para esse arquivo, com o cabeçalho `User-Agent: ZettelApp/<version>`. Nada mais: nenhuma nota, configuração ou identificador. Qualquer falha é silenciosa. Veja [Atualizações](getting-started.md#updates). |
| Você faz uma pergunta na página **Perguntar** | O provedor de IA que você configurou (Anthropic, OpenAI, Z.ai ou seu próprio endpoint) | Sua pergunta e as notas listadas em *Fontes enviadas* |
| Você testa a conexão de IA ou atualiza a lista de modelos | O mesmo provedor | Sua chave de API, para autenticação |
| Você usa **Sincronizar com o Anki** | O AnkiConnect **neste computador** (`127.0.0.1`) | Os flashcards do escopo escolhido |
| Você usa **Inserir ▸ Referência do Zotero** ou *Testar conexão* nas opções do Zotero | O Zotero **neste computador** (`127.0.0.1`) | Suas palavras de busca (somente leitura) |
| Você clica em um link web, ou usa *Ajuda ▸ Site / Documentação / Verificar atualizações*, ou o botão **Baixar** do aviso de atualização | Seu navegador abre a página | Nada do ZettelApp |

Para interromper a verificação de atualização, desmarque *Ferramentas ▸ Opções ▸ Geral ▸ Verificar atualizações quando o ZettelApp iniciar*;
o ZettelApp então não faz nenhuma requisição até você fazer uma pergunta ou usar um dos outros recursos acima.

As conexões locais com o Anki e o Zotero nunca usam proxy, então não podem ser redirecionadas para fora do seu computador.
O servidor MCP não faz nenhuma requisição de rede.

## Onde seus dados ficam

| O quê | Onde |
|---|---|
| Notas, links, flashcards, histórico de revisão | A pasta do seu cofre: `zettel.db` (SQLite). Por padrão **Documentos\ZettelApp**. |
| Imagens | A pasta `assets` do cofre. |
| Preferências | O registro, em `HKEY_CURRENT_USER\Software\ZettelApp\ZettelApp`. |
| Chaves de API | **Gerenciador de Credenciais do Windows** (`ZettelApp/llm/…`), nunca em arquivos nem no registro. |
| Logs | `%LOCALAPPDATA%\ZettelApp\Logs` (rotacionados, no máximo alguns MB). Registram erros, não suas notas, e nunca incluem chaves de API. |
| Backups automáticos | `%LOCALAPPDATA%\ZettelApp\Backups` |
| Pequeno cache da interface | `%LOCALAPPDATA%\ZettelApp\Cache` |

O cofre é uma pasta comum: você pode copiá-la, fazer backup dela ou mantê-la no OneDrive. O ZettelApp grava o
banco de dados com sincronização total, uma configuração escolhida para se adequar a pastas sincronizadas. Evite abrir o mesmo cofre em dois
computadores ao mesmo tempo.

## Backups e desfazer

- **Backups diários:** na primeira vez que um cofre é aberto a cada dia, uma cópia consistente de seu banco de dados é
  salva. Os 10 mais recentes são mantidos (*Opções ▸ Backups*). *Arquivo ▸ Fazer backup do cofre agora* faz um a qualquer momento.
  As imagens são armazenadas por conteúdo e nunca são excluídas automaticamente.
- **Lixeira:** as notas excluídas vão primeiro para a Lixeira e podem ser restauradas até você esvaziá-la.
- **Salvamento automático:** as notas são salvas enquanto você digita. Uma caixa de diálogo de falha informa erros inesperados e grava detalhes no
  log.

## Como o ZettelApp protege você

As notas podem vir de importações, da web ou de respostas de IA, então o ZettelApp trata seu conteúdo como não confiável:

- **Sem conteúdo ativo.** O HTML bruto nas notas é exibido como texto, nunca renderizado; nada em uma nota pode executar
  scripts. A pré-visualização da nota carrega imagens **somente da pasta `assets` do próprio cofre**, nunca da
  web nem de outro lugar do disco.
- **Lista de links permitidos.** Clicar em um link abre apenas páginas web (`http`/`https`), e-mail (`mailto`), notas,
  links de *selecionar item* / *abrir PDF* do Zotero e links para arquivos locais (abaixo). `javascript:` e outros
  esquemas são recusados.
- **Links de arquivos locais apenas revelam o arquivo.** Um link `file:///` abre o **Explorador de Arquivos com o arquivo
  selecionado**; o arquivo em si nunca é aberto nem executado. Somente caminhos em uma unidade local são permitidos. Caminhos de rede
  (UNC), como `\\server\share`, são recusados, porque consultar um deles pode enviar suas credenciais do Windows
  a esse servidor.
- **As imagens são verificadas pelo conteúdo**, não pelo nome do arquivo. Somente PNG, JPEG, GIF, WebP e BMP de até 25 MB são
  aceitos; o SVG é recusado porque pode conter scripts. A verificação cobre a assinatura do arquivo e o tamanho
  compactado; as dimensões em pixels são verificadas quando a imagem é exibida pela primeira vez.
- **Importações seguras.** Os arquivos são verificados quanto a truques de caminho ("zip-slip") e bombas de descompressão. Cada campo
  é validado e tem o tamanho limitado, as importações Markdown não conseguem alcançar nada fora da pasta importada, e uma
  importação que falha deixa o cofre inalterado: as importações rodam em uma única transação de banco de dados que é revertida em
  qualquer erro.
- **Exportações seguras.** Os sites exportados não contêm scripts e trazem uma Content-Security-Policy rigorosa. Os arquivos
  são gravados de forma atômica.
- **Segurança do banco de dados.** Todas as consultas ao banco de dados usam parâmetros vinculados, e o texto de busca nunca é interpretado como
  sintaxe de consulta.
- **Os links `zettelapp://`** (usados pelos cartões do Anki) só podem *abrir uma nota pelo seu ID*. Qualquer outra requisição é
  ignorada.
- **Uma única instância por usuário.** Uma segunda inicialização repassa sua requisição ao aplicativo em execução por um pipe nomeado do Windows
  que somente a sua conta de usuário pode acessar.
- **Segurança da IA.** O modelo de IA não recebe ferramentas, então instruções escondidas em uma nota não podem fazê-lo agir, e sua
  resposta é renderizada com o mesmo renderizador seguro. As chaves de API ficam no Gerenciador de Credenciais e são removidas das
  mensagens de erro.
- **Servidor MCP e seu interruptor.** Os clientes MCP só alcançam suas notas enquanto o ZettelApp está aberto **e** o
  interruptor MCP na barra de status dele está ligado. O interruptor fica desligado toda vez que o ZettelApp inicia e nunca é salvo.
  O servidor é somente leitura por padrão, roda apenas quando seu cliente MCP o inicia e usa a entrada/saída
  padrão, sem porta de rede. Veja [Servidor MCP](mcp-server.md).

## Desinstalação

Desinstale em *Configurações do Windows ▸ Aplicativos ▸ Aplicativos instalados ▸ ZettelApp ▸ Desinstalar*. O desinstalador oferece
uma opção desmarcada, **Excluir também minhas configurações e dados do ZettelApp**. Se você marcá-la, ela remove suas
configurações, as chaves de API salvas no Gerenciador de Credenciais, os logs, o cache e os backups automáticos
(`%LOCALAPPDATA%\ZettelApp`) **e todas as suas notas** (o banco de dados e os anexos dos seus cofres). Desmarcada,
suas notas permanecem onde estão.

Encontrou um problema de segurança? Por favor, relate-o em particular; veja
[SECURITY.md](https://github.com/DutraIRS/ZettelApp/blob/main/SECURITY.md).
