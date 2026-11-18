#!/usr/bin/env python3
"""把第一卷各节对应的原文段落加密，写到 text/para/v1-NN.json。
用法：MAOXUAN_PASSWORD=密码 python3 tools/encrypt_paras.py
需要 build/text.json（由 build_text.py 生成）和 content/para_map.json。
加密：PBKDF2-SHA256(密码, 盐, 310000 次) → AES-256-GCM。盐在 text/para/salt.txt，所有篇目共用。"""
import base64, json, os, re, secrets, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITER = 310000
HEAD_TAIL = re.compile(r'([一二三四五六七八九十]|第[一二三四五六七八九十]+[章节])[^。！？”]{1,24}$')

def derive(pw, salt):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode())

def norm(x):
    return re.sub(r'[\s“”"]', '', x)

def cut_tail(p, h):
    """段落末尾如果带着下一节的标题，就去掉。"""
    hn = norm(h)[:4]
    tail_start = max(0, len(p) - len(h) - 16)
    k = p.find(hn[:2], tail_start)
    while k != -1:
        if norm(p[k:]).startswith(hn):
            p = p[:k]
            break
        k = p.find(hn[:2], k + 1)
    p = p.rstrip('“"')
    p = re.sub(r'(第[一二三四五六七八九十]+[章节])+$', '', p)
    p = re.sub(r'(?<=[。”！？：）])[一二三四五六七八九十]$', '', p)
    return p

def cut_head(p, h):
    hn = norm(h)
    q = norm(p)
    for pre in ('', '一', '二', '三', '四', '五', '六', '七', '八', '—'):
        if q.startswith(pre + hn):
            # 在原文里找到标题结束的位置
            n, cnt = 0, 0
            target = len(pre + hn)
            while n < len(p) and cnt < target:
                if not re.match(r'[\s“”"]', p[n]):
                    cnt += 1
                n += 1
            rest = p[n:]
            if re.match(r'^[。，：；、]', rest):
                return p  # 段首的小标题本身就是句子的一部分，保留
            return re.sub(r'^[”"]*——[^，。“]{2,16}?(形式|问题)', '', rest)
    return p

def build_payload(no, paras, ranges, heads):
    out = []
    for si, r in enumerate(ranges):
        if r is None:
            out.append(None); continue
        a, b = r
        seg = list(paras[a:b + 1])
        seg[0] = cut_head(seg[0], heads[si])
        nxt = next((heads[j] for j in range(si + 1, len(ranges)) if ranges[j] is not None), None)
        if nxt:
            seg[-1] = cut_tail(seg[-1], nxt)
        out.append([x for x in seg if x.strip()])
    return {'v1': no, 'sections': out}

def main():
    pw = os.environ.get('MAOXUAN_PASSWORD')
    if not pw:
        sys.exit('请先设置 MAOXUAN_PASSWORD')
    text = json.load(open(os.path.join(ROOT, 'build', 'text.json'), encoding='utf-8'))
    idx = json.load(open(os.path.join(ROOT, 'content', 'text_index.json'), encoding='utf-8'))
    pmap = json.load(open(os.path.join(ROOT, 'content', 'para_map.json'), encoding='utf-8'))
    outdir = os.path.join(ROOT, 'text', 'para')
    os.makedirs(outdir, exist_ok=True)
    salt_path = os.path.join(outdir, 'salt.txt')
    if os.path.exists(salt_path):
        salt = bytes.fromhex(open(salt_path).read().strip())
    else:
        salt = secrets.token_bytes(16); open(salt_path, 'w').write(salt.hex())
    key = derive(pw, salt)
    for k, ranges in pmap.items():
        if k.startswith('_'):
            continue
        no = int(k)
        f = next(x['file'] for x in idx if x.get('v1') == no)
        paras = text[int(f[:3]) - 1]['paras']
        art = json.load(open(os.path.join(ROOT, 'content', 'vol1', f'{no:02d}.json'), encoding='utf-8'))
        heads = [s['h'].replace('第五章 ', '').split('：')[0] for s in art['sections']]
        payload = json.dumps(build_payload(no, paras, ranges, heads), ensure_ascii=False).encode()
        iv = secrets.token_bytes(12)
        ct = AESGCM(key).encrypt(iv, payload, None)
        rec = {'enc': 'pbkdf2-sha256/aes-256-gcm', 'iter': ITER, 'salt': salt.hex(),
               'iv': base64.b64encode(iv).decode(), 'ct': base64.b64encode(ct).decode()}
        json.dump(rec, open(os.path.join(outdir, f'v1-{no:02d}.json'), 'w'), ensure_ascii=False)
    print('已加密', len([k for k in pmap if not k.startswith('_')]), '篇 → text/para/')

if __name__ == '__main__':
    main()
