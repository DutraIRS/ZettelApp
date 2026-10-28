# Zotero

ZettelApp 可连接免费的参考文献管理器 [Zotero](https://www.zotero.org/),让你能在笔记中引用参考文献,并撰写链接到文献库中条目及其 PDF 的**文献笔记**。

## 设置

1. 使用 **Zotero 7 或更高版本**并保持其运行。
2. 在 Zotero 中,打开 *Settings ▸ Advanced* 并开启 **"Allow other applications on this computer to communicate with Zotero"**。
3. 在 ZettelApp 中,*工具 ▸ 选项 ▸ Zotero ▸ 测试连接*应显示 *Connected to Zotero*。

ZettelApp 通过本机上 Zotero 的**本地 API**(`127.0.0.1`,默认端口 23119)读取你的文献库。它只读取:绝不会更改你的 Zotero 文献库,也不会有任何内容经由互联网传输。搜索的是你的个人文献库(*My Library*);暂不搜索群组文献库。

## 引用参考文献

*插入 ▸ Zotero 引用…*,或编辑器工具栏中的书本按钮,会打开一个搜索框。输入标题的一部分、作者或年份。搜索为空时,会列出你最近修改的条目。选择一个条目可查看其详情,然后:

- **插入引用**(或双击)会添加一条作者–年份引用,点击后在 Zotero 中打开该条目:

  ```markdown
  [Ebbinghaus (1885)](zotero://select/library/items/ABCD2345)
  ```

- **新建文献笔记**会为该条目创建一条笔记,包含:
  - 条目的标题;
  - 一行参考文献(作者、年份、标题、出版物、DOI);
  - 指向*在 Zotero 中打开*、*打开 PDF*(当条目有 PDF 附件时)和 DOI 的链接;
  - 摘要;
  - 供你填写的*关键想法*和*我的想法*小节;
  - 标签 `literature` 以及该条目的 Zotero 标签;
  - 以该 Zotero 条目作为笔记的**来源链接**。

文献笔记是 Zettelkasten 经典的桥梁,连接阅读与你自己的永久笔记:用你自己的话写下关键想法,然后把它们链接到它们所支持、扩展或反驳的笔记。

## Zotero 链接

点击笔记中的 Zotero 链接会在 Zotero 中打开该条目,或在 Zotero 的阅读器中打开 PDF。出于安全考虑,ZettelApp 只会跟随两种 Zotero 链接,并拒绝任何其他 `zotero://` 地址:

```text
zotero://select/library/items/<KEY>
zotero://open-pdf/library/items/<KEY>?page=<N>
```

群组文献库链接(`zotero://select/groups/<ID>/items/<KEY>`)也会被接受。你还可以把 Zotero 链接粘贴到笔记的**来源链接**字段中。在 Zotero 中,右键点击条目并复制其链接(或使用 Zutilo 这类插件),然后粘贴。

## 故障排除

| 消息 | 处理方法 |
|---|---|
| *Could not reach Zotero* | 启动 Zotero 7 或更高版本。检查*选项 ▸ Zotero* 中的端口(默认 23119)。 |
| *Zotero refused the request* | 开启 *Allow other applications…* 设置(上面的第 2 步)。 |
| *This Zotero version has no local API* | 将 Zotero 更新到 7 或更高版本。 |
