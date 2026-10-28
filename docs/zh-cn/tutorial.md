# 教程:你的前 30 分钟

一次动手实践的导览。每一步都会说明该做什么以及你应该看到什么。标有*可选*的步骤需要 Zotero、AI 密钥或 Anki;如果你不使用它们,可以跳过。

对这种方法本身还不了解?请先阅读[什么是 Zettelkasten?](what-is-zettelkasten.md),只需五分钟。

## 1. 安装并打开欢迎库

1. 从[最新版本](https://github.com/DutraIRS/ZettelApp/releases/latest)下载 **ZettelApp-Setup.exe** 并运行,或者解压 **ZettelApp-Portable.zip** 并运行 `ZettelApp.exe`。
2. 启动 ZettelApp。

**你应该看到**“笔记”页面,以及位于 *Documents\ZettelApp* 中新库里的十一条相互链接的入门笔记。“欢迎使用 ZettelApp”已在编辑器中打开。片刻之后,ZettelApp 还会提供可选的*档案馆的失踪王子*探险;如果你更喜欢这份文字导览,请选择**以后再说**。

## 2. 新建笔记

1. 按 **Ctrl+N**。
2. 输入标题,例如 *Spaced repetition*(间隔重复),然后按 **Enter** 移动到正文。
3. 用你自己的话写下一个想法,两三句即可:
   *以递增的间隔复习材料有助于长期记忆,因为每次复习都发生在即将遗忘之前。*

**你应该看到**这条笔记出现在列表顶部。这里没有“保存”按钮:笔记会在你输入时自动保存。标题下方的 ID(例如 `20261027153012`)就是这条笔记的永久地址。

## 3. 添加标签

点击标题下方的**添加标签**,输入 `learning`,然后按 **Enter**。再添加 `memory`。

**你应该看到**两个标签块,*#learning* 和 *#memory*。列表上方的标签筛选器现在会提供它们,在搜索框中输入 `tag:memory` 就能找到这条笔记。

## 4. 链接到另一条笔记

1. 新建第二条笔记(**Ctrl+N**),标题为 *Forgetting curve*(遗忘曲线),内容一句话:*除非复习信息,否则记忆会迅速消退。*
2. 回到 *Spaced repetition*(在列表中点击它)。在正文中输入 `[[`,然后输入 `Forg`。
3. 在补全列表中选择 **Forgetting curve**,然后按 **Enter**。

**你应该看到**正文中 `[[Forgetting curve]]` 带有下划线。在侧边栏的**链接**下会出现 *Forgetting curve*。点击工具栏中的眼睛按钮(**分屏**):预览中会显示一个可点击的链接。

## 5. 说明笔记之间*如何*关联

在链接前面加上 `supports::`,把它变成类型链接:

```markdown
supports:: [[Forgetting curve]]
```

**你应该看到**该链接在侧边栏中被列为*支持*。打开 *Forgetting curve*:它的**反向链接**显示为 *Spaced repetition:**支持者***,因为*支持*是一种有向链接类型。普通的 `[[links]]` 表示*相关于*。

## 6. 使用建议的链接

再写几条关于相关想法的笔记,例如 *Active recall* 和 *Interleaving*,每条写一两句话,并加上标签 `learning`。然后打开其中一条,查看侧边栏中的**链接建议**。

- 点击**链接**接受一条建议。旁边的小箭头可选择链接类型。
- 点击 **✕** 忽略不合适的建议。
- 将鼠标悬停在建议上,可查看它**为何**被建议:每项度量支持或反对的依据。

**模型学到了什么:**被接受的建议会变成链接,作为正例训练分类器。被忽略的建议会作为反例被记住,并且这一对笔记不会再被建议。你用得越多,建议就越准确。参见[链接建议](link-suggestions.md)。

![带有链接建议的笔记](../website/assets/screenshots/notes-light.png)

## 7. 添加图片

复制任意图片(例如使用 *Win+Shift+S*),在笔记正文中点击并按 **Ctrl+V**。你也可以拖入图片文件,或使用*插入 ▸ 图片…*。

**你应该看到**正文中出现 `![…](asset:…)`,预览中显示该图片。因为这是这条笔记的第一张图片,它同时会成为**笔记图片**,显示在标题旁边以及图谱中该笔记的圆圈内。

## 8. 绘制思维导图

1. 打开**思维导图**标签页,点击**添加想法**。
2. 按 **Tab** 添加子想法,按 **Enter** 添加同级想法,按 **F2** 重命名,按 **Del** 删除。方向键可在想法之间移动。
3. 现在点击**从链接生成**,并确认它可以替换你刚才绘制的导图。

**你应该看到**一张根据该笔记的链接生成的思维导图,按链接类型分组,每条被链接笔记自己的链接则深入一层。右键点击任意想法,可将它链接到某条笔记。导出按钮可保存为 PNG、SVG 或 FreeMind。

![思维导图](../website/assets/screenshots/mindmap-light.png)

## 9. 制作闪卡并复习

把这些行添加到 *Spaced repetition* 的正文中:

```markdown
Q: Why space reviews out?
A: Each effortful retrieval just before forgetting strengthens the memory.

{{c1::Hermann Ebbinghaus}} described the forgetting curve.
```

**你应该看到**标签页上显示**闪卡 (2)**:一张问答卡和一张填空卡。现在打开**复习**(**Ctrl+4**)并点击**开始复习**。

- 按 **Space** 显示答案。
- 用 **1–4** 给自己评分(*重来、困难、良好、简单*)。

SM-2 调度算法会决定每张卡片何时再次出现。也可以试试**练习测验 ▸ 选择题**或**为笔记命名**。

![选择题测验](../website/assets/screenshots/quiz-light.png)

## 10. 探索图谱

打开**图谱**(**Ctrl+2**)。

1. 拖动笔记,用滚轮缩放,将鼠标悬停在笔记上可高亮其相邻笔记。
2. 在“笔记”页面选中一条笔记,返回后点击 **Local**,然后把 **Depth** 改为 1、2 或 3。
3. 把 **Colour by** 设为 **Clusters: k-means**。笔记会按语义分组,图例用关键词为每个聚类命名。
4. 切换 **Group**,把每组笔记拉到一起,并显示在带阴影的背景上。
5. 点击 **3D**,拖动可环绕查看,并试试 **Rotate automatically**。

![按标签着色并分组的图谱](../website/assets/screenshots/graph-light.png)

## 11. 查看你的 Insights

打开 **Insights**(**Ctrl+3**),可查看数量、每月笔记数、热门标签、按类型的链接以及连接最多的笔记。**未链接的笔记**是你的待办清单:把它们链接到某处。每个图表都有表格视图。

## 12. 引用 Zotero 条目并撰写文献笔记(可选)

在 Zotero 7+ 运行,并且在其 *Settings ▸ Advanced* 中开启了 *Allow other applications on this computer to communicate with Zotero* 的情况下:

1. 选择*插入 ▸ Zotero 引用…*,搜索条目并点击**插入引用**:会生成类似 *Ebbinghaus (1885)* 的链接,点击后在 Zotero 中打开该条目。
2. 再做一次,这次点击**新建文献笔记**。

**你应该看到**一条新笔记,包含参考文献、*在 Zotero 中打开*和*打开 PDF* 链接、摘要,以及*关键想法* / *我的想法*两个小节,并带有标签 `literature`。参见 [Zotero](zotero.md)。

## 13. 询问你的笔记(可选)

1. 在*工具 ▸ 选项 ▸ AI 助手*中选择一个服务商(Anthropic、OpenAI 或 Z.ai),粘贴你的 API 密钥并点击**测试连接**。
2. 打开**提问**(**Ctrl+5**)并提问:*间隔和提取如何协同作用?*

**你应该看到**一个以链接形式引用你的笔记的回答,以及**已发送的来源**的准确列表。只有这些笔记和你的问题会离开你的电脑。参见[询问你的笔记](ai-assistant.md)。

## 14. 导出子图并同步到 Anki(可选)

1. 打开一条笔记,选择*文件 ▸ 导出…*(**Ctrl+Shift+E**),选择**当前笔记及其链接笔记**,深度 2,格式选**网站**。
2. 在浏览器中打开压缩包里的 `index.html`:这是你 Zettelkasten 中那一部分内容的小型网站。
3. 在 Anki 运行且已安装 AnkiConnect 插件(代码 `2055492159`)的情况下,打开**复习**并点击**同步到 Anki**。每张卡片的来源链接都会在 ZettelApp 中打开对应笔记。

参见[导出与导入](export-import.md)和 [Anki](review-and-anki.md#anki)。

## 15. 了解你的数据存放在哪里

- 你的笔记存放在库文件夹中(*文件 ▸ 在文件资源管理器中显示库*):`zettel.db` 加上 `assets`。
- 每天会自动备份一次,*文件 ▸ 立即备份库*可随时手动备份。
- 删除的笔记会进入笔记列表下方的**回收站**,你可以在那里还原它们。

详情参见[隐私与安全](privacy-and-security.md)。

**就是这些。**坚持每条笔记一个想法,带着原因链接每条新笔记,让建议和图谱向你展示你所拥有的一切。快捷键请见[键盘快捷键](keyboard-shortcuts.md)。
