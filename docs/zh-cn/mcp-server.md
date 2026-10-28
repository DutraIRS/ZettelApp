# MCP 服务器

[Model Context Protocol](https://modelcontextprotocol.io/)(MCP)是一项开放标准,让 AI 助手可以使用其他程序提供的工具和数据。ZettelApp 内置了一个 MCP 服务器,因此 **Claude Desktop** 和 **Claude Code** 等助手可以在帮助你的同时搜索你的 Zettelkasten、读取笔记、跟随类型链接并请求链接建议。

## 它如何运行

该服务器是一个独立的小程序 **`zettelapp-mcp.exe`**,安装在 `ZettelApp.exe` 旁边。从源码运行时,同一个服务器通过 `python -m zettelapp.mcp_main` 运行。你的 MCP 客户端会在需要时启动它,并通过标准输入/输出与它通信。**不会打开任何网络端口。**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

如果没有 `--vault`,它会提供你上次在 ZettelApp 中打开的库。通过 MCP 所做的更改会在几秒钟内出现在应用中。

## MCP 开关

只有在 **ZettelApp 已打开且其状态栏中的 MCP 开关处于开启状态**时,MCP 客户端才能访问你的笔记。该开关在**每次 ZettelApp 启动时都是关闭的**,因此每次会话都由你决定助手是否可以读取你的笔记。把它关闭,或关闭 ZettelApp,服务器会在大约一秒内停止。没有该开关时,服务器会拒绝启动并说明原因。有关确切行为,请参见 [MCP API 参考](mcp-reference.md)。

## 连接 Claude Desktop

打开*工具 ▸ 选项 ▸ MCP 服务器*并点击**添加到 Claude Desktop…**。ZettelApp 会把自己添加到 `%APPDATA%\Claude\claude_desktop_config.json`(并保留旧文件的备份)。然后重启 Claude Desktop。请在启动 Claude Desktop 之前,先打开 ZettelApp 状态栏中的 **MCP 开关**;如果你稍后才打开它,请在 Claude Desktop 中重新连接 ZettelApp,或重启 Claude Desktop。要手动操作,请把该页面上显示的代码片段复制到该文件中。它看起来像这样:

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

## 连接 Claude Code

同一个“选项”页面会显示可复制的命令:

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

其他 MCP 客户端需要相同的命令和参数。与 Claude Desktop 一样,请先在 ZettelApp 中打开 MCP,如果之后才打开,请重新连接服务器(在 Claude Code 中使用 `/mcp`)。

## 工具

| 工具 | 作用 |
|---|---|
| `search_notes` | 对标题、正文和标签进行全文搜索(支持 `tag:name` 筛选)。空查询会列出最近编辑的笔记。 |
| `get_note` | 一条笔记的完整文本、标签、来源链接、日期、双向的类型链接、闪卡和思维导图大纲。 |
| `list_tags` | 所有标签,以及使用每个标签的笔记数量。 |
| `get_subgraph` | 与某条笔记相距 1–4 个链接以内的笔记,以及它们之间的类型链接(可选择只包含某些链接类型)。 |
| `suggest_links` | 很可能与某条笔记相关但尚未链接的笔记,按[朴素贝叶斯建议器](link-suggestions.md)排序。 |
| `list_link_types` | 库中的链接类型,例如*支持*、*与之矛盾*和*属于*。 |
| `create_note` | *(写入)* 创建一条笔记。正文中的 `[[Title]]` 会链接到已有笔记。 |
| `add_link` | *(写入)* 添加从一条笔记到另一条笔记的类型链接。 |

## 默认只读

服务器以**只读**方式打开你的库。只有当以下**两个**条件都成立时,才会提供这两个写入工具:

1. 在*选项 ▸ MCP 服务器*中勾选了**允许 MCP 客户端创建笔记和链接**;
2. 服务器是用 `--allow-writes` 启动的。勾选该选项后,“选项”页面上的代码片段会包含这个标志。

每次写入时都会重新检查该设置,因此取消勾选会立即生效。开启它则需要 MCP 客户端重启服务器。

笔记内容会作为数据传递给助手,服务器会告知助手不要把它们当作指令。输入会经过验证(ID、大小和限制),并且服务器绝不会触碰库以外的文件。

## 故障排除

- **客户端提示服务器启动失败,或工具调用提示开关已关闭。**打开 ZettelApp,并在其状态栏中开启 MCP,然后在客户端中重新连接服务器。
- **服务器仍然无法启动。**检查 `zettelapp-mcp.exe` 的路径是否正确。自己在终端中运行该命令:它会在标准错误输出中报告问题所在(例如“No ZettelApp vault found”)。
- **缺少写入工具。**勾选该选项*并*添加 `--allow-writes`,然后重启客户端。
