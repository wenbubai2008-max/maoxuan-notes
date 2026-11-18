#!/usr/bin/env python3
"""从 PDF 提取原文，按篇、按段落整理，输出 build/text.json（不进仓库）。

用法：
  python3 tools/build_text.py --vol14 source/一卷本.pdf --vol5 source/第五卷.pdf --out build/text.json
依赖：pdftotext（poppler）
每篇：{vol, title, date, headnote, paras: [...], notes: [...]}
"""
import argparse, json, os, re, subprocess, sys

CJK = r'[　-〿一-鿿＀-￯“”‘’—…·]'
DATE = re.compile(r'^\s*[（(]\s*(一九[〇○零0-9一二三四五六七八九十 ]{2,6}年[^）)]{0,40})[）)]?\s*$')
DATE5 = re.compile(r'^\s*[（(]?\s*(一九[〇○零0-9一二三四五六七八九十 ]{2,6}年[^）)]{0,40})[）)]?\s*$')
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

def parse_article(lines, start, end, title, head_flush=False):
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
        if s.startswith('（《毛泽东选集》') or re.fullmatch(r'-{5,}.*', s):
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
            if lead >= 4 or (head_flush and lead == 0):
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
                if len(s) <= 40 and DATE5.match(V[j]):
                    hit = (i, j, DATE5.match(V[j]).group(1))
                break
            if hit:
                break
        if not hit:
            print('UNMATCHED 5:', t, file=sys.stderr); continue
        top = hit[0]
        for k in range(hit[0] - 1, max(hit[0] - 10, 0), -1):
            if V[k].strip().replace(' ', '').replace('—', '-') == key:
                top = k
        arts.append((t, hit[2], hit[1], top)); start = hit[1] + 1
    out = []
    for n, (t, d, line, _title_line) in enumerate(arts):
        end = arts[n + 1][3] if n + 1 < len(arts) else len(V)
        head, paras, notes = parse_article(V, line + 1, end, t, head_flush=True)
        d = d.replace(' ', '').replace('0', '〇')
        t = {'坚持艰苦奋共，密切联系群众': '坚持艰苦奋斗，密切联系群众', '我们党的—些历史经验': '我们党的一些历史经验'}.get(t, t)
        out.append({'vol': '5', 'title': t, 'date': d, 'headnote': head, 'paras': paras, 'notes': notes})
    return out

def split_vol24(path):
    """第二至四卷：按目录页码切分，标题和日期取正文首页，页中间开始的短文另行切出。"""
    txt=subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True, check=True).stdout; pages=txt.split('\f')
    num=[None]*len(pages)
    for i,pg in enumerate(pages):
        ls=[l.strip() for l in pg.split('\n') if l.strip()]
        for l in ls[:2]+ls[-2:]:
            m=re.match(r'^(\d{1,4})\s+毛泽东选集',l) or re.search(r'\S\s+(\d{1,4})$',l) or re.fullmatch(r'(\d{1,4})',l)
            if m: num[i]=int(m.group(1)); break
    # 页码：用相邻页的“PDF 页序 - 书页码”中位数纠正个别误读
    cand = [(i, n) for i, n in enumerate(num) if n is not None and i > 40]
    num = [None] * len(pages)
    for i in range(len(pages)):
        near = sorted(ii - n for ii, n in cand if abs(ii - i) <= 10)
        if near:
            num[i] = i - near[len(near) // 2]
    b2p = {}
    for i, n in enumerate(num):
        if n is not None and n not in b2p and i > 40:
            b2p[n] = i
    DATE=re.compile(r'^\s*[（(]\s*(一九[〇○零0-9一二三四五六七八九十 ]{2,6}年[^）)]{0,40})[）)]?\s*$')
    SKIP = ('跋', '结论', '引言', '序', '序言')
    def starts_here(pg):
        ne = [l for l in pg.split('\n') if l.strip()]
        for j, l in enumerate(ne[:7]):
            pl = ne[j-1] if j >= 1 else ''
            if (DATE.match(l) and len(l.strip()) <= 30 and j >= 1 and len(pl) - len(pl.lstrip()) >= 2
                    and len(pl.strip()) <= 34 and not re.search(r'[。，；：]$', pl.strip())):
                t = re.sub(r'[*＊⑴-⒇\s]', '', pl)
                return not (t in SKIP or t.startswith('发言人') or t.startswith('中国共产党中央革命军事委员会'))
        return False
    L=txt.split('\n'); endt=next(i for i,l in enumerate(L) if '唯心历史观的破产' in l)
    tocs = sorted({int(m.group(1)) for l in L[20:endt+1] for m in [re.search(r'\.{3,}\s*(\d+)\s*[－-]\s*\d*\s*$',l.strip())] if m})
    startp = set()
    for sbk in tocs:
        if sbk < 315 or sbk not in b2p: continue
        p0 = b2p[sbk]
        for d in (0, 1, -1, 2, -2, 3, -3):
            q = p0 + d
            if 0 <= q < len(pages) and any(DATE.match(l) for l in [x for x in pages[q].split('\n') if x.strip()][:12]):
                startp.add(q); break
    for i, pg in enumerate(pages):
        if num[i] is not None and num[i] >= 315 and starts_here(pg):
            startp.add(i)
    startp = sorted(startp)
    endp = max(i for i in range(b2p[1454], b2p[1454] + 3) if num[i] == 1454)
    startp = [p for p in startp if p <= endp]
    out=[]
    for k,p0 in enumerate(startp):
        s = num[p0]
        p1 = startp[k+1]-1 if k+1 < len(startp) else endp
        lines=[]
        for p in range(p0,p1+1): lines+=pages[p].split('\n')
        # title lines before the first date line, within first 15 non-empty lines
        ne=[(i,l) for i,l in enumerate(lines) if l.strip()]
        di=None
        for j,(i,l) in enumerate(ne[:15]):
            if DATE.match(l): di=j; break
        if di is None: continue
        tl=[l.strip() for _,l in ne[:di] if not re.fullmatch(r'\d+',l.strip()) and '毛泽东选集' not in l.replace(' ','')]
        title=re.sub(r'[*＊⑴-⒇]','',''.join(tl).replace(' ',''))
        title=re.sub(r'\d+.*$','',title) or title
        title=title.replace('论人民民主专政纪念中国共产党二十八周年','论人民民主专政')
        if title.startswith('附录'): title='附录：关于若干历史问题的决议'
        d=DATE.match(ne[di][1]).group(1).replace(' ','')
        # 页中间开始的短文：标题行（居中、短）后紧跟日期行
        cuts=[(ne[di][0],title,d)]
        for j in range(di+3,len(ne)):
            i,l=ne[j]
            if DATE.match(l) and len(l.strip())<=30:
                k=j-1; tl2=[]
                while k>j-4 and k>0:
                    pl=ne[k][1]; ps=pl.strip()
                    if len(pl)-len(pl.lstrip())>=4 and len(ps)<=34 and not re.search(r'[。，；：]$',ps) and not re.fullmatch(r'[\d\s]+',ps) and '毛泽东选集' not in ps.replace(' ','') and not re.search(r'\s\d{2,4}$',ps):
                        tl2.insert(0,ps); k-=1
                    else: break
                if tl2 and not any(kw in title for kw in ('命令和谈话', '两个文件', '两个电报', '序言和跋')) and re.sub(r'[*＊⑴-⒇\s]','',''.join(tl2)) not in ('跋','结论','引言','序','序言'):
                    t2=re.sub(r'[*＊⑴-⒇\s]','',''.join(tl2))
                    cuts.append((i,t2,DATE.match(l).group(1).replace(' ',''),ne[k+1][0]))
        for c,(i,t,dd,*rest) in enumerate(cuts):
            stop=cuts[c+1][3] if c+1<len(cuts) else len(lines)
            head,paras,notes=parse_article(lines, i+1, stop, t)
            out.append({'vol':'1-4','title':t,'date':dd,'headnote':head,'paras':paras,'notes':notes,'page':s})

    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vol14', required=True)
    ap.add_argument('--vol5', required=True)
    ap.add_argument('--out', default='build/text.json')
    a = ap.parse_args()
    v14 = split_vol14(layout_lines(a.vol14))
    k = next(i for i, x in enumerate(v14) if x['title'] == '矛盾论') + 1   # 第一卷沿用原方法（段落编号已用于对照）
    data = v14[:k] + split_vol24(a.vol14) + split_vol5(layout_lines(a.vol5))
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    json.dump(data, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(data)} 篇，{sum(len("".join(x["paras"])) for x in data)} 字 → {a.out}')

if __name__ == '__main__':
    main()
