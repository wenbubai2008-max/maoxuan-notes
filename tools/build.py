#!/usr/bin/env python3
"""生成静态网站。

内容在 content/：
  content/vol1/NN.json   每篇一个文件（结构见 README）
  content/method.html    总论页正文
  content/_*.html        个别篇目的附加栏目（深读等）
  content/vol5/NN.json   第五卷重点篇，NN 是第五卷目录里的篇序（1—70）
运行：python3 tools/build.py   → 生成 index.html、maoxuan.html、method.html、v1/NN.html、v5/NN.html、v5/index.html
"""
import hashlib, html, json, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = 'wenbubai2008-max/reading'
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

VOL_NAME = {'1': '第一卷', '2': '第二卷', '3': '第三卷', '4': '第四卷', '5': '第五卷'}
VOL_INFO = {1: ('1925—1937', '第一、二次国内革命战争时期'), 2: ('1937—1941', '抗日战争时期（上）'),
            3: ('1941—1945', '抗日战争时期（下）'), 4: ('1945—1949', '第三次国内革命战争时期'),
            5: ('1949—1957', '社会主义革命和建设时期')}

def load_articles(vol='1'):
    arts = []
    for f in sorted(glob.glob(C(f'vol{vol}', '*.json'))):
        a = json.load(open(f, encoding='utf-8'))
        a['vol'] = vol
        arts.append(a)
    return arts

def load_text_index():
    p = C('text_index.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []

def text_locked():
    p = os.path.join(ROOT, 'text', '001.html')
    return os.path.exists(p) and 'staticrypt' in open(p, encoding='utf-8').read(20000).lower()

def text_link_for(no, root, vol='1'):
    for t in load_text_index():
        if t.get(f'v{vol}') == no:
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
    if current == 'shelf':
        return (f'<header class="topbar"><a class="brand" href="{root}index.html">读书'
                f'<small>读过的书，和读书时想清楚的事</small></a></header>\n')
    cur = lambda k: ' aria-current="page"' if k == current else ''
    vols = ''.join(f'<a href="{root}v{n}/index.html"{cur("v" + str(n))} title="第{c}卷">{c}</a>' for n, c in zip(range(1, 6), '一二三四五'))
    links = (f'<a href="{root}maoxuan.html"{cur("home")}>本书首页</a>'
             f'<span class="volnav" aria-label="分卷">卷{vols}</span>'
             f'<a href="{root}method.html"{cur("method")}>总论：思维方法</a>')
    return (f'<header class="topbar"><a class="brand" href="{root}index.html">读书</a>'
            f'<span class="crumb">›</span><a class="book" href="{root}maoxuan.html">毛泽东选集</a>'
            f'<nav class="sitenav" aria-label="本书栏目">{links}</nav></header>\n')

def foot(root, shelf=False):
    return (f'<footer class="sitefoot"><p>{"读书笔记由 Claude 协助撰写，供个人学习参考。" if shelf else "注解与分析由 Claude 撰写，供个人学习参考。原文据人民出版社版本提取（一至四卷 1967 年版，第五卷 1977 年版），个别分段或文字可能有误，引用前请核对原书。"}</p></footer>\n'
            f'<script src="{root}assets/site.js?v={asset_ver()}"></script>\n</body>\n</html>\n')

def toc(arts, root, cur_no):
    vol = arts[0]['vol']
    vn = VOL_NAME[vol]
    out = [f'<nav class="toc" aria-label="{vn}目录"><h2>{vn}</h2>']
    period = None
    for a in arts:
        if a['period'] != period:
            if period is not None:
                out.append('</ol>')
            period = a['period']
            out.append(f'<div class="period">{esc(period)}</div><ol>')
        on = ' class="on"' if a['no'] == cur_no else ''
        out.append(f'<li{on}><a href="{root}v{vol}/{a["no"]:02d}.html"><span class="n">{a["no"]}</span>{esc(a["title"])}</a></li>')
    if vol in ('2', '3', '4'):
        out.append(f'</ol><div class="more">{VOL_NAME[vol]}共 {len(arts)} 篇，序号是原书目录里的篇序。<a href="{root}v{vol}/index.html">本卷脉络 →</a></div></nav>')
    elif vol == '5':
        out.append(f'</ol><div class="more">第五卷共 70 篇，序号是原书目录里的篇序。<a href="{root}v5/index.html">本卷脉络 →</a> · <a href="{root}v5/tulong.html">“屠龙卷”专题 →</a></div></nav>')
    else:
        out.append(f'</ol><div class="more">按第一版（1951 年起）编排，共 17 篇。第二版在《星星之火，可以燎原》后加入《反对本本主义》。<a href="{root}v1/index.html">本卷脉络 →</a></div></nav>')
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
    link = text_link_for(a['no'], root, a['vol'])
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
                     f'{slot_html}{q}<div class="sum-label">提要</div><p class="summary">{summ}</p><div class="orig" data-sec="{si - 1}"></div></div>'
                     f'<ol class="notes">{"".join(lis)}</ol></div>')
    return '\n'.join(parts), num - 1

def ul(items):
    return '<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul>'

def article_page(a, arts):
    root = '../'
    vol = a['vol']; key = f'v{vol}-{a["no"]:02d}'; tl = text_link_for(a['no'], root, vol)
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
            + (f'<h2><span class="k">后来</span>后来发生了什么</h2>{ul(a["after"])}' if a.get('after') else '') +
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
    vol = a['vol']; key = f'v{vol}-{a["no"]:02d}'; tl = text_link_for(a['no'], root, vol)
    prev_next = []
    idx = [x['no'] for x in arts].index(a['no'])
    if idx > 0:
        p = arts[idx - 1]; prev_next.append(f'<a href="{p["no"]:02d}.html">← {esc(p["title"])}</a>')
    else:
        prev_next.append('<span></span>')
    if idx + 1 < len(arts):
        n = arts[idx + 1]; prev_next.append(f'<a href="{n["no"]:02d}.html">{esc(n["title"])} →</a>')
    page = (head(f'{a["title"]} · 毛选 · 读书', root) + topbar(root, f'v{vol}') + '<div class="shell">' + toc(arts, root, a['no']) +
            f'<main data-root="{root}" data-repo="{REPO}" data-notes="content/notes/{key}.json"' +
            (f' data-para="{root}text/para/{key}.json">' if os.path.exists(os.path.join(ROOT, 'text', 'para', f'{key}.json')) else '>') +
            f'<div class="eyebrow">{VOL_NAME[vol]} · 第 {a["no"]} 篇 · {esc(a["period"])}</div>'
            f'<h1>{esc(a["title"])}</h1><p class="date">（{esc(a["date"])}）</p>'
            f'<div class="meta">{meta}</div>'
            f'<div class="tabs" role="tablist" aria-label="本篇内容">{btns}</div>'
            f'<section class="panel" id="p-text" role="tabpanel" aria-labelledby="t-text">'
            '<form class="orig-bar" id="orig-bar" hidden><label for="orig-pw">输入密码，在每一节下面直接显示对应的原文段落</label>'
            '<div class="row"><input id="orig-pw" type="password" autocomplete="current-password" placeholder="密码">'
            '<button type="submit">确定</button></div>'
            '<label class="rem"><input type="checkbox" id="orig-rem" checked> 在这台设备上记住</label><p class="err" id="orig-err" hidden>密码不对，请再试一次。</p></form>'
            + (f'<div class="notice"><div><b>原文。</b><a href="{tl}">阅读这篇的原文 →</a>{"（2026 年 12 月 31 日前需要密码）" if text_locked() else ""}。下面是分节提要和注解，点下划线的词可以定位到右侧的注。</div></div>' if tl else '<div class="notice"><div>下面是分节提要和注解，点下划线的词可以定位到右侧的注。</div></div>') +
            f'<p class="mx-notes-entry"><a href="#" id="mx-notes-btn">写笔记</a></p>'
            '<div class="legend"><span><i class="lo"></i>原文（宋体，米黄底）</span><span><i class="la"></i>提要和注解（黑体，蓝线，由 Claude 撰写）</span></div>'
            f'{secs}</section>\n{read}\n{bg}\n{extra_html}'
            '<dialog id="mx-token" class="mx-dlg"><h3>GitHub 令牌</h3>'
            '<p>笔记会直接保存到你的 GitHub 仓库。粘贴一个只允许修改本仓库内容的令牌，它只保存在这台设备的浏览器里。</p>'
            '<input id="mx-token-in" type="password" placeholder="github_pat_…" autocomplete="off">'
            '<div class="row"><button type="button" id="mx-token-save">保存</button><button type="button" id="mx-token-clear" class="ghost">清除</button>'
            '<button type="button" id="mx-token-cancel" class="ghost">取消</button></div></dialog>'
            f'<div class="pager">{"".join(prev_next)}</div></main></div>\n' + foot(root))
    return page

def biglist(arts):
    return ''.join(
        f'<li><a href="v{a["vol"]}/{a["no"]:02d}.html"><span class="n">{a["no"]}</span><span class="t">{esc(a["title"])}'
        f'<span class="d">{esc(a["date"])}</span></span><span class="g">{esc(a["gist"])}</span></a></li>' for a in arts)

def home_page(arts, arts5, arts2=(), arts3=(), arts4=()):
    root = ''
    items = load_text_index()
    cards = []
    for n in range(1, 6):
        years, period = VOL_INFO[n]
        total = len([t for t in items if t.get('volno') == n])
        done = {1: len(arts), 2: len(arts2), 3: len(arts3), 4: len(arts4), 5: len(arts5)}.get(n, 0)
        if done and done >= total:
            st, cls = f'{done} 篇全部注解', 'done'
        elif done:
            st, cls = f'重点 {done} 篇已注解 · 其余可读原文', 'part'
        else:
            st, cls = '原文可读 · 注解待做', 'todo'
        cards.append(f'<a class="volcard {cls}" href="v{n}/index.html"><span class="vn">第{"一二三四五"[n-1]}卷</span>'
                     f'<span class="vy">{years}</span><span class="vp">{period}</span>'
                     f'<span class="vc">共 {total} 篇</span><span class="vs">{st}</span>{'<span class="vx">含“屠龙卷”专题</span>' if n == 5 else ''}</a>')
    body = f'''<div class="shell wide"><main>
<div class="eyebrow"><a href="index.html">书架</a> › 毛泽东选集</div>
<h1>《毛泽东选集》逐篇注解与深读</h1>
<p class="lede">每篇文章做三件事：讲清楚写作背景和名词，把文章的推理过程拆开，再看它的方法今天还能怎么用、局限在哪里。观点会过时，思考的方法可以带走。</p>
<div class="volgrid">{"".join(cards)}</div>
<div class="cards">
  <a class="card" href="method.html"><b>总论：思维方法</b><span>从五卷里提炼的 12 条底层逻辑，每条都标出处、用法和失灵条件。</span></a>
</div>
</main></div>

'''
    return head('毛泽东选集 · 读书', root) + topbar(root, 'home') + body + foot(root)

def resolve_links(html_, root, arts_by):
    """[[v1-NN]] → 注解页；[[t:标题]] → 原文页。"""
    items = load_text_index()
    def v(m):
        a = arts_by.get((m.group(1), int(m.group(2))))
        return f'<a href="{root}v{m.group(1)}/{int(m.group(2)):02d}.html">《{esc(a["title"])}》</a>' if a else m.group(0)
    def t(m):
        title = m.group(1)
        it = next((x for x in items if x['title'] == title), None)
        if not it:
            return f'《{esc(title)}》'
        if it.get('v1'):
            return f'<a href="{root}v1/{it["v1"]:02d}.html">《{esc(title)}》</a>'
        for vv in ('2', '3', '4'):
            if it.get('v' + vv):
                return f'<a href="{root}v{vv}/{it["v" + vv]:02d}.html">《{esc(title)}》</a>'
        if it.get('v5'):
            return f'<a href="{root}v5/{it["v5"]:02d}.html">《{esc(title)}》</a>'
        return f'<a href="{root}text/{it["file"]}">《{esc(title)}》</a>'
    html_ = re.sub(r'\[\[v([1-5])-(\d\d)\]\]', v, html_)
    return re.sub(r'\[\[t:([^\]]+)\]\]', t, html_)

def vol_index_page(n, arts_by):
    root = '../'
    vol = str(n); cn = '一二三四五'[n-1]
    years, period = VOL_INFO[n]
    items = [t for t in load_text_index() if t.get('volno') == n]
    intro = open(C(f'vol{n}_intro.html'), encoding='utf-8').read() if os.path.exists(C(f'vol{n}_intro.html')) else ''
    ov = C('overview', f'vol{n}.html')
    overview = resolve_links(open(ov, encoding='utf-8').read(), root, arts_by) if os.path.exists(ov) else ''
    rows = []
    nann = 0
    for t in items:
        no = t.get('v' + vol)
        a = arts_by.get((vol, no)) if no else None
        seq = no if n in (2, 3, 4, 5) else (a['no'] if a else t['seq'])
        if a:
            nann += 1
            rows.append(f'<li class="has-ann"><a href="{no:02d}.html"><span class="n">{seq}</span><span class="t">{esc(t["title"])}'
                        f'<span class="d">{esc(t["date"])}</span></span><span class="g">{esc(a["gist"])}</span></a>'
                        f'<a class="tag-note" href="{root}text/{t["file"]}">原文</a></li>')
        else:
            rows.append(f'<li><a href="{root}text/{t["file"]}"><span class="n">{seq}</span><span class="t">{esc(t["title"])}'
                        f'<span class="d">{esc(t["date"])}</span></span><span class="g">原文 · 约 {t["chars"]//100/10:.1f} 千字</span></a></li>')
    lock = "（2026 年 12 月 31 日前需要密码）" if text_locked() else ""
    status = (f'共 {len(items)} 篇，全部已做注解和分析。' if nann == len(items) else
              f'共 {len(items)} 篇。带摘要的 {nann} 篇已做注解和分析，点进去看；其余直接打开原文{lock}。' if nann else
              f'共 {len(items)} 篇。这一卷的注解还没有做，下面每篇都可以直接打开原文{lock}。')
    body = (f'<div class="shell wide"><main><div class="eyebrow"><a href="{root}maoxuan.html">毛泽东选集</a> › 第{cn}卷</div>'
            f'<h1>第{cn}卷 <small class="h1s">{years} · {period}</small></h1>{intro}'
            + (f'<a class="card tulong" href="tulong.html"><b>专题：“屠龙卷”——第五卷里的反官僚主义一线</b><span>这一卷为什么被叫作“屠龙卷”，文本里说了什么，后来怎样实践，结果如何，今天能学到什么。</span></a>' if n == 5 else '') +
            f'<details class="fold vol-ov"><summary>本卷脉络与收获<span class="hint">分阶段梳理这一卷，以及从中能学到什么（点开）</span></summary><div class="overview">{overview}</div></details>'
            f'<h2 class="vh">全部篇目</h2><p class="note-s">{status}</p>'
            f'<ol class="biglist textlist v5list">{"".join(rows)}</ol></main></div>\n')
    return head(f'第{cn}卷 · 毛选 · 读书', root) + topbar(root, f'v{n}') + body + foot(root)

def shelf_page():
    books = json.load(open(C('books.json'), encoding='utf-8'))
    cards = ''.join(
        f'<a class="bookshelf-entry shelf-{esc(b["id"])}" href="{esc(b["href"])}" aria-label="阅读{esc(b["title"])}">'
        f'<h2>{esc(b["title"])}</h2>'
        f'<p class="bookshelf-edition">{esc(b.get("shelf_subtitle", b.get("edition", "")))}</p>'
        f'<div class="bookshelf-cover" aria-hidden="true"><span>{esc(b["title"])}</span></div>'
        f'</a>'
        for b in books)
    body = (f'<main class="bookshelf-home">'

            f'<div class="bookshelf-grid">{cards}</div>'
            f'</main>\n')
    return head('读书', '') + body + '</body>\n</html>\n'

def method_page(arts):
    root = ''
    body = open(C('method.html'), encoding='utf-8').read()
    # [[v1-NN]] → 链接到篇目
    def link(m):
        vol, no = m.group(1), int(m.group(2))
        a = next(x for x in arts + load_articles('2') + load_articles('3') + load_articles('4') + load_articles('5') if x['vol'] == vol and x['no'] == no)
        return f'<a href="v{vol}/{no:02d}.html">《{esc(a["title"])}》</a>'
    # 每条方法后面自动列出全书里标注了这条方法的篇目
    allarts = arts + load_articles('2') + load_articles('3') + load_articles('4') + load_articles('5')
    def backlinks(m):
        mid = m.group(1)
        out = []
        for vol in ('1', '2', '3', '4', '5'):
            hits = [x for x in allarts if x['vol'] == vol and mid in x.get('methods', [])]
            if hits:
                out.append(f'{VOL_NAME[vol]}：' + '、'.join(f'<a href="v{vol}/{x["no"]:02d}.html">{x["no"]}《{esc(x["title"])}》</a>' for x in hits))
        total = sum(1 for x in allarts if mid in x.get('methods', []))
        rel = (f'<dt>全书相关篇目</dt><dd class="rel"><details><summary>共 {total} 篇用到或检验了这一条（点开）</summary>'
               f'{"；".join(out)}</details></dd>') if out else ''
        blk = m.group(0)
        return blk.replace('<dt class="fail">', rel + '<dt class="fail">', 1)
    body = re.sub(r'<div class="method" id="(m\d\d)">.*?</dl>', backlinks, body, flags=re.S)
    body = re.sub(r'\[\[v([1-5])-(\d\d)\]\]', link, body)
    return head('总论：思维方法 · 毛选 · 读书', root) + topbar(root, 'method') + f'<div class="shell wide"><main class="long">{body}</main></div>\n' + foot(root)

def text_index_page():
    root = '../'
    items = load_text_index()
    if not items:
        return None
    groups = [(f'第{"一二三四五"[n-1]}卷', VOL_INFO[n][0], [t for t in items if t.get('volno') == n]) for n in range(1, 6)]
    body = ['<div class="shell wide"><main><div class="eyebrow">原文</div><h1>《毛泽东选集》原文</h1>',
            ('<p class="lede" id="pw-note">2026 年 12 月 31 日前，原文仅供个人阅读，打开时需要输入密码，勾选“在这台设备上记住密码”后，同一台设备只需输入一次。2027 年 1 月 1 日起自动公开，不再需要密码。</p>' if text_locked() else ''),
            f'<p class="note-s">共 {len(items)} 篇。由原书 PDF 自动提取，个别篇目的分段可能不准确；编号是各卷内的篇序。标有“注解”的篇目可以对照阅读。</p>']
    for name, years, lst in groups:
        body.append(f'<h2 class="vh">{name} <small>{years} · {len(lst)} 篇</small></h2><ol class="biglist textlist">')
        for t in lst:
            tag = ''.join(f'<a class="tag-note" href="{root}v{v}/{t["v" + v]:02d}.html">注解</a>' for v in ('1', '2', '3', '4', '5') if t.get('v' + v))
            body.append(f'<li><a href="{t["file"]}"><span class="n">{t.get("seq", int(t["file"][:3]))}</span><span class="t">{esc(t["title"])}'
                        f'<span class="d">{esc(t["date"])}</span></span><span class="g">约 {t["chars"]//100/10:.1f} 千字</span></a>{tag}</li>')
        body.append('</ol>')
    body.append('</main></div>')
    return head('原文 · 毛选 · 读书', root) + topbar(root, 'text') + ''.join(body) + foot(root)

def main():
    arts = load_articles('1')
    arts5 = load_articles('5')
    arts2 = load_articles('2')
    arts3 = load_articles('3')
    arts4 = load_articles('4')
    tip = text_index_page()
    if tip:
        os.makedirs(os.path.join(ROOT, 'text'), exist_ok=True)
        open(os.path.join(ROOT, 'text', 'index.html'), 'w', encoding='utf-8').write(tip)
    for vol, lst in (('1', arts), ('2', arts2), ('3', arts3), ('4', arts4), ('5', arts5)):
        os.makedirs(os.path.join(ROOT, f'v{vol}'), exist_ok=True)
        for a in lst:
            open(os.path.join(ROOT, f'v{vol}', f'{a["no"]:02d}.html'), 'w', encoding='utf-8').write(article_page(a, lst))
    arts_by = {(a['vol'], a['no']): a for a in arts + arts2 + arts3 + arts4 + arts5}
    tl = resolve_links(open(C('v5_tulong.html'), encoding='utf-8').read(), '../', arts_by)
    os.makedirs(os.path.join(ROOT, 'v5'), exist_ok=True)
    open(os.path.join(ROOT, 'v5', 'tulong.html'), 'w', encoding='utf-8').write(
        head('“屠龙卷”专题 · 第五卷 · 毛选 · 读书', '../') + topbar('../', 'v5') + f'<div class="shell wide"><main class="long tulong-page">{tl}</main></div>\n' + foot('../'))
    for n in range(1, 6):
        os.makedirs(os.path.join(ROOT, f'v{n}'), exist_ok=True)
        open(os.path.join(ROOT, f'v{n}', 'index.html'), 'w', encoding='utf-8').write(vol_index_page(n, arts_by))
    open(os.path.join(ROOT, 'maoxuan.html'), 'w', encoding='utf-8').write(home_page(arts, arts5, arts2, arts3, arts4))
    open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(shelf_page())
    open(os.path.join(ROOT, 'method.html'), 'w', encoding='utf-8').write(method_page(arts))
    print(f'生成 第一卷 {len(arts)} 篇 + 第二卷 {len(arts2)} 篇 + 第三卷 {len(arts3)} 篇 + 第四卷 {len(arts4)} 篇 + 第五卷 {len(arts5)} 篇 + 书架 + 本书首页 + 总论')

if __name__ == '__main__':
    main()
