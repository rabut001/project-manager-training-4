# 作業規約

IPA 公開のプロジェクトマネージャ試験・午前Ⅱを1問ずつ解く静的サイトのリポジトリである。

## どこを見るか

| 知りたいこと | 正本 |
| --- | --- |
| 画面、操作、保存、データの形式、公開 | `docs/spec.md` |
| 問題文の起こし方、解説の書き方、レビュー | `docs/content-guide.md` |
| 変更案件の進め方 | `docs/changes/README.md` |
| 開発の手順、フォルダ、出典 | `README.md` |

`docs/changes/NNNN-*/` は案件ごとの記録で、現在の仕様の参照先にしない。`chat-exports/` は会話のログで、実装や仕様の根拠にしない。

## 守ること

- 画面、操作、保存、問題データ、公開のしかたを変えるときは、実装の前に `docs/changes/` に案件を作る。仕様を変えるときは、実装の前に `docs/spec.md` を更新する。
- 利用者とのやり取りと文書は日本語で書く。
- `exams/` の PDF は編集しない。
- 解説の `answer` は IPA の解答例のまま変えない。
- 解説や問題文のレビューは、作成時の会話を持たないサブエージェントに頼む（`docs/content-guide.md`）。
- `git push` は、そのたびに利用者の確認を得る。コミットは頼まれたとき、または案件の区切りで利用者に断ってから行う。

## 環境

- 開発は `.devcontainer/` の開発コンテナで行う。Node.js 24、Python 3.13（uv で管理）、GitHub CLI が入っている。
- エージェントのセッションは、開発コンテナの外（WSL2 のホスト）で動くことがある。ホストには `gh`、`node`、`uv` がなく、git の認証もない。`gh` や `git push` が要るときは、`.devcontainer/Dockerfile` のイメージで `docker run` して実行する。`~/.config/gh` に利用者のログイン情報がある。トークンは出力しない。

  ```sh
  docker build -q -t pm-training-4-dev .devcontainer   # 初回のみ
  docker run --rm -v "$PWD":/work -v "$HOME/.config/gh":/gh-config:ro -w /work -e GH_CONFIG_DIR=/gh-config \
    pm-training-4-dev bash -c 'git config --global --add safe.directory /work && gh auth setup-git && git push origin main'
  ```

  `git push` の前に利用者の確認を得る決まりは、コンテナ経由でも同じ。
- 画面は Vite + React + TypeScript。UI ライブラリとルーティングのライブラリは使わない。
- Python のスクリプトは `uv run scripts/<名前>.py` で実行する。

## よく使うコマンド

```sh
npm run dev          # 開発サーバ http://localhost:5173/project-manager-training-4/
npm run check        # 型検査、テスト、データの検証
npm run build        # dist/ へビルド
uv run scripts/validate_data.py
```
