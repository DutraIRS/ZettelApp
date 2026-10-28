# 常见问题

### ZettelApp 免费吗?

是的。它免费且开源,依据 [The Unlicense](https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE) 释放到公有领域。可选的 AI 功能使用你自己的 API 密钥,因此由服务商直接向你计费。

### 我如何支持 ZettelApp?

谢谢你的关心!你可以在 [Ko-fi](https://ko-fi.com/dutrairs) 上支持开发。企业可以赞助[路线图](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md)中的特定事项;请通过 [GitHub](https://github.com/DutraIRS/ZettelApp) 联系。赞助者会在发布说明中得到感谢。报告错误、改进文档以及分享 ZettelApp 同样有帮助。

### 它需要联网吗?

不需要。一切都可以离线使用。只有在启动时的一次小小的更新检查(你可以关闭它)、你在**提问**页面提出问题,以及你打开链接时,才会用到互联网。参见[隐私与安全](privacy-and-security.md)。

### ZettelApp 会检查更新吗?

会,在启动时检查一次:对项目网站上一个小文件发出一次请求,其中不包含任何关于你或你笔记的内容。如果存在更新的版本,右下角会出现通知。可通过*工具 ▸ 选项 ▸ 常规 ▸ ZettelApp 启动时检查更新*,或通知上的**不检查更新**将其关闭。参见[入门](getting-started.md#updates)。

### 状态栏中的 MCP 开关是什么?

它让 Claude Desktop 或 Claude Code 等 AI 助手通过 [MCP](mcp-server.md) 使用你的笔记。它在**每次 ZettelApp 启动时都是关闭的**。当它关闭或 ZettelApp 已关闭时,助手无法访问你的笔记。打开它之后,请在你的 MCP 客户端中重新连接 ZettelApp(或重启客户端)。

### 我可以使用自己电脑上的模型吗?

可以。在*工具 ▸ 选项 ▸ AI 助手*中,选择 **OpenAI** 并把**端点**设置为你的本地服务器,例如 `http://localhost:11434/v1`(Ollama)或 `http://localhost:1234/v1`(LM Studio)。`localhost` 不需要 API 密钥。参见[使用你自己的 LLM](ai-assistant.md#bring-your-own-llm)。

### 我的笔记在哪里?

在你的库文件夹中,默认位于 **Documents\ZettelApp**:一个 `zettel.db` 数据库和一个 `assets` 文件夹。*文件 ▸ 在文件资源管理器中显示库*会打开它。

### 我可以配合 OneDrive、Dropbox 或 Google Drive 使用吗?

可以。把库放在同步文件夹中(*文件 ▸ 新建库…*)。在另一台电脑上打开同一个库之前,请先在一台电脑上关闭 ZettelApp,因为两台电脑同时写入可能会产生冲突。

### 如何迁移到另一台电脑?

复制库文件夹,或使用*文件 ▸ 导出…* ▸ **ZettelApp 归档**,然后在另一台电脑上导入。

### 我可以使用我的 Obsidian 库吗?

可以。*文件 ▸ 导入 Markdown 文件夹…*会导入 Markdown 文件及其 front matter、`#tags`、`[[links]]` 和图片。你的 Obsidian 文件不会被更改。反过来,导出为 **Markdown 文件**,然后在 Obsidian 中打开该文件夹。

### 为什么会有像 20261027153012 这样的“Zettel” ID?

每条笔记都会根据其创建时间(年、月、日、时、分、秒)获得一个永久 ID。标题可以更改;ID 不会,因此按 ID 建立的链接绝不会失效。你很少需要看到它们。

### 正文中的链接和侧边栏中的链接有什么区别?

两者都是真正的链接。正文中的 `[[Links]]` 是你写作的一部分,把它们从正文中删除即可移除。通过**添加链接…**或接受建议而添加的链接不在正文中。你可以在侧边栏中更改它们的类型、反转它们的方向或移除它们。

### 为什么建议只显示“18% · 或许”?

这个数字是模型对你会链接这两条笔记的诚实估计。在新建或稀疏的库中,大多数笔记对都互不相关,因此即使是好的建议,起初也只有不高的数值。建议的顺序最重要,并且随着你链接和忽略,估计会不断改善。参见[链接建议](link-suggestions.md)。

### 它能在 macOS 或 Linux 上使用吗?

暂时不能。Linux 软件包(.deb、AppImage)和 macOS 已列入[路线图](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md)。

### 应用提供其他语言吗?

是的。安装程序和应用已翻译成西班牙语、葡萄牙语(巴西)、法语、德语、意大利语、俄语、简体中文、日语、韩语和阿拉伯语。应用默认跟随你的 Windows 语言;可在*选项*中更改。缺失的文字会回退到英文。

### 如何卸载?我的数据会怎样?

*设置 ▸ 应用 ▸ 已安装的应用 ▸ ZettelApp ▸ 卸载*。卸载程序提供一个未勾选的**同时删除我的 ZettelApp 设置和数据**选项,它会删除偏好设置、已保存的 API 密钥、日志、缓存和自动备份,**以及你的所有笔记**(库数据库和附件)。不勾选时,你的笔记会被保留。对于便携版,删除它的文件夹即可;它的偏好设置位于注册表中的 `HKEY_CURRENT_USER\Software\ZettelApp` 下,日志和备份位于 `%LOCALAPPDATA%\ZettelApp`。

### 出了问题。日志在哪里?

在 `%LOCALAPPDATA%\ZettelApp\Logs` 中。当你[报告问题](https://github.com/DutraIRS/ZettelApp/issues)时,请附上相关部分。请先检查其中不包含任何隐私内容。
