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
    by_title = {a['title']: a['no'] for a in B.load_articles('1')}
    by_title5 = {a['title']: a['no'] for a in B.load_articles('5')}
    have = {v: {a['no'] for a in B.load_articles(str(v))} for v in (2, 3, 4)}
    n5 = 0
    # 一至四卷按各卷第一篇切分
    firsts = {'反对日本进攻的方针、办法和前途': 2, '《农村调查》的序言和跋': 3, '抗日战争胜利后的时局和我们的方针': 4}
    volno, seqs = 1, {}
    outdir = os.path.join(ROOT, 'build', 'site-text')
    os.makedirs(outdir, exist_ok=True)
    manifest = []
    for i, x in enumerate(data, 1):
        f = f'{i:03d}.html'
        v1 = by_title.get(x['title']) if x['vol'] != '5' else None
        v5 = by_title5.get(x['title']) if x['vol'] == '5' else None
        rec = {'file': f, 'vol': x['vol'], 'title': x['title'], 'date': x['date'], 'v1': v1,
               'chars': len(''.join(x['paras']))}
        if x['vol'] == '5':
            n5 += 1; rec['v5no'] = n5; rec['v5'] = v5; rec['volno'] = 5; rec['seq'] = n5
        else:
            volno = firsts.get(x['title'], volno)
            seqs[volno] = seqs.get(volno, 0) + 1
            rec['volno'] = volno; rec['seq'] = seqs[volno]
            if volno in have and seqs[volno] in have[volno]:
                rec[f'v{volno}'] = seqs[volno]
        manifest.append(rec)
        root = '../'
        back = (f'<a class="btn-link" href="{root}v1/{v1:02d}.html">← 看这篇的注解和深读</a>' if v1 else
                f'<a class="btn-link" href="{root}v5/{v5:02d}.html">← 看这篇的注解和分析</a>' if v5 else
                next((f'<a class="btn-link" href="{root}v{v}/{rec["v" + str(v)]:02d}.html">← 看这篇的注解和分析</a>' for v in (2, 3, 4) if rec.get(f'v{v}')), ''))
        head = (f'<div class="notice"><div><b>题解。</b>{B.esc(x["headnote"])}</div></div>' if x['headnote'] else '')
        paras = ''.join(f'<p>{B.esc(p)}</p>' for p in x['paras'])
        notes = ''.join(f'<li>{B.esc(n)}</li>' for n in x['notes'])
        notes_html = f'<h2 class="vh">原书注释</h2><ol class="srcnotes">{notes}</ol>' if notes else ''
        prev_ = f'<a href="{i-1:03d}.html">← 上一篇</a>' if i > 1 else '<span></span>'
        next_ = f'<a href="{i+1:03d}.html">下一篇 →</a>' if i < len(data) else '<span></span>'
        page = (B.head(f'{x["title"]} · 原文 · 毛选 · 读书', root) + B.topbar(root, 'text') +
                f'<div class="shell wide"><main><div class="eyebrow">原文 · 第{"一二三四五"[rec["volno"] - 1]}卷 · 第 {rec["seq"]} 篇</div>'
                f'<h1>{B.esc(x["title"])}</h1><p class="date">（{B.esc(x["date"])}）</p>{back}{head}'
                f'<article class="srctext">{paras}</article>{notes_html}'
                f'<div class="pager">{prev_}<a href="index.html">原文目录</a>{next_}</div></main></div>\n' + B.foot(root))
        open(os.path.join(outdir, f), 'w', encoding='utf-8').write(page)
    json.dump(manifest, open(os.path.join(ROOT, 'content', 'text_index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(manifest)} 篇原文页面 → build/site-text/，清单 → content/text_index.json')

if __name__ == '__main__':
    main()
