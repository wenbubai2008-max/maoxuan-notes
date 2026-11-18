# 毛选读注

《毛泽东选集》五卷逐篇注解与深读。网站：https://wenbubai2008-max.github.io/maoxuan-notes/

## 结构

```
index.html            首页（由 build.py 生成）
compare.html          原文对照阅读（仅本地选取 PDF，不托管原文）
method.html           总论：思维方法（生成）
v1/NN.html            第一卷各篇（生成）
assets/site.css/.js   共享样式和脚本
content/vol1/NN.json  每篇的内容：背景、分节提要、注解、方法、应用、争议
content/method.html   总论正文；[[v1-NN]] 会自动变成篇目链接
content/_v1-01-*.html 第 1 篇的附加栏目（深读、版本变化、管理视角）
tools/build.py        生成网站：python3 tools/build.py
tools/split_corpus.py 把本地 PDF 切成单篇 JSON
```

**改内容只改 `content/`，不要直接改生成的 HTML。**

在 GitHub 网页上改完 `content/` 里的文件并提交后，Actions 会自动运行 `tools/build.py` 重新生成网页（约 1–2 分钟），再由 Pages 发布。在本地改的话，运行 `python3 tools/build.py` 后一起提交。

## 每篇 JSON 的字段

- `no` `title` `date` `period`：篇号、标题、题注日期、时期
- `meta`：页首信息格 `[["标签","内容"], ...]`
- `gist`：一句话主旨
- `methods`：对应总论的方法编号，如 `["m04","m10"]`
- `method_note` `use` `debate`：方法说明、今天怎么用、争议与局限
- `background`：题解与背景段落（或 `background_html` 指向文件）
- `sections`：分节，每节 `h` 标题、`sum` 提要、可选 `quote`、`notes` 注解列表
  - 注解：`term` 词条、`kind` 类别、`text` 内容、可选 `anchor`（在提要中标记的文字）
- `extra_tabs`：可选的附加栏目

## 原文

公开站点已提供 `compare.html`：选择本地 1967 年一卷本 PDF 后，可按第一卷 17 篇直接跳到对应原文页，右侧显示本站逐篇分析。1977 年第五卷可按书内印页翻阅；逐篇分析尚待制作。PDF 只在浏览器本地加载，不进入仓库或服务器，刷新后需要重新选择文件。

原文 PDF 放在 `source/`，切分结果在 `build/`，都不进仓库。正文计划在 **2027 年 1 月 1 日** 之后导入网站。

```bash
python3 tools/split_corpus.py --vol14 source/一卷本.pdf --vol5 source/第五卷.pdf --out build/corpus.json
```
