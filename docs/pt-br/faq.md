# Perguntas frequentes

### O ZettelApp é gratuito?

Sim. É gratuito e de código aberto, liberado para o domínio público sob
[The Unlicense](https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE). O recurso opcional de IA usa
a sua própria chave de API, então o provedor cobra diretamente de você.

### Como posso apoiar o ZettelApp?

Obrigado por perguntar! Você pode apoiar o desenvolvimento no [Ko-fi](https://ko-fi.com/dutrairs). Empresas podem
patrocinar um item específico do [roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md); entre em
contato pelo [GitHub](https://github.com/DutraIRS/ZettelApp). Os patrocinadores são agradecidos nas notas de versão.
Relatar bugs, melhorar a documentação e divulgar o ZettelApp também ajudam.

### Precisa de internet?

Não. Tudo funciona offline. A internet é usada apenas para uma pequena verificação de atualização na inicialização (que você pode
desativar), quando você faz uma pergunta na página **Perguntar** e quando você abre um link. Veja
[Privacidade e segurança](privacy-and-security.md).

### O ZettelApp verifica atualizações?

Sim, uma vez na inicialização: uma requisição para um pequeno arquivo no site do projeto, sem nada sobre você ou
suas notas. Se existir uma versão mais nova, um aviso aparece no canto inferior direito. Desative-o em
*Ferramentas ▸ Opções ▸ Geral ▸ Verificar atualizações quando o ZettelApp iniciar*, ou com **Não verificar atualizações**
no aviso. Veja [Primeiros passos](getting-started.md#updates).

### O que é o interruptor MCP na barra de status?

Ele permite que assistentes de IA como o Claude Desktop ou o Claude Code usem suas notas por meio do
[MCP](mcp-server.md). Fica **desligado toda vez que o ZettelApp inicia**. Enquanto estiver desligado, ou com o ZettelApp fechado,
os assistentes não conseguem alcançar suas notas. Depois de ligá-lo, reconecte o ZettelApp no seu cliente MCP (ou
reinicie o cliente).

### Posso usar um modelo no meu próprio computador?

Sim. Em *Ferramentas ▸ Opções ▸ Assistente de IA*, escolha **OpenAI** e defina o **Endpoint** com o seu servidor local, por
exemplo `http://localhost:11434/v1` (Ollama) ou `http://localhost:1234/v1` (LM Studio). Nenhuma chave de API é
necessária para `localhost`. Veja [Traga seu próprio LLM](ai-assistant.md#bring-your-own-llm).

### Onde estão minhas notas?

Na pasta do seu cofre, por padrão **Documentos\ZettelApp**: um banco de dados `zettel.db` e uma pasta `assets`.
*Arquivo ▸ Mostrar cofre no Explorador de Arquivos* a abre.

### Posso usar com OneDrive, Dropbox ou Google Drive?

Sim. Coloque o cofre em uma pasta sincronizada (*Arquivo ▸ Novo cofre…*). Feche o ZettelApp em um computador antes de
abrir o mesmo cofre em outro, porque dois computadores gravando ao mesmo tempo podem causar conflitos.

### Como mudo para outro computador?

Copie a pasta do cofre, ou use *Arquivo ▸ Exportar…* ▸ **Arquivo do ZettelApp** e importe-o no outro
computador.

### Posso usar meu cofre do Obsidian?

Sim. *Arquivo ▸ Importar pasta Markdown…* importa arquivos Markdown com seu front matter, `#tags`,
`[[links]]` e imagens. Seus arquivos do Obsidian não são alterados. No sentido contrário, exporte para **arquivos
Markdown** e abra a pasta no Obsidian.

### Por que IDs "Zettel" como 20261027153012?

Cada nota recebe um ID permanente a partir do momento em que foi criada (ano, mês, dia, hora, minuto, segundo).
Os títulos podem mudar; os IDs não, então os links por ID nunca quebram. Você raramente precisa vê-los.

### Qual é a diferença entre um link no texto e um link no painel lateral?

Ambos são links de verdade. Os `[[Links]]` no texto fazem parte da sua escrita e são removidos apagando-os
do texto. Os links adicionados com **Adicionar link…** ou aceitando uma sugestão não estão no texto. Você pode
alterar o tipo deles, inverter a direção ou removê-los no painel lateral.

### Por que uma sugestão diz apenas "18% · possível"?

O número é a estimativa honesta do modelo de que você ligaria as duas notas. Em um cofre jovem ou esparso,
a maioria dos pares de notas não tem relação, então até boas sugestões começam modestas. A ordem das sugestões
é o que mais importa, e as estimativas melhoram conforme você liga e dispensa. Veja
[Sugestões de links](link-suggestions.md).

### Funciona no macOS ou no Linux?

Ainda não. Pacotes para Linux (.deb, AppImage) e o macOS estão no
[roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

### O aplicativo está disponível em outros idiomas?

Sim. O instalador e o aplicativo são traduzidos para espanhol, português (Brasil), francês, alemão, italiano,
russo, chinês simplificado, japonês, coreano e árabe. Por padrão, o aplicativo segue o idioma do seu Windows;
altere-o em *Opções*. Textos ausentes recorrem ao inglês.

### Como desinstalo, e o que acontece com meus dados?

*Configurações ▸ Aplicativos ▸ Aplicativos instalados ▸ ZettelApp ▸ Desinstalar*. O desinstalador oferece uma opção desmarcada **Excluir
também minhas configurações e dados do ZettelApp** que remove preferências, chaves de API salvas, logs, cache e
backups automáticos, **e todas as suas notas** (bancos de dados e anexos dos cofres). Desmarcada, suas notas são mantidas. Na
versão portátil, exclua a pasta dela; as preferências ficam no registro em
`HKEY_CURRENT_USER\Software\ZettelApp`, e os logs e backups em `%LOCALAPPDATA%\ZettelApp`.

### Algo deu errado. Onde estão os logs?

Em `%LOCALAPPDATA%\ZettelApp\Logs`. Inclua a parte relevante quando
[relatar um problema](https://github.com/DutraIRS/ZettelApp/issues). Verifique antes que ela não contém nada
privado.
