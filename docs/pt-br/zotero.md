# Zotero

O ZettelApp se conecta ao [Zotero](https://www.zotero.org/), o gerenciador de referências gratuito, para que você possa citar
referências em suas notas e escrever **notas de literatura** ligadas ao item, e ao PDF dele, na sua biblioteca.

## Configuração

1. Use o **Zotero 7 ou posterior** e mantenha-o em execução.
2. No Zotero, abra *Configurações ▸ Avançado* e ative **"Permitir que outros aplicativos neste computador se
   comuniquem com o Zotero"**.
3. No ZettelApp, *Ferramentas ▸ Opções ▸ Zotero ▸ Testar conexão* deve dizer *Conectado ao Zotero*.

O ZettelApp lê sua biblioteca pela **API local** do Zotero neste computador (`127.0.0.1`, porta 23119 por
padrão). Ele só lê: nunca altera sua biblioteca do Zotero, e nada vai pela internet.
Sua biblioteca pessoal (*Minha biblioteca*) é pesquisada; as bibliotecas de grupo ainda não são.

## Citar uma referência

*Inserir ▸ Referência do Zotero…*, ou o botão de livros na barra de ferramentas do editor, abre uma caixa de busca. Digite parte de
um título, um autor ou um ano. Com a busca vazia, seus itens modificados mais recentemente são listados. Selecione
um item para ver seus detalhes e então:

- **Inserir citação** (ou clique duas vezes) adiciona uma citação autor–ano que abre o item no Zotero:

  ```markdown
  [Ebbinghaus (1885)](zotero://select/library/items/ABCD2345)
  ```

- **Nova nota de literatura** cria uma nota para o item, com:
  - o título do item;
  - uma linha de referência (autores, ano, título, publicação, DOI);
  - links para *Abrir no Zotero*, *Abrir PDF* (quando o item tem um anexo PDF) e para o DOI;
  - o resumo;
  - as seções *Ideias-chave* e *Meus pensamentos* para você preencher;
  - a tag `literature` mais as tags do item no Zotero;
  - o item do Zotero como **link de fonte** da nota.

As notas de literatura são a ponte clássica do Zettelkasten entre a leitura e suas próprias notas permanentes: escreva
as ideias-chave com suas palavras e depois ligue-as às notas que elas apoiam, estendem ou contradizem.

## Links do Zotero

Clicar em um link do Zotero em uma nota abre o Zotero no item, ou abre o PDF no leitor do Zotero. Por segurança,
o ZettelApp só segue dois tipos de link do Zotero e recusa qualquer outro endereço `zotero://`:

```text
zotero://select/library/items/<KEY>
zotero://open-pdf/library/items/<KEY>?page=<N>
```

Links de bibliotecas de grupo (`zotero://select/groups/<ID>/items/<KEY>`) também são aceitos. Você também pode colar um
link do Zotero no campo de **link de fonte** de uma nota. No Zotero, clique com o botão direito em um item e copie o link dele (ou use
um complemento como o Zutilo), depois cole-o.

## Solução de problemas

| Mensagem | O que fazer |
|---|---|
| *Could not reach Zotero* | Inicie o Zotero 7 ou posterior. Verifique a porta em *Opções ▸ Zotero* (padrão 23119). |
| *Zotero refused the request* | Ative a configuração *Permitir que outros aplicativos…* (passo 2 acima). |
| *This Zotero version has no local API* | Atualize o Zotero para a versão 7 ou posterior. |
