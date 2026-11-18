#!/usr/bin/env python3
"""生成静态网站。

内容在 content/：
  content/vol1/NN.json   每篇一个文件（结构见 README）
  content/method.html    总论页正文
  content/_*.html        个别篇目的附加栏目（深读等）
运行：python3 tools/build.py   → 生成 index.html、method.html、v1/NN.html
"""
import hashlib, html, json, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = lambda *p: os.path.join(ROOT, 'content', *p)

METHOD_NAMES = {
    'm01': '没有调查就没有发言权', 'm02': '判断是假设，要在行动中检验', 'm03': '从特殊出发，别照搬',
    'm04': '抓主要矛盾，盯住转化', 'm05': '全面比较力量', 'm06': '先问在什么条件下成立',
    'm07': '分层、量化、区别对待', 'm08': '战略上藐视，战术上重视', 'm09': '一般号召加个别指导',
    'm10': '又联合又斗争', 'm11': '能动性有边界', 'm12': '有的放矢地表达',
}
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@400;600;900&display=swap" rel="stylesheet">')

def esc(s):
    return html.escape(s, quote=True)

def load_articles():
    arts = []
    for f in sorted(glob.glob(C('vol1', '*.json'))):
        a = json.load(open(f, encoding='utf-8'))
        arts.append(a)
    return arts

def load_text_index():
    p = C('text_index.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []

def text_locked():
    p = os.path.join(ROOT, 'text', '001.html')
    return os.path.exists(p) and 'staticrypt' in open(p, encoding='utf-8').read(20000).lower()

def text_link_for(no, root):
    for t in load_text_index():
        if t.get('v1') == no:
            return f'{root}text/{t["file"]}'
    return None

def asset_ver():
    h = hashlib.md5()
    for f in ('site.css', 'site.js'):
        h.update(open(os.path.join(ROOT, 'assets', f), 'rb').read())
    return h.hexdigest()[:8]

def head(title, root):
    return (f'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{esc(title)}</title>\n{FONTS}\n'
            f'<link rel="stylesheet" href="{root}assets/site.css?v={asset_ver()}">\n</head>\n<body>\n')

def topbar(root, current):
    items = [('home', '首页', f'{root}index.html'), ('v1', '第一卷', f'{root}v1/01.html'),
             ('method', '总论：思维方法', f'{root}method.html'), ('text', '原文', f'{root}text/index.html')]
    links = ''.join(
        f'<a href="{u}"{" aria-current=\"page\"" if k == current else ""}>{t}</a>' for k, t, u in items)
    return (f'<header class="topbar"><a class="brand" href="{root}index.html">毛选读注'
            f'<small>《毛泽东选集》逐篇注解</small></a>'
            f'<nav class="sitenav" aria-label="网站栏目">{links}</nav></header>\n')

def foot(root):
    return (f'<footer class="sitefoot"><p>注解与分析由 Claude 撰写，供个人学习参考。原文由人民出版社 1967 年版提取，个别分段或文字可能有误，引用前请核对原书。</p></footer>\n'
            f'<script src="{root}assets/site.js?v={asset_ver()}"></script>\n</body>\n</html>\n')

def toc(arts, root, cur_no):
    out = ['<nav class="toc" aria-label="第一卷目录"><h2>第一卷</h2>']
    period = None
    for a in arts:
        if a['period'] != period:
            if period is not None:
                out.append('</ol>')
            period = a['period']
            out.append(f'<div class="period">{esc(period)}</div><ol>')
        on = ' class="on"' if a['no'] == cur_no else ''
        out.append(f'<li{on}><a href="{root}v1/{a["no"]:02d}.html"><span class="n">{a["no"]}</span>{esc(a["title"])}</a></li>')
    out.append('</ol><div class="more">按第一版（1951 年起）编排，共 17 篇。第二版在《星星之火，可以燎原》后加入《反对本本主义》。</div></nav>')
    return '\n'.join(out)

def wrap_terms(text, notes, start):
    """在提要里给注解词加标记；词不在提要里时只在右侧列出。"""
    out = esc(text)
    for i, n in enumerate(notes):
        num = start + i
        key = n.get('anchor', n['term'])
        k = esc(key)
        if k in out and 'data-note' not in out.split(k, 1)[0][-40:]:
            out = out.replace(k, f'<button class="term" data-note="n{num}">{k}<sup>{num}</sup></button>', 1)
    return out

def render_sections(a, root='../'):
    parts, num = [], 1
    link = text_link_for(a['no'], root)
    for si, s in enumerate(a['sections'], 1):
        notes = s.get('notes', [])
        summ = wrap_terms(s['sum'], notes, num)
        q = f'<p class="quote">{esc(s["quote"])}</p>' if s.get('quote') else ''
        lis = []
        for i, n in enumerate(notes):
            lis.append(f'<li class="note" id="n{num + i}"><div class="head"><span class="num">{num + i}</span>'
                       f'<b>{esc(n["term"])}</b><span class="kind">{esc(n.get("kind", "注"))}</span></div>{esc(n["text"])}</li>')
        num += len(notes)
        if link:
            slot_html = f'<a class="slot" href="{link}">阅读原文{"（需密码）" if text_locked() else ""} →</a>'
        else:
            slot_html = '<span class="slot">原文 · 暂未收入</span>'
        parts.append(f'<div class="sec"><div><h3><span class="sn">§{si}</span>{esc(s["h"])}</h3>'
                     f'{slot_html}{q}<p class="summary">{summ}</p><div class="orig" data-sec="{si - 1}"></div></div>'
                     f'<ol class="notes">{"".join(lis)}</ol></div>')
    return '\n'.join(parts), num - 1

def ul(items):
    return '<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul>'

def article_page(a, arts):
    root = '../'
    secs, nnotes = render_sections(a)
    tabs = [('text', '正文与注解'), ('read', '读法与应用'), ('background', '题解与背景')]
    extras = a.get('extra_tabs', [])
    if extras:
        tabs.insert(1, (extras[0]['id'], extras[0]['label']))
        for e in extras[1:]:
            tabs.append((e['id'], e['label']))
    btns = ''.join(f'<button role="tab" id="t-{k}" aria-controls="p-{k}" aria-selected="{"true" if i == 0 else "false"}" '
                   f'data-view="{k}">{esc(l)}</button>' for i, (k, l) in enumerate(tabs))
    meta = ''.join(f'<div><b>{esc(k)}</b>{esc(v)}</div>' for k, v in a['meta'])
    meta += f'<div><b>本页注解</b>{len(a["sections"])} 节提要 · {nnotes} 条注</div>'
    method_links = ''.join(
        f'<li><a href="{root}method.html#{m}"><span class="mid">{m[1:]}</span>{esc(METHOD_NAMES[m])}</a></li>' for m in a.get('methods', []))
    read = (f'<section class="panel long" id="p-read" role="tabpanel" aria-labelledby="t-read" hidden>'
            f'<h2><span class="k">主旨</span>这篇在回答什么</h2><p class="lede">{esc(a["gist"])}</p>'
            f'<h2><span class="k">方法</span>这篇里用到的思维方法</h2><ul class="mlinks">{method_links}</ul>'
            + (f'<p>{esc(a["method_note"])}</p>' if a.get('method_note') else '') +
            f'<h2><span class="k">应用</span>今天怎么用</h2>{ul(a["use"])}<p class="note-s">这些应用借用的是方法的结构，不是原文的结论。商业和日常生活的目标、规则、代价都和战争与政治不同，用之前请对照总论里相应各条的“迁移边界”。</p>'
            f'<h2><span class="k">争议</span>争议与局限</h2>{ul(a["debate"])}</section>')
    if a.get('background_html'):
        bg_inner = open(C(a['background_html']), encoding='utf-8').read()
    else:
        bg_inner = ''.join(f'<p>{esc(p)}</p>' for p in a['background'])
    bg = f'<section class="panel prose" id="p-background" role="tabpanel" aria-labelledby="t-background" hidden>{bg_inner}</section>'
    extra_html = ''
    for e in extras:
        body = open(C(e['file']), encoding='utf-8').read()
        extra_html += f'<section class="panel {e.get("cls", "long")}" id="p-{e["id"]}" role="tabpanel" aria-labelledby="t-{e["id"]}" hidden>{body}</section>\n'
    prev_next = []
    idx = [x['no'] for x in arts].index(a['no'])
    if idx > 0:
        p = arts[idx - 1]; prev_next.append(f'<a href="{p["no"]:02d}.html">← {esc(p["title"])}</a>')
    else:
        prev_next.append('<span></span>')
    if idx + 1 < len(arts):
        n = arts[idx + 1]; prev_next.append(f'<a href="{n["no"]:02d}.html">{esc(n["title"])} →</a>')
    page = (head(f'{a["title"]} · 毛选读注', root) + topbar(root, 'v1') + '<div class="shell">' + toc(arts, root, a['no']) +
            (f'<main data-para="{root}text/para/v1-{a["no"]:02d}.json">' if os.path.exists(os.path.join(ROOT, 'text', 'para', f'v1-{a["no"]:02d}.json')) else '<main>') +
            f'<div class="eyebrow">第一卷 · 第 {a["no"]} 篇 · {esc(a["period"])}</div>'
            f'<h1>{esc(a["title"])}</h1><p class="date">（{esc(a["date"])}）</p>'
            f'<div class="meta">{meta}</div>'
            f'<div class="tabs" role="tablist" aria-label="本篇内容">{btns}</div>'
            f'<section class="panel" id="p-text" role="tabpanel" aria-labelledby="t-text">'
            '<form class="orig-bar" id="orig-bar" hidden><label for="orig-pw">输入密码，在每一节下面直接显示对应的原文段落</label>'
            '<div class="row"><input id="orig-pw" type="password" autocomplete="current-password" placeholder="密码">'
            '<button type="submit">显示原文</button></div>'
            '<label class="rem"><input type="checkbox" id="orig-rem" checked> 在这台设备上记住</label><p class="err" id="orig-err" hidden>密码不对，请再试一次。</p></form>'
            + (f'<div class="notice"><div><b>原文。</b><a href="{text_link_for(a["no"], root)}">阅读这篇的原文 →</a>{"（2026 年 12 月 31 日前需要密码）" if text_locked() else ""}。下面是分节提要和注解，点下划线的词可以定位到右侧的注。</div></div>' if text_link_for(a['no'], root) else '<div class="notice"><div>下面是分节提要和注解，点下划线的词可以定位到右侧的注。</div></div>') +
            f'{secs}</section>\n{read}\n{bg}\n{extra_html}'
            f'<div class="pager">{"".join(prev_next)}</div></main></div>\n' + foot(root))
    return page

def home_page(arts):
    root = ''
    rows = ''.join(
        f'<li><a href="v1/{a["no"]:02d}.html"><span class="n">{a["no"]}</span><span class="t">{esc(a["title"])}'
        f'<span class="d">{esc(a["date"])}</span></span><span class="g">{esc(a["gist"])}</span></a></li>' for a in arts)
    body = f'''<div class="shell wide"><main>
<div class="eyebrow">毛选读注</div>
<h1>《毛泽东选集》逐篇注解与深读</h1>
<p class="lede">每篇文章做三件事：讲清楚写作背景和名词，把文章的推理过程拆开，再看它的方法今天还能怎么用、局限在哪里。观点会过时，思考的方法可以带走。</p>
<div class="cards">
  <a class="card" href="method.html"><b>总论：思维方法</b><span>从五卷里提炼的 12 条底层逻辑，每条都标出处、用法和失灵条件。</span></a>
  <a class="card" href="v1/01.html"><b>样章：中国社会各阶级的分析</b><span>最完整的一篇，含深读、版本变化和管理视角。</span></a>
</div>
<h2 class="vh">第一卷 <small>1925—1937 · 17 篇</small></h2>
<ol class="biglist">{rows}</ol>
<h2 class="vh">第二至五卷 <small>待做</small></h2>
<p class="note-s">第一卷完成后继续。</p>
</main></div>
<script>if(location.hash==='#method'){{location.replace('method.html');}}</script>
'''
    return head('毛选读注', root) + topbar(root, 'home') + body + foot(root)

def method_page(arts):
    root = ''
    body = open(C('method.html'), encoding='utf-8').read()
    # [[v1-NN]] → 链接到篇目
    def link(m):
        no = int(m.group(1)); a = next(x for x in arts if x['no'] == no)
        return f'<a href="v1/{no:02d}.html">《{esc(a["title"])}》</a>'
    body = re.sub(r'\[\[v1-(\d\d)\]\]', link, body)
    return head('总论：思维方法 · 毛选读注', root) + topbar(root, 'method') + f'<div class="shell wide"><main class="long">{body}</main></div>\n' + foot(root)

def text_index_page():
    root = '../'
    items = load_text_index()
    if not items:
        return None
    groups = [('一至四卷', '1925—1949', [t for t in items if t['vol'] != '5']), ('第五卷', '1949—1957', [t for t in items if t['vol'] == '5'])]
    body = ['<div class="shell wide"><main><div class="eyebrow">原文</div><h1>《毛泽东选集》原文</h1>',
            ('<p class="lede" id="pw-note">2026 年 12 月 31 日前，原文仅供个人阅读，打开时需要输入密码，勾选“在这台设备上记住密码”后，同一台设备只需输入一次。2027 年 1 月 1 日起自动公开，不再需要密码。</p>' if text_locked() else ''),
            f'<p class="note-s">共 {len(items)} 篇。由原书 PDF 自动提取，个别篇目的分段可能不准确；另有约十篇因排版问题暂未收入。标有“注解”的篇目可以对照阅读。</p>']
    for name, years, lst in groups:
        body.append(f'<h2 class="vh">{name} <small>{years} · {len(lst)} 篇</small></h2><ol class="biglist textlist">')
        for t in lst:
            tag = f'<a class="tag-note" href="{root}v1/{t["v1"]:02d}.html">注解</a>' if t.get('v1') else ''
            body.append(f'<li><a href="{t["file"]}"><span class="n">{int(t["file"][:3])}</span><span class="t">{esc(t["title"])}'
                        f'<span class="d">{esc(t["date"])}</span></span><span class="g">约 {t["chars"]//100/10:.1f} 千字</span></a>{tag}</li>')
        body.append('</ol>')
    body.append('</main></div>')
    return head('原文 · 毛选读注', root) + topbar(root, 'text') + ''.join(body) + foot(root)

def main():
    arts = load_articles()
    tip = text_index_page()
    if tip:
        os.makedirs(os.path.join(ROOT, 'text'), exist_ok=True)
        open(os.path.join(ROOT, 'text', 'index.html'), 'w', encoding='utf-8').write(tip)
    os.makedirs(os.path.join(ROOT, 'v1'), exist_ok=True)
    for a in arts:
        open(os.path.join(ROOT, 'v1', f'{a["no"]:02d}.html'), 'w', encoding='utf-8').write(article_page(a, arts))
    open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(home_page(arts))
    open(os.path.join(ROOT, 'method.html'), 'w', encoding='utf-8').write(method_page(arts))
    print(f'生成 {len(arts)} 篇 + 首页 + 总论')

if __name__ == '__main__':
    main()
