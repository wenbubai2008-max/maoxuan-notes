#!/usr/bin/env python3
"""把《毛泽东选集》PDF 切成单篇 JSON（仅本地使用，输出不进 git）。

用法：
  python3 tools/split_corpus.py --vol14 source/一卷本.pdf --vol5 source/第五卷.pdf --out build/corpus.json

依赖：poppler 的 pdftotext（macOS: brew install poppler；Ubuntu: apt install poppler-utils）
输出：[{vol, title, date, text}, ...]，text 为正文（已去掉文末注释和页眉页码）。
已知局限：少数篇目因排版问题对不上，会在 stderr 打印 UNMATCHED，需要人工补。
"""
import argparse, json, re, subprocess, sys

CJK = r'[　-〿一-鿿＀-￯“”‘’—…·]'
DATE = re.compile(r'^\s*[（(]\s*(一九[〇○零一二三四五六七八九十]{2}年[^）)]{0,40})[）)]\s*$')

def pdf_lines(path):
    out = subprocess.run(['pdftotext', path, '-'], capture_output=True, text=True, check=True).stdout
    return out.split('\n')

def clean(s):
    return re.sub(r'(?<=%s)[ \t]+(?=%s)' % (CJK, CJK), '', s)

def ym(d):
    m = re.match(r'(一九[^年]+年[^月]*月)', d)
    return m.group(1) if m else d

def body(lines, s, e):
    txt = []
    for l in lines[s:e]:
        st = l.strip()
        if re.match(r'^(〔1〕|\[1\])', st) and len(txt) > 3:
            break  # 文末注释开始
        if len(st) < 40 and re.fullmatch(r'\d+|毛\s*泽\s*东\s*选\s*集.*', st):
            continue  # 页码、页眉
        txt.append(st)
    return clean(''.join(txt))

def split_vol14(L):
    # 目录在正文第一篇之前；用“标题（日期）”匹配目录项，再按日期顺序对齐正文
    first = next(i for i, l in enumerate(L) if i > 40 and DATE.match(l))
    toc_text = ''.join(l.strip() for l in L[:first])
    entries = []
    for m in re.finditer(r'([^\.\d…－—\s][^（\.…]{1,60}?)\s*（(一九[^）]{2,30})）', toc_text):
        t = re.sub(r'^[\d一二三四五六七八九十]*\s*', '', m.group(1)).strip()
        t = re.sub(r'^(毛泽东选集|目录\d*|第.次国内革命战争时期|抗日战争时期)', '', t.replace(' ', ''))
        entries.append((t, m.group(2)))
    vol5_start = next((i for i, l in enumerate(L) if '第五卷' in l and '出版说明' in ''.join(L[i:i+5])), len(L))
    hits = [(i, DATE.match(l).group(1)) for i, l in enumerate(L) if first - 2 <= i < vol5_start and DATE.match(l)]
    arts, k = [], 0
    for t, d in entries:
        found = None
        for kk in range(k, min(k + 12, len(hits))):
            h = hits[kk][1]
            if h.startswith(d) or d.startswith(h) or ym(h) == ym(d):
                found = kk; break
        if found is None:
            print('UNMATCHED 1-4:', t, d, file=sys.stderr); continue
        arts.append((t, d, hits[found][0])); k = found + 1
    out = []
    for n, (t, d, line) in enumerate(arts):
        end = arts[n + 1][2] if n + 1 < len(arts) else vol5_start
        out.append({'vol': '1-4', 'title': t, 'date': d, 'text': body(L, line + 1, end)})
    return out

def split_vol5(V):
    toc_start = next(i for i, l in enumerate(V) if re.sub(r'\s', '', l) == '目录')
    toc = [re.sub(r'\s*\.{2,}.*$', '', l).strip() for l in V[toc_start:toc_start + 120] if re.search(r'\.{4,}\s*\d+', l)]
    arts, start = [], toc_start + len(toc)
    for t in toc:
        key = t.replace(' ', '').replace('—', '-')
        for i in range(start, len(V) - 3):
            if V[i].strip().replace(' ', '').replace('—', '-') == key:
                ds = [DATE.match(V[i + j]) for j in (1, 2, 3)]
                ds = [m for m in ds if m]
                if ds:
                    arts.append((t, ds[0].group(1), i)); start = i + 1; break
        else:
            print('UNMATCHED 5:', t, file=sys.stderr)
    out = []
    for n, (t, d, line) in enumerate(arts):
        end = arts[n + 1][2] if n + 1 < len(arts) else len(V)
        out.append({'vol': '5', 'title': t, 'date': d, 'text': body(V, line + 1, end)})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vol14', required=True, help='一至四卷（一卷本）PDF')
    ap.add_argument('--vol5', required=True, help='第五卷 PDF')
    ap.add_argument('--out', default='build/corpus.json')
    a = ap.parse_args()
    corpus = split_vol14(pdf_lines(a.vol14)) + split_vol5(pdf_lines(a.vol5))
    import os; os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    json.dump(corpus, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(corpus)} 篇，{sum(len(c["text"]) for c in corpus)} 字 → {a.out}')

if __name__ == '__main__':
    main()
