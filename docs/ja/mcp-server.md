# MCP サーバー

[Model Context Protocol](https://modelcontextprotocol.io/) (MCP) は、AI アシスタントが他のプログラムのツールやデータを使えるようにするオープンな標準です。ZettelApp には MCP サーバーが含まれているので、**Claude Desktop** や **Claude Code** などのアシスタントが、あなたを手助けしながら、Zettelkasten の検索、ノートの読み取り、種類付きリンクの追跡、リンク候補の取得を行えます。

## 実行のしくみ

サーバーは別の小さなプログラム **`zettelapp-mcp.exe`** で、`ZettelApp.exe` と同じ場所にインストールされます。ソースから実行する場合は、同じサーバーを `python -m zettelapp.mcp_main` で起動します。MCP クライアントが必要に応じてこれを起動し、標準入出力を通じて通信します。**ネットワークポートは開かれません。**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

`--vault` を指定しない場合は、ZettelApp で最後に開いた保管庫を提供します。MCP 経由で行った変更は、数秒以内にアプリに反映されます。

## MCP スイッチ

MCP クライアントがノートにアクセスできるのは、**ZettelApp が開いていて、ステータスバーの MCP スイッチがオン**の間だけです。スイッチは **ZettelApp を起動するたびにオフ**になるので、アシスタントにノートを読ませるかどうかを、セッションごとにあなたが決められます。スイッチをオフにするか ZettelApp を閉じると、サーバーは約 1 秒以内に停止します。スイッチがオンでないと、サーバーは起動を拒否し、その理由を伝えます。正確な動作については [MCP API リファレンス](mcp-reference.md)を参照してください。

## Claude Desktop に接続する

*ツール ▸ オプション ▸ MCP サーバー*を開き、**Claude Desktop に追加…**をクリックします。ZettelApp は `%APPDATA%\Claude\claude_desktop_config.json` に自身を追加します (古いファイルのバックアップは残されます)。その後、Claude Desktop を再起動します。Claude Desktop を起動する前に、ZettelApp のステータスバーの **MCP スイッチ**をオンにしてください。後からオンにした場合は、Claude Desktop で ZettelApp に再接続するか、Claude Desktop を再起動します。手動で行う場合は、そのページに表示されているスニペットをファイルにコピーします。次のような内容です。

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

## Claude Code に接続する

同じオプションページに、コピーするコマンドが表示されます。

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

他の MCP クライアントにも、同じコマンドと引数が必要です。Claude Desktop と同様に、まず ZettelApp で MCP をオンにし、後からオンにした場合はサーバーに再接続します (Claude Code では `/mcp`)。

## ツール

| ツール | 内容 |
|---|---|
| `search_notes` | タイトル、本文、タグの全文検索 (`tag:name` フィルターも使えます)。クエリが空の場合は、最近編集したノートを一覧表示します。 |
| `get_note` | ノートの全文、タグ、情報源リンク、日付、双方向の種類付きリンク、フラッシュカード、マインドマップの概要。 |
| `list_tags` | すべてのタグと、それぞれを使っているノートの数。 |
| `get_subgraph` | ノートから 1〜4 リンク以内のノートと、それらの間の種類付きリンク (一部のリンクの種類のみに絞ることも可能)。 |
| `suggest_links` | ノートに関連がありそうだがまだリンクされていないノートを、[ナイーブベイズによる提案](link-suggestions.md)で順位付けしたもの。 |
| `list_link_types` | *supports*、*contradicts*、*part of* など、保管庫にあるリンクの種類。 |
| `create_note` | *(書き込み)* ノートを作成します。本文中の `[[Title]]` は既存のノートにリンクされます。 |
| `add_link` | *(書き込み)* あるノートから別のノートへ、種類付きリンクを追加します。 |

## 既定では読み取り専用

サーバーは保管庫を**読み取り専用**で開きます。2 つの書き込みツールが提供されるのは、次の**両方**が満たされたときだけです。

1. *オプション ▸ MCP サーバー*で**MCP クライアントによるノートとリンクの作成を許可**にチェックが入っている。
2. サーバーが `--allow-writes` で起動されている。オプションにチェックを入れると、オプションページのスニペットにこのフラグが含まれます。

この設定は書き込みのたびに再確認されるので、チェックを外すとすぐに反映されます。オンにする場合は、MCP クライアントがサーバーを再起動する必要があります。

ノートの内容は、データとしてアシスタントに渡され、サーバーはアシスタントに、それを指示として扱わないよう伝えます。入力 (ID、サイズ、上限) は検証され、サーバーが保管庫の外のファイルに触れることはありません。

## トラブルシューティング

- **クライアントがサーバーの起動に失敗したと表示する、またはツール呼び出しがスイッチはオフだと答える。** ZettelApp を開いてステータスバーで MCP をオンにし、クライアントでサーバーに再接続してください。
- **それでもサーバーが起動しない。** `zettelapp-mcp.exe` へのパスが正しいか確認してください。ターミナルでコマンドを自分で実行すると、何が問題か (たとえば「No ZettelApp vault found」) が標準エラーに出力されます。
- **書き込みツールが表示されない。** オプションにチェックを入れ、*かつ* `--allow-writes` を追加してから、クライアントを再起動してください。
