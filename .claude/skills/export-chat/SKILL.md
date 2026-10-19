---
name: export-chat
description: このリポジトリでの Claude Code の会話を chat-exports/ へ Markdown で書き出す。利用者がチャットの書き出し、会話ログの保存、chat-exports への出力を頼んだときに使う。
---

# チャットの書き出し

会話本文の変換はスクリプトで行う。手で Markdown を組み立てない。

## 手順

1. リポジトリ直下で次を実行する。引数を省くと、このリポジトリの会話記録のうち最後に更新されたもの（いまのセッション）を書き出す。

```bash
python3 .claude/skills/export-chat/scripts/export_chat.py
```

別のセッションを書き出すときは `--transcript ~/.claude/projects/<作業ディレクトリ名>/<セッション ID>.jsonl` を渡す。

2. 標準出力に出たパスを、書き出したファイルとして利用者に伝える。
3. 頼まれない限りコミットしない。

## 出力

`chat-exports/YYYY-MM-DD-HHMM/chat.md` に書く。時刻は、最初のユーザー発言の日本時間である。同じフォルダがあれば `chat.md` を置き換える。ツールの呼び出しと結果、思考は含めず、ユーザーとアシスタントの本文だけを書く。

`chat-exports/` はログであり、アプリの資産ではない。実装や仕様の根拠にしない。
