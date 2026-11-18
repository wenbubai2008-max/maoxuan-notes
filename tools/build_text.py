#!/usr/bin/env python3
"""从 PDF 提取原文，按篇、按段落整理，输出 build/text.json（不进仓库）。

用法：
  python3 tools/build_text.py --vol14 source/一卷本.pdf --vol5 source/第五卷.pdf --out build/text.json
依赖：pdftotext（poppler）
每篇：{vol, title, date, headnote, paras: [...], notes: [...]}
"""
import argparse, json, os, re, subprocess, sys

CJK = r'[　-〿一-鿿＀-￯“”‘’—…·]'
DATE = re.compile(r'^\s*[（(]\s*(一九[〇○零一二三四五六七八九十]{2}年[^）)]{0,40})[）)]\s*$')
MARK_ONLY = re.compile(r'^[\s〔〕\[\]０-９\d⑴-⒇（）()]+$')

def layout_lines(path):
    out = subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True, check=True).stdout
    return out.split('\n')

def clean(s):
    s = re.sub(r'(?<=%s)[ \t]+(?=%s)' % (CJK, CJK), '', s)
    s = re.sub(r'[ \t]+(?=[，。、；：？！”’）》])', '', s)
    return s.strip()

def ym(d):
    m = re.match(r'(一九[^年]+年[^月]*月)', d)
    return m.group(1) if m else d

def is_page_furniture(s, title):
    t = title.replace(' ', '')
    ss = s.replace(' ', '')
    return (re.fullmatch(r'\d+', ss) is not None or ss.startswith('毛泽东选集') or
            re.match(r'^\d+毛泽东选集', ss) is not None or ss == t or
            (ss.startswith(t[:6]) and re.search(r'\d+$', ss) is not None and len(ss) <= len(t) + 6) or
            re.fullmatch(r'目录\d*', ss) is not None)

def parse_article(lines, start, end, title):
    paras, head, notes, body = [], [], [], []
    mode, in_notes = 'body', False
    for raw in lines[start:end]:
        if not raw.strip():
            continue
        lead = len(raw) - len(raw.lstrip(' '))
        s = raw.strip()
        if re.fullmatch(r'注\s*释', s):
            in_notes = True; continue
        if in_notes:
            if re.match(r'^(〔\s*\d+\s*〕|\[\d+\])', s):
                notes.append(s)
            elif notes and not is_page_furniture(s, title):
                notes[-1] += s
            continue
        if is_page_furniture(s, title):
            if mode == 'head':
                mode = 'body'
            continue
        if MARK_ONLY.match(s) and lead >= 2:
            continue
        if s == '*':
            continue
        if s.startswith('*'):
            mode = 'head'; head.append(s.lstrip('*').strip()); continue
        if mode == 'head':
            if lead >= 4:
                head[-1] += s; continue
            mode = 'body'
        body.append(s)
        if lead == 2 or not paras:
            paras.append(s)
        else:
            paras[-1] += s
    if len(paras) <= 2 and sum(len(x) for x in body) > 800:
        # 这一篇原书没有段首缩进：按“短行 + 句末标点”推断段落
        lens = sorted(len(x) for x in body)
        med = lens[len(lens) // 2]
        paras, cur = [], ''
        for x in body:
            cur += x
            if len(x) < 0.8 * med and re.search(r'[。！？”：]$', x):
                paras.append(cur); cur = ''
        if cur:
            paras.append(cur)
    return clean(''.join(head)), [clean(p) for p in paras if clean(p)], [clean(n) for n in notes]

def split_vol14(L):
    first = next(i for i, l in enumerate(L) if i > 40 and DATE.match(l))
    toc_text = ''.join(l.strip() for l in L[:first])
    entries = []
    for m in re.finditer(r'([^\.\d…－—\s][^（\.…]{1,60}?)\s*（(一九[^）]{2,30})）', toc_text):
        t = re.sub(r'^[\d一二三四五六七八九十]*\s*', '', m.group(1)).strip()
        t = re.sub(r'^(毛泽东选集|目录\d*|第.次国内革命战争时期|抗日战争时期)', '', t.replace(' ', ''))
        t = re.sub(r'^.*(目录\d*|国内革命战争时期|抗日战争时期)', '', t)
        entries.append((t, m.group(2)))
    end_all = len(L)
    hits = [(i, DATE.match(l).group(1)) for i, l in enumerate(L) if i >= first - 2 and DATE.match(l)]
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
    # 附录之后不再有正文篇目
    out = []
    for n, (t, d, line) in enumerate(arts):
        end = arts[n + 1][2] - 3 if n + 1 < len(arts) else end_all
        head, paras, notes = parse_article(L, line + 1, end, t)
        out.append({'vol': '1-4', 'title': t, 'date': d, 'headnote': head, 'paras': paras, 'notes': notes})
    return out

def split_vol5(V):
    toc_start = next(i for i, l in enumerate(V) if re.sub(r'\s', '', l) == '目录')
    toc = [re.sub(r'\s*\.{2,}.*$', '', l).strip() for l in V[toc_start:toc_start + 200] if re.search(r'\.{4,}\s*\d+', l)]
    arts, start = [], toc_start + len(toc)
    for t in toc:
        key = t.replace(' ', '').replace('—', '-')
        hit = None
        for i in range(start, len(V)):
            if V[i].strip().replace(' ', '').replace('—', '-') != key:
                continue
            for j in range(i + 1, min(i + 10, len(V))):
                s = V[j].strip()
                if not s or s.replace(' ', '') == key:
                    continue
                if DATE.match(V[j]):
                    hit = (i, j, DATE.match(V[j]).group(1))
                break
            if hit:
                break
        if not hit:
            print('UNMATCHED 5:', t, file=sys.stderr); continue
        arts.append((t, hit[2], hit[1])); start = hit[1] + 1
    out = []
    for n, (t, d, line) in enumerate(arts):
        end = arts[n + 1][2] - 4 if n + 1 < len(arts) else len(V)
        head, paras, notes = parse_article(V, line + 1, end, t)
        out.append({'vol': '5', 'title': t, 'date': d, 'headnote': head, 'paras': paras, 'notes': notes})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vol14', required=True)
    ap.add_argument('--vol5', required=True)
    ap.add_argument('--out', default='build/text.json')
    a = ap.parse_args()
    data = split_vol14(layout_lines(a.vol14)) + split_vol5(layout_lines(a.vol5))
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    json.dump(data, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(data)} 篇，{sum(len("".join(x["paras"])) for x in data)} 字 → {a.out}')

if __name__ == '__main__':
    main()
