# Primeiros passos

## Instalação

O ZettelApp roda no **Windows 10 (21H2 ou posterior) e no Windows 11, 64 bits**. Baixe-o da
[versão mais recente](https://github.com/DutraIRS/ZettelApp/releases/latest):

| Download | Use quando |
|---|---|
| `ZettelApp-Setup.exe` | Você quer uma instalação normal, com entrada no menu Iniciar, um desinstalador em *Configurações ▸ Aplicativos* e links `zettelapp://` que abrem notas a partir do Anki. Não são necessários direitos de administrador: ele instala somente para a sua conta. |
| `ZettelApp-Portable.zip` | Você não pode instalar software ou quer executá-lo de um pen drive USB. Descompacte-o em qualquer lugar e execute `ZettelApp.exe`. |

O instalador pergunta qual idioma usar e sugere o idioma de exibição do seu Windows. O instalador
e o aplicativo são traduzidos para 11 idiomas; altere o idioma do aplicativo em *Opções*.

Cada versão lista somas de verificação SHA-256 (`SHA256SUMS.txt`). Para conferir um download no PowerShell:

```powershell
Get-FileHash .\ZettelApp-Setup.exe -Algorithm SHA256
```

### "O Windows protegeu seu computador"

As compilações ainda não têm assinatura de código, então o Microsoft Defender SmartScreen pode exibir um aviso na primeira vez que você executar o
instalador. Se você o baixou da página oficial de versões e a soma de verificação confere, escolha
**Mais informações ▸ Executar assim mesmo**. A assinatura de código está no [roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

## Seu primeiro cofre

Um **cofre** é uma pasta que guarda suas notas: um arquivo de banco de dados (`zettel.db`) e uma pasta `assets` para imagens.
Na primeira inicialização, o ZettelApp cria um em **Documentos\ZettelApp** com onze notas iniciais ligadas entre si. A nota
*Bem-vindo ao ZettelApp* conduz por links, tags, imagens, mapas mentais, flashcards e o restante do aplicativo. Uma
aventura opcional de dez minutos oferece o mesmo tour por meio de ações reais. Os novos cofres criados com
*Arquivo ▸ Novo cofre…* ou *Arquivo ▸ Abrir cofre…* recebem o mesmo material inicial, então você pode trabalhar em outro lugar,
por exemplo em uma pasta do OneDrive.
*Arquivo ▸ Abrir recentes* lista os cofres que você usou por último.

As notas são salvas automaticamente enquanto você digita. Não há botão Salvar.

## Um tour pela janela

![A página Notas](../website/assets/screenshots/notes-light.png)

A **barra de navegação** à esquerda alterna entre as páginas (Ctrl+1 a Ctrl+5):

- **Notas**: a lista de notas, o editor e um painel lateral.
  - A *lista* tem busca (filtros `tag:nome` também funcionam), um filtro de tags, ordenação e a Lixeira.
  - O *editor* tem o título, as tags, um link de fonte opcional e abas para a **Nota** (Markdown, com
    os modos Editar, Dividir e Pré-visualizar), seu **Mapa mental** e seus **Flashcards**.
  - O *painel lateral* mostra os **Links sugeridos**, os **Links** da nota e seus **Backlinks**.
- **Grafo**: suas notas como uma rede em 2D ou 3D, coloridas por tag ou por cluster de assunto.
- **Insights**: estatísticas e gráficos sobre o seu cofre.
- **Revisão**: revisões por repetição espaçada, quizzes e Anki.
- **Perguntar**: faça perguntas sobre suas notas usando um provedor de IA à sua escolha (opcional).

As **Opções** (na parte inferior da barra, ou *Ferramentas ▸ Opções…*, Ctrl+,) reúnem as preferências: tema, tamanho do texto
do editor, sugestões de links, tipos de link, IA, servidor MCP, Anki, Zotero, integração com o Windows e backups.

O aplicativo segue a configuração **claro/escuro** e a **cor de destaque** do seu Windows. Você pode forçar um tema em
*Exibir ▸ Tema*.

## Atualizações

Cerca de quatro segundos depois de iniciar, o ZettelApp faz uma requisição HTTPS para
`https://dutrairs.github.io/ZettelApp/version.json` para saber a versão mais recente. Ele não envia mais nada
(apenas um user-agent `ZettelApp/<version>`), e se a requisição falhar você não verá nada. Quando existe uma versão
mais nova, um pequeno aviso aparece no canto inferior direito, no máximo uma vez por versão. Ele nunca
rouba o foco. **Baixar** abre a página de versões no navegador, **✕** fecha o aviso e
**Não verificar atualizações** desativa a verificação. Você pode reativá-la em
*Ferramentas ▸ Opções ▸ Geral ▸ Verificar atualizações quando o ZettelApp iniciar*. O ZettelApp nunca instala
nada por conta própria.

## Desinstalação

Use *Configurações do Windows ▸ Aplicativos ▸ Aplicativos instalados ▸ ZettelApp ▸ Desinstalar*. Depois que você confirmar, uma caixa de diálogo oferece
uma opção desmarcada **Excluir também minhas configurações e dados do ZettelApp**. Ela remove suas configurações, chaves de API
salvas, logs, cache e backups automáticos (`%LOCALAPPDATA%\ZettelApp`) **e todas as suas notas** (o banco de dados
e os anexos dos seus cofres). Deixe-a desmarcada para manter suas notas. Na versão portátil, exclua a pasta dela.

## Próximos passos

- Aprenda a sintaxe das notas em [Notas e links](notes-and-links.md).
- Leia como funcionam as [sugestões de links](link-suggestions.md).
- Pressione **F1** a qualquer momento para abrir esta documentação, ou veja os [atalhos de teclado](keyboard-shortcuts.md).
