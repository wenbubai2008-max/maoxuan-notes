#!/usr/bin/env python3
"""Build distinct simplified Water Margin 100/120 editions from Wikisource.

Wikisource page naming (verified 2026-11-18):
  水滸傳_(100回本)/第001回  .. /第100回 (Rongyutang)
  水滸傳_(120回本)/第001回  .. /第120回 (120-edition, related to Yuan Wuyai)
These Wikisource transcriptions do not reliably contain the historic margin comments.
Do not manufacture any original 李卓吾评 notes. Annotate only text actually present.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote, quote

import requests
from bs4 import BeautifulSoup
from opencc import OpenCC
from clean_shuihu_text import trim_paragraphs

ROOT = Path(__file__).resolve().parent.parent
API = "https://zh.wikisource.org/w/api.php"
URL = "https://zh.wikisource.org/zh-hans/"
HEADERS = {
    "User-Agent": "ReadingNotes/1.0 (public-domain literary research; https://github.com/wenbubai2008-max/reading)",
    "Accept": "application/json, text/html;q=0.9",
}
CC = OpenCC("t2s")
CHAPTER_RE = re.compile(r"/第0*(\d{1,3})回(?:$|[#?])")
SLEEP = 5.0
FAILURES = []

def request_json(session, params, tries=3):
    last = None
    for attempt in range(tries):
        if attempt > 0:
            time.sleep(30 * attempt)
        else:
            time.sleep(SLEEP)
        try:
            res = session.get(API, params=params, timeout=35, headers=HEADERS)
            if res.status_code == 429:
                retry_after = res.headers.get("Retry-After")
                if retry_after:
                    try: time.sleep(min(150, max(5, int(retry_after))))
                    except ValueError: pass
                last = f"429 Too Many Requests: {res.url}"
                continue
            res.raise_for_status()
            result = res.json()
            if "error" in result:
                raise ValueError(str(result["error"]))
            return result
        except Exception as exc:
            last = exc
    raise RuntimeError(str(last))

def load_html(session, title):
    j = request_json(session, {
        "action": "parse", "page": title, "prop": "text",
        "format": "json", "formatversion": 2,
        "disableeditsection": "1", "uselang": "zh-hans",
    })
    html = j.get("parse", {}).get("text")
    if not html or len(html) < 300:
        raise RuntimeError("Wikisource parse HTML empty")
    return html

def find_toc(session, edition):
    base = f"水滸傳_({edition}回本)"
    root = BeautifulSoup(load_html(session, base), "html.parser")
    content = root.select_one(".mw-parser-output") or root
    chapters = {}
    for anchor in content.select("a[href]"):
        href = unquote(anchor.get("href", ""))
        m = CHAPTER_RE.search(href)
        if not m:
            continue
        n = int(m.group(1))
        if n < 1 or n > int(edition):
            continue
        text = anchor.parent.get_text(" ", strip=True) if anchor.parent else ""
        label = anchor.get_text(" ", strip=True)
        if text.startswith(label):
            text = text[len(label):].strip(" \t　|:")
        elif label in text:
            text = text.replace(label, "", 1).strip(" \t　|:")
        title = CC.convert(re.sub(r"\s+", " ", text))
        if len(title) > 90:
            title = title[:90].rstrip()
        if title and n not in chapters:
            chapters[n] = {"number": n, "title": title, "source": URL + quote(base, safe="()") + f"/第{n:03d}回"}
    if len(chapters) < int(edition) * 0.9:
        raise RuntimeError(f"Only {len(chapters)}/{edition} chapter titles found")
    return [chapters[n] for n in sorted(chapters)]

def extract_chapter(session, edition, n, title):
    base = f"水滸傳_({edition}回本)"
    page = f"{base}/第{n:03d}回"
    soup = BeautifulSoup(load_html(session, page), "html.parser")
    content = soup.select_one(".mw-parser-output") or soup
    for tag in content.select(".mw-editsection, .noprint, .mw-references-wrap, .reference, .mw-empty-elt"):
        tag.decompose()
    paragraphs = []
    for paragraph in content.find_all("p"):
        if paragraph.find_parent(["nav", "table", "footer", "aside"]):
            continue
        raw = paragraph.get_text("", strip=False)
        raw = re.sub(r"[ \t]+", " ", raw).strip()
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        clean = CC.convert(raw)
        if len(clean) >= 8:
            paragraphs.append(clean)
    paragraphs = trim_paragraphs(paragraphs)
    chars = sum(len(p) for p in paragraphs)
    # Some Wikisource chapters use a few unusually long paragraphs. Check the
    # full text length before rejecting them solely for paragraph count.
    if chars < 1500 or (len(paragraphs) < 3 and chars < 9000):
        raise RuntimeError(f"Incomplete chapter: {n}, {chars} characters and {len(paragraphs)} paragraphs")
    # No historical 批语 are extracted unless actually marked and attribution verified.
    return {
        "edition": str(edition),
        "chapter": n,
        "title": title or f"第{n}回",
        "language": "简体中文",
        "source": URL + quote(base, safe="()") + f"/第{n:03d}回",
        "characters": chars,
        "paragraphs": paragraphs,
        "source_notes": [],
        "provenance": "维基文库对应版本的小说正文，经OpenCC繁转简。该转录未确认包含明代逐句评点。"
    }

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--edition", required=True, choices=["100", "120"])
    p.add_argument("--limit", type=int, default=0, help="Fetch at most N missing chapters")
    p.add_argument("--chapter", type=int, help="Specific chapter 1..max")
    args = p.parse_args()
    edition = args.edition
    max_ch = int(edition)
    out = ROOT / "shuihu" / edition
    text_dir = out / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()
    index_path = out / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        try:
            chapters = find_toc(sess, edition)
            index = {
                "edition": edition, "count": max_ch,
                "source": URL + quote(f"水滸傳_({edition}回本)", safe="()"),
                "chapters": chapters,
            }
            write_json(index_path, index)
            print(f"INDEX: {len(chapters)} titles in edition {edition}", flush=True)
        except Exception as exc:
            print(f"Index fetch failed: {exc}", file=sys.stderr, flush=True)
            index = {"chapters": []}
    titles = {int(c["number"]):c["title"] for c in index["chapters"]}
    if args.chapter is not None:
        if not (1 <= args.chapter <= max_ch):
            p.error("chapter outside edition range")
        remaining = [args.chapter]
    else:
        remaining = [i for i in range(1, max_ch+1) if not (text_dir/f"{i:03d}.json").exists()]
        if args.limit:
            remaining = remaining[:args.limit]
    failed = {}
    for idx, n in enumerate(remaining, start=1):
        try:
            record = extract_chapter(sess, edition, n, titles.get(n,""))
            write_json(text_dir/f"{n:03d}.json", record)
            print(f"OK {edition}/{n:03d} ({idx}/{len(remaining)}): {record['characters']} chars", flush=True)
        except Exception as exc:
            failed[str(n)] = str(exc)[:350]
            print(f"FAIL {edition}/{n:03d}: {exc}", file=sys.stderr, flush=True)
    available = [int(file.stem) for file in sorted(text_dir.glob("[0-9][0-9][0-9].json"))]
    status = {
        "edition": edition, "expected": max_ch,
        "available": available, "missing": [i for i in range(1, max_ch+1) if i not in available],
        "errors": failed,
    }
    write_json(out/"status.json", status)
    print(f"COMPLETE: {edition} edition, {len(available)}/{max_ch} available; {len(failed)} errors this run", flush=True)
    if failed and len(available) == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
