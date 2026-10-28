# ZettelApp 文档

ZettelApp 是一款适用于 Windows 的 Zettelkasten 应用:由许多小笔记组成的网络,每条笔记只包含一个想法,并通过能说明想法之间*如何*关联的链接相互连接。它会在你写作时建议链接,把你的知识绘制成 2D 或 3D 图谱,把笔记变成闪卡和测验,并可与 Anki、Zotero 和 AI 助手配合使用。

除非你主动使用需要联网的功能,否则一切内容都保存在你的电脑上。

## 初次使用?

- **[什么是 Zettelkasten?](what-is-zettelkasten.md)**:这种方法是什么、它的由来,以及 ZettelApp 如何支持它。
- **[教程:你的前 30 分钟](tutorial.md)**:动手实践的导览,从第一条笔记一直到 3D 图谱。

## 目录

- [入门](getting-started.md):安装、你的第一个库,以及窗口导览
- [笔记与链接](notes-and-links.md):Markdown、维基链接、类型链接与有向链接、标签、图片、思维导图、闪卡、搜索和回收站
- [链接建议](link-suggestions.md):朴素贝叶斯建议器的工作原理以及如何调整
- [图谱与 Insights](graph-and-insights.md):2D 和 3D 图谱、聚类、分组和图表
- [复习、测验与 Anki](review-and-anki.md):间隔重复、测验模式、Anki 同步和牌组
- [Zotero](zotero.md):引用参考文献并撰写文献笔记
- [询问你的笔记(AI)](ai-assistant.md):来自 Claude、OpenAI 或 Z.ai、以你的笔记为依据的回答
- [MCP 服务器](mcp-server.md):让 Claude Desktop、Claude Code 和其他 MCP 客户端读取你的库
- [MCP API 参考](mcp-reference.md):协议、工具和错误,供构建 MCP 客户端的人使用
- [导出与导入](export-import.md):整个集合或任意子图,支持七种格式
- [键盘快捷键](keyboard-shortcuts.md)
- [隐私与安全](privacy-and-security.md):哪些内容会离开你的电脑、数据存放在哪里,以及 ZettelApp 如何保护数据
- [开发](development.md):从源码构建、运行测试、打包发布版本
- [常见问题](faq.md)

## 背后的理念

**Zettelkasten**(“卡片盒”)是一种因社会学家尼克拉斯·卢曼(Niklas Luhmann)而广为人知的笔记方法。每条笔记都是*原子化*的(一个想法,用你自己的话写成),并带有永久 ID。价值来自连接:当你把新笔记链接到已有笔记时,你不得不思考想法之间如何关联,之后还可以顺着这些链接发现意想不到的组合。

ZettelApp 保留了这种严谨,同时去掉了摩擦:

- **ID 自动生成**:每条笔记都会得到一个时间戳 ID,例如 `20261027153012`。
- **链接可以说明笔记之间的关系**:*支持*、*与之矛盾*、*扩展*、*示例*、*属于*、*引用*,或你自己的链接类型。
- **建议会呈现你遗漏的连接**:分类器会把一条笔记与库中的其余笔记比较,并从你接受和忽略的链接中学习。
- **复习内置其中**:笔记可以变成闪卡和测验,使用间隔重复或 Anki。
