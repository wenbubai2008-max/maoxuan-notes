# 毛选读注

《毛泽东选集》五卷逐篇注解与深读。私密仓库，个人学习用。

## 现在有什么

- `index.html`：样章网站，单文件，双击即可在浏览器打开。
  - 第一卷第 1 篇《中国社会各阶级的分析》：段落提要 + 18 条注解、深读、题解、版本变化、管理视角
  - 总论页「思维方法」：顶部导航进入，或在地址后加 `#method`
- `tools/split_corpus.py`：把本地 PDF 切成单篇 JSON，供写注解时参考。

## 原文放哪里

原文 PDF 放在 `source/`（已被 `.gitignore` 排除，不会上传）。切分结果输出到 `build/`，同样不上传。

```bash
python3 tools/split_corpus.py --vol14 source/一卷本.pdf --vol5 source/第五卷.pdf --out build/corpus.json
```

正文计划在 **2027 年 1 月 1 日** 之后导入网站，在那之前仓库里不放原文。

## 怎么看网页

- 本地：直接打开 `index.html`。
- GitHub Pages：私密仓库需要付费账户（Pro 及以上）才能开启，而且开启后网站本身是**公开**的，任何人有链接都能看。所以默认不开启。
