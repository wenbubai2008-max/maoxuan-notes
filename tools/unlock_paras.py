#!/usr/bin/env python3
"""2027-01-01 起由工作流调用：把 text/para/*.json 解密成明文 JSON。"""
import base64, glob, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pw = os.environ['MAOXUAN_PASSWORD']
n = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'text', 'para', 'v[0-9]-*.json'))):
    rec = json.load(open(f, encoding='utf-8'))
    if 'ct' not in rec:
        continue
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=bytes.fromhex(rec['salt']), iterations=rec['iter']).derive(pw.encode())
    data = json.loads(AESGCM(key).decrypt(base64.b64decode(rec['iv']), base64.b64decode(rec['ct']), None))
    json.dump(data, open(f, 'w', encoding='utf-8'), ensure_ascii=False)
    n += 1
print('已解密', n, '个段落文件')
