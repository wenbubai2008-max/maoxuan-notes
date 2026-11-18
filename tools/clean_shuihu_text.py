#!/usr/bin/env python3
"""Remove Wikisource license-template tails, never prose or genuine commentary.

Used by both corpus builders and as a one-off repair for stored JSON chapters.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_BAD = (
    re.compile(r"^(?:此(?:明朝|清朝|古代)?(?:作品|著作)|本作品)(?:在全世界)?(?:都)?属于公有领域(?:[，,：:\s]|$)"),
    re.compile(r"^(?:Public\s*domain\s*)+(?:(?:false|true)\s*)*$", re.I),
    re.compile(r"^(?:(?:false|true)\s*){2,}$", re.I),
    re.compile(r"^(?:PD-old|PD-China|CC0|copyright status|版权状态)(?:\s+\w+)*$", re.I),
)
_MARKER = re.compile(r"⟦J\d+⟧")

def is_footer(text: str) -> bool:
    text = re.sub(r"\s+", " ", str(text).replace("\ufeff", "").replace("\u200b", "")).strip()
    return not text or any(p.search(text) for p in _BAD)

def trim_paragraphs(paragraphs: list[str]) -> list[str]:
    kept = list(paragraphs)
    # Only remove trailing source metadata. Never remove "且听下回分解",
    # verse endings, or historical comments such as "李卓吾曰".
    while kept and is_footer(kept[-1]):
        kept.pop()
    return kept

def clean_record(data: dict) -> tuple[dict, int]:
    original = data.get("paragraphs")
    if not isinstance(original, list):
        return data, 0
    cleaned = trim_paragraphs(original)
    removed = len(original) - len(cleaned)
    if not removed:
        return data, 0
    data["paragraphs"] = cleaned
    if "original_characters" in data:
        joined = "\n\n".join(cleaned)
        data["original_characters"] = len(_MARKER.sub("", joined))
    if "characters" in data:
        data["characters"] = sum(len(p) for p in cleaned)
    return data, removed

def main():
    changed = 0
    removed = 0
    for edition in ["", "100", "120"]:
        directory = ROOT / "shuihu" / edition / "text" if edition else ROOT / "shuihu" / "text"
        if not directory.is_dir():
            continue
        for file in sorted(directory.glob("[0-9][0-9][0-9].json")):
            data = json.loads(file.read_text(encoding="utf-8"))
            data, count = clean_record(data)
            if count:
                file.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
                changed += 1
                removed += count
                print(f"Cleaned {file.relative_to(ROOT)}: {count} footer paragraphs")
    print(f"Done: {changed} files, {removed} trailing template paragraphs removed")

if __name__ == "__main__":
    main()
