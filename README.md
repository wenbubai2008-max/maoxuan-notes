# 毛选读注

《毛泽东选集》五卷逐篇注解与深读。网站：https://wenbubai2008-max.github.io/maoxuan-notes/

## 结构

```
index.html            首页（由 build.py 生成）
compare.html          原文对照阅读（第一卷原文在线；也可选本地 PDF）
originals/v1/NN.html  第一卷各篇原文文字稿（由1967年PDF提取）
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

公开站点已提供 `compare.html`：第一卷17篇的1967年版文字原文已发布在 `originals/v1/`，可直接左原文右注解阅读；如需核对扫描影印版，可选择本地 PDF，文件仍只在浏览器本地加载。1977年第五卷目前仍须选择本地 PDF 阅读，逐篇分析尚待制作。

原文 PDF 放在 `source/`，切分结果在 `build/`，都不进仓库。第一卷原文文字已由上传的1967年一卷本提取并发布，存在自动提取误差；引用前应核对PDF扫描页。

```bash
python3 tools/split_corpus.py --vol14 source/一卷本.pdf --vol5 source/第五卷.pdf --out build/corpus.json
```
