#!/usr/bin/env python3
"""把 build/text.json 生成原文页面（明文，放在 build/site-text/，不进仓库），
并写出公开的篇目清单 content/text_index.json。
之后用 tools/encrypt_text.sh 加密到 text/。"""
import html, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build as B

def main():
    data = json.load(open(os.path.join(ROOT, 'build', 'text.json'), encoding='utf-8'))
    arts = B.load_articles()
    by_title = {a['title']: a['no'] for a in arts}
    outdir = os.path.join(ROOT, 'build', 'site-text')
    os.makedirs(outdir, exist_ok=True)
    manifest = []
    for i, x in enumerate(data, 1):
        f = f'{i:03d}.html'
        v1 = by_title.get(x['title'])
        manifest.append({'file': f, 'vol': x['vol'], 'title': x['title'], 'date': x['date'], 'v1': v1,
                         'chars': len(''.join(x['paras']))})
        root = '../'
        back = (f'<a class="btn-link" href="{root}v1/{v1:02d}.html">← 看这篇的注解和深读</a>' if v1 else '')
        head = (f'<div class="notice"><div><b>题解。</b>{B.esc(x["headnote"])}</div></div>' if x['headnote'] else '')
        paras = ''.join(f'<p>{B.esc(p)}</p>' for p in x['paras'])
        notes = ''.join(f'<li>{B.esc(n)}</li>' for n in x['notes'])
        notes_html = f'<h2 class="vh">原书注释</h2><ol class="srcnotes">{notes}</ol>' if notes else ''
        prev_ = f'<a href="{i-1:03d}.html">← 上一篇</a>' if i > 1 else '<span></span>'
        next_ = f'<a href="{i+1:03d}.html">下一篇 →</a>' if i < len(data) else '<span></span>'
        page = (B.head(f'{x["title"]} · 原文 · 毛选读注', root) + B.topbar(root, 'text') +
                f'<div class="shell wide"><main><div class="eyebrow">原文 · {"第五卷" if x["vol"]=="5" else "一至四卷"}</div>'
                f'<h1>{B.esc(x["title"])}</h1><p class="date">（{B.esc(x["date"])}）</p>{back}{head}'
                f'<article class="srctext">{paras}</article>{notes_html}'
                f'<div class="pager">{prev_}<a href="index.html">原文目录</a>{next_}</div></main></div>\n' + B.foot(root))
        open(os.path.join(outdir, f), 'w', encoding='utf-8').write(page)
    json.dump(manifest, open(os.path.join(ROOT, 'content', 'text_index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(manifest)} 篇原文页面 → build/site-text/，清单 → content/text_index.json')

if __name__ == '__main__':
    main()
