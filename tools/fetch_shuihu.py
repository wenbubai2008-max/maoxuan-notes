#!/usr/bin/env python3
"""Download the public-domain Jin Shengtan 70-chapter Shuǐhǔzhuàn text.

Data source: https://zh.wikisource.org/wiki/水滸傳_(70回本)
Output: shuihu/text/000.json ... 070.json, in simplified Chinese.
Original text and Jin Shengtan's annotations are kept distinct.
Do not claim other edition annotations come from this source.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from opencc import OpenCC

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "shuihu" / "text"
SOURCE_TITLE = "水滸傳_(70回本)"
API = "https://zh.wikisource.org/w/api.php"
HEADERS = {"User-Agent": "ReadingNotes/1.0 (educational static reading site; contact via GitHub wenbubai2008-max/reading)"}
CC = OpenCC("t2s")
NOTE = re.compile(r"〖([\s\S]*?)〗")
EXCLUDE = ("table", "nav", "aside", "footer", "sup", ".noprint", ".printfooter", ".mw-editsection", ".reference", ".reflist", ".ws-noexport")

def clean(s: str) -> str:
    s = s.replace("\u200b", "").replace("\ufeff", "")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"(\n[ \t]*){3,}", "\n\n", s)
    return CC.convert(s.strip())

def fetch_html(number: int) -> str:
    chapter = "楔子" if number == 0 else f"第{number:02d}回"
    title = SOURCE_TITLE + "/" + chapter
    params = {"action": "parse", "page": title, "prop": "text", "format": "json", "formatversion": 2, "disableeditsection": "1", "uselang": "zh-hans"}
    for attempt in range(3):
        try:
            res = requests.get(API, params=params, headers=HEADERS, timeout=23)
            res.raise_for_status()
            data = res.json()
            if "error" in data:
                raise ValueError(str(data["error"]))
            output = data["parse"]["text"]
            if not isinstance(output, str) or len(output) < 600:
                raise ValueError("Unexpected short response")
            return output
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")

def extract(number: int, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one(".mw-parser-output") or soup
    pieces = []
    for element in root.find_all(["p", "h2", "h3"]):
        if element.find_parent(EXCLUDE):
            continue
        if element.get("class") and any(c in {"mw-empty-elt", "mw-heading", "noprint"} for c in element.get("class", [])):
            continue
        if element.name in {"h2", "h3"}:
            value = clean(element.get_text("", strip=False))
            if value and len(value) < 90 and "目录" not in value:
                pieces.append(("heading", value))
            continue
        text = clean(element.get_text("", strip=False))
        if not text or text in {"上一回", "下一回"}:
            continue
        if len(text) < 8 and not ("〖" in text or "〗" in text):
            continue
        pieces.append(("paragraph", text))
    # Full source carries notes that can span paragraph breaks.
    raw = "\n\n".join(t for _, t in pieces)
    if not raw or len(raw) < 1000:
        raise ValueError(f"Chapter {number}: only {len(raw)} chars extracted; source markup may have changed")
    tokens = []
    comments = []
    pos = 0
    for match in NOTE.finditer(raw):
        tokens.append(raw[pos:match.start()])
        note_text = clean(match.group(1))
        note_kind = "夹批"
        if re.match(r"^\s*(?:总批|總批|眉批|夹批|夾批)[:：]", note_text):
            note_kind, note_text = re.split(r"[:：]", note_text, maxsplit=1)
            note_kind = CC.convert(note_kind.strip())
        if note_text.strip():
            note_id = len(comments)
            comments.append({"id": note_id, "kind": note_kind, "text": note_text.strip()})
            tokens.append(f"⟦J{note_id}⟧")
        pos = match.end()
    tokens.append(raw[pos:])
    plain = "".join(tokens)
    paragraphs = [p.strip() for p in plain.split("\n\n") if p.strip()]
    # Check for remnants of unclosed note markup before publishing.
    if "〖" in plain or "〗" in plain:
        raise ValueError(f"Chapter {number}: unbalanced original annotations")
    total_len = len(re.sub(r"⟦J\d+⟧", "", plain))
    if total_len < 700:
        raise ValueError(f"Chapter {number}: short text after annotation cleanup ({total_len})")
    if len(paragraphs) > 800:
        raise ValueError("Unreasonable paragraph count")
    chapter = "楔子" if number == 0 else f"第{number:02d}回"
    return {
        "chapter": number, "title": chapter,
        "edition": "金圣叹评七十回本",
        "language": "简体中文",
        "source": "https://zh.wikisource.org/zh-hans/" + quote(SOURCE_TITLE + "/" + chapter),
        "original_characters": total_len,
        "paragraphs": paragraphs,
        "jin_notes": comments,
        "source_policy": "金圣叹总批、夹批来自此版本，容与堂、袁无涯另以不同来源核验；本站点评为原创研究。"
    }

def process(number):
    doc = extract(number, fetch_html(number))
    target = OUT / f"{number:03}.json"
    target.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return number, doc["original_characters"], len(doc["jin_notes"])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chapter", type=int, help="Fetch one chapter, 0–70")
    a = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    nums = list(range(71)) if a.chapter is None else [a.chapter]
    if not all(0 <= n <= 70 for n in nums):
        p.error("Chapter must be 0–70")
    errors = []
    # Low concurrency to respect source capacity; independent files allow incremental retries.
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(process, n): n for n in nums}
        for future in concurrent.futures.as_completed(futures):
            number = futures[future]
            try:
                n, size, count = future.result()
                print(f"OK {n:03}: {size} original chars, {count} Jin comments", flush=True)
            except Exception as e:
                print(f"FAIL {number:03}: {e}", file=sys.stderr, flush=True)
                errors.append(number)
    (OUT / "status.json").write_text(json.dumps({"available": [int(p.stem) for p in sorted(OUT.glob("[0-9][0-9][0-9].json"))], "failed": errors}, ensure_ascii=False), encoding="utf-8")
    if errors:
        print(f"Chapters needing review/retry: {errors}", file=sys.stderr)
        if len(errors) == len(nums):
            sys.exit(1)

if __name__ == "__main__":
    main()
