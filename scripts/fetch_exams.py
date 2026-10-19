#!/usr/bin/env python3
"""IPA の過去問題ページから、PM 午前Ⅱの問題冊子と解答例を exams/<id>/ に取得する。"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import date

from exams import EXAMS, EXAMS_DIR, find_exam

BASE = "https://www.ipa.go.jp"
FILES = {"qs": "am2-mondai.pdf", "ans": "am2-kaitou.pdf"}


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="取得する回の id。省略するとすべて")
    args = parser.parse_args()
    targets = [find_exam(i) for i in args.ids] if args.ids else list(EXAMS)

    manifest_path = EXAMS_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    entries = {(e["id"], e["file"]): e for e in manifest}

    for exam in targets:
        html = get(f"{BASE}/shiken/mondai-kaiotu/{exam.page}.html").decode("utf-8")
        for kind, name in FILES.items():
            original = f"{exam.prefix}_pm_am2_{kind}.pdf"
            match = re.search(rf'href="([^"]*/{re.escape(original)})"', html)
            if not match:
                raise SystemExit(f"{exam.id}: {original} が年度ページに見つかりません")
            url = BASE + match.group(1)
            body = get(url)
            if not body.startswith(b"%PDF"):
                raise SystemExit(f"{exam.id}: {url} が PDF ではありません")
            out = EXAMS_DIR / exam.id / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(body)
            entries[(exam.id, name)] = {
                "id": exam.id,
                "title": exam.title,
                "file": name,
                "url": url,
                "original": original,
                "bytes": len(body),
                "fetched": date.today().isoformat(),
            }
            print(f"{exam.id}/{name} {len(body):,} bytes")

    order = {exam.id: i for i, exam in enumerate(EXAMS)}
    rows = sorted(entries.values(), key=lambda e: (order[e["id"]], e["file"]))
    manifest_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
