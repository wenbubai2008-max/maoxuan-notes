#!/usr/bin/env python3
"""Offline repair of previously cached paragraphs whose Jin notes are bracketed.

No network requests. Only rewrites cache entries with zero extracted Jin notes.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "shuihu" / "text"
NOTES = re.compile(r"[〖【]([\s\S]*?)[〗】]")
MARK = re.compile(r"⟦J\d+⟧")

def main():
    fixed = 0
    for path in sorted(TEXT.glob("[0-9][0-9][0-9].json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        if item.get("jin_notes") or not item.get("paragraphs"):
            continue
        raw = "\n\n".join(item["paragraphs"])
        if not NOTES.search(raw):
            continue
        notes = []

        def repl(match):
            value = match.group(1).strip()
            head = re.match(r"^\s*(总批|眉批|夹批|金批)\s*[:：]\s*([\s\S]*)", value)
            name = head.group(1) if head else "夹批"
            text = head.group(2).strip() if head else value
            index = len(notes)
            notes.append({"id": index, "kind": name, "text": text})
            return f"⟦J{index}⟧"

        clean = NOTES.sub(repl, raw)
        item["paragraphs"] = [s.strip() for s in clean.split("\n\n") if s.strip()]
        item["jin_notes"] = notes
        item["original_characters"] = len(MARK.sub("", clean))
        path.write_text(json.dumps(item, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        fixed += 1
        print(f"Normalized {path.stem}: {len(notes)} Jin annotations")
    print(f"Fixed {fixed} cached chapters")

if __name__ == "__main__":
    main()
