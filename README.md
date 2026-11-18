# 读书 · 毛泽东选集

《毛泽东选集》逐篇注解与《水浒传》金圣叹七十回本。网站：https://wenbubai2008-max.github.io/reading/

## 结构

```
index.html            书架首页（《毛泽东选集》和《水浒传》两本书，书目见 content/books.json）
maoxuan.html          《毛泽东选集》本书首页（生成）
shuihu.html           《水浒传》三个版本的选择页
shuihu-70.html        金圣叹七十回本独立目录
assets/shuihu-versions.css 三版本选择页样式
shuihu-read.html      《水浒传》简体原文与直接显示的金圣叹原批
assets/shuihu-jin.css 金圣叹版本专用样式
assets/shuihu-more.css 容与堂本与百二十回本专用样式
shuihu-100.html       容与堂百回本目录
shuihu-120.html       百二十回本目录
shuihu-other-read.html 两本新版本的独立正文阅读器
assets/shuihu-data.js 七十回目录和来源地址
assets/shuihu-commentary.js 原多版本研究存档（当前金圣叹阅读页不加载）
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

## 水浒传 · 金圣叹评七十回本

- 本书首页 `shuihu.html`：只显示这一版本的封面及楔子、七十回目录，不混入其他书籍与版本介绍。
- 阅读页 `shuihu-read.html?chapter=N`：直接显示简体原文和金圣叹总批、夹批；短批在原句后以赭金小字标出，长批紧接原句以赭金批注段落展开。不使用折叠按钮，也不需要点击才能看见。
- 正文缓存 `shuihu/text/000.json`—`070.json`：71份齐全，由维基文库七十回本转换为简体；每条金批和原文在数据层区分。
- 样式 `assets/shuihu-jin.css`。目录数据 `assets/shuihu-data.js`。
- 原文同步工具 `tools/fetch_shuihu.py`，离线旧格式修复 `tools/normalize_shuihu_cached.py`，工作流 `.github/workflows/shuihu-text.yml`。
- 如需容与堂百回本和袁无涯百二十回本，未来分别作为独立书籍建立，不能把不同底本的评语贴进金圣叹本中。
- 原文为公开文本经自动简繁转换而来，仍可能存在错字或断句偏差；正式引用应对照原本。

## 水浒传另外两个独立版本（2026-11-18）

- `shuihu-100.html`：容与堂百回本书籍首页、100回独立目录。简体正文存放在 `shuihu/100/text/001.json` 至 `100.json`。
- `shuihu-120.html`：百二十回本（袁无涯刊本系统）书籍首页、120回独立目录，另含田虎、王庆故事。简体正文存放在 `shuihu/120/text/001.json` 至 `120.json`。
- `shuihu-other-read.html?edition=100&chapter=N` 与 `?edition=120&chapter=N` 采用同一阅读引擎但严格按版读取独立目录和正文，字形经 OpenCC 转简体。
- `assets/shuihu-more-data.js`：各版来源说明及已撰写并明确署名为**本站读注**的少量随文点评；只按与相关正文匹配的关键词插入。不将金圣叹的批语复制给其他版本，也不伪称这些本站点评是李卓吾原批。
- `tools/fetch_shuihu_more.py`：从维基文库相应版本提取独立原文，`.github/workflows/shuihu-more.yml` 在 GitHub Actions 中执行，先提交起始几回，再逐步补齐余回；实际缓存量以各版本 `status.json` 为准。
- 两本明代评点本的完整历史眉批、夹批和总评并未保留在当前维基文库正文转录里，因此尚未上线为原批。若未来取得可核查的原批影印资料，应另行校勘、注明回页后才能插入。

## 书架导航

书架只显示《毛泽东选集》和《水浒传》两本书。点击《水浒传》进入 `shuihu.html` 选择金圣叹七十回本、容与堂百回本或袁无涯系百二十回本。各自目录分别是 `shuihu-70.html`、`shuihu-100.html`、`shuihu-120.html`；原文与批注数据不合并、不互换。七十回本阅读页 `shuihu-read.html` 返回到 `shuihu-70.html#chapters`。


## 水浒传页面排版与点评（2026-11-18 修订）

- 金圣叹七十回本：`shuihu-read.html` 不再把“金”字批注按钮塞在小说句子里。正文独立成段，当前段的金批在其下方以赭金色完整显示；同一段多则批语按顺序分列，保留原批内容及简短原文定位。
- 容与堂百回本：`shuihu-other-read.html?edition=100&chapter=N` 从对应底本中识别可查证的“李载贽曰”“李秃翁曰”“卓老曰”等附评，显示为青绿色的**底本附评**，只保留原文署名、不确定其真实作者。本站独立评论用紫色。
- 百二十回本：`?edition=120&chapter=N` 没有完整可核实的逐回历史批本电子标注。现在每回至少提供本站评析或回目导读，全部直接显示为紫色，不能称为袁无涯原批。
- `assets/shuihu-guides.js`：百回本100回和百二十回本120回均有阅读点评/导读，其中重点章节另有基于人物和事件的独立分析；有些其余回目只能先作为待深化的回目导读。
- `assets/shuihu-text-clean.js` 和 `tools/clean_shuihu_text.py`：仅删除小说结尾来自维基文库的版权模板和 `Public domain / falsefalse` 标志；小说正文、诗词、结尾及真实附评不删除。`.github/workflows/shuihu-cleanup.yml` 负责在仓库中批量清理此前缓存。


### 金圣叹七十回本 · 正文断行修复

- 原始文本的人工硬断行（如“东京大相国寺\\n住持”“背了包裹\\n、腰包”）已在 `tools/clean_shuihu_text.py` 中统一规范化，既有71篇缓存通过清理工作流重新生成。明确使用连续缩进排版的星宿名单、诗词、职务表仍保留分行。
- `shuihu-read.html`：短夹批继续在句中用赭金色显示；长批不再打断一句话或制造新的正文段落，而是在原始自然段末尾集中按出现顺序显示，并附原文定位。正文的自动换行仍由浏览器按屏幕宽度自然处理。
- 修改正文、批注或清理器时，应检查第四回“东京大相国寺住持 / 背了包裹、腰包”和第七十回星宿名册格式，且核对评点编号与正文占位符数量一致。
