# 读书 · 毛泽东选集

《毛泽东选集》五卷逐篇注解与深读。网站：https://wenbubai2008-max.github.io/reading/

## 结构

```
index.html            书架首页（生成，书目见 content/books.json）
maoxuan.html          《毛泽东选集》本书首页（生成）
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

- `text/NNN.html`：五卷原文，每篇一页，**已加密**。2026 年 12 月 31 日前打开时需要输入密码。
- `text/index.html`：原文目录（公开，只有标题）。
- `content/text_index.json`：原文篇目清单，`build.py` 用它生成目录和注解页上的“阅读原文”链接。
- 加密用的是 [StaticCrypt](https://github.com/robinmoisson/staticrypt)，盐值在 `.staticrypt.json`。仓库里只有加密后的文件，明文和 PDF 都不进仓库。

**2027 年 1 月 1 日自动公开**：工作流 `.github/workflows/unlock-text.yml` 会在北京时间 2027-01-01 00:05 自动解密全部原文页面并提交。前提是在仓库 Settings → Secrets and variables → Actions 里添加了名为 `MAOXUAN_PASSWORD` 的密钥。

重新生成原文页面（需要本地有 PDF）：

```bash
python3 tools/build_text.py --vol14 source/一卷本.pdf --vol5 source/第五卷.pdf --out build/text.json
python3 tools/make_text_site.py
MAOXUAN_PASSWORD=密码 bash tools/encrypt_text.sh
python3 tools/build.py
```
