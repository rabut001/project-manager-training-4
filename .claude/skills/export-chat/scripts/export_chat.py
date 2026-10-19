#!/usr/bin/env python3
"""Claude Code の会話記録（jsonl）から、ユーザーとアシスタントの本文を Markdown に書き出す。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[4]


def default_transcript() -> Path:
    slug = str(ROOT).replace("/", "-")
    folder = Path.home() / ".claude" / "projects" / slug
    candidates = sorted(folder.glob("*.jsonl"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        raise SystemExit(f"会話記録が見つかりません: {folder}")
    return candidates[-1]


def local_time(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(JST)


def messages(path: Path) -> list[tuple[str, datetime, str]]:
    rows: list[tuple[str, datetime, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if entry.get("isSidechain") or entry.get("isMeta"):
            continue
        kind = entry.get("type")
        content = (entry.get("message") or {}).get("content")
        if kind == "user" and isinstance(content, str):
            if (entry.get("origin") or {}).get("kind") not in (None, "human"):
                continue
            rows.append(("ユーザー", local_time(entry["timestamp"]), content.strip()))
        elif kind == "assistant" and isinstance(content, list):
            text = "\n\n".join(
                block["text"].strip() for block in content if block.get("type") == "text" and block["text"].strip()
            )
            if text:
                rows.append(("アシスタント", local_time(entry["timestamp"]), text))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", type=Path, help="会話記録の jsonl。省略すると最後に更新されたもの")
    args = parser.parse_args()
    path = (args.transcript or default_transcript()).expanduser()

    rows = messages(path)
    users = [row for row in rows if row[0] == "ユーザー"]
    if not users:
        raise SystemExit("ユーザーの発言がありません")
    started = users[0][1]

    parts = ["# チャット書き出し", "", f"セッション開始: {started:%Y-%m-%d %H:%M}", ""]
    for role, stamp, text in rows:
        parts += [f"## {role}", ""]
        if role == "ユーザー":
            parts += [f"*{stamp:%Y-%m-%d %H:%M}*", ""]
        parts += [text, ""]

    out = ROOT / "chat-exports" / f"{started:%Y-%m-%d-%H%M}" / "chat.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
