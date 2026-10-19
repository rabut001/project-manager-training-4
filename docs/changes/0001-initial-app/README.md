---
status: 完了
---

# 演習サイトの初期構築

## 目的

PM 午前Ⅱの17回を、問題画像と正解で1問ずつ解ける静的サイトを作り、GitHub Pages へ公開する。問題文と解説は `0002-am2-content` で作る。

## 決めたこと

- 画面と操作は、参照元（`rabut001/system-arch-training`）の演習サイトを引き継ぐ。仕様は `docs/spec.md` に書いた。
- 参照元から次の4点を改善する。
  - 広い幅では、問題画像と操作の欄を左右2列に並べる。
  - PC のキー操作（1〜4 / A〜D で選択、Enter で確認、←→ で移動）。
  - 回の一覧に、回ごとの進み具合を出す。参照元では出さないと決めていた点を変える。
  - 前後の問題画像の先読み。
- 参照元の、以前のレイアウトを測り直して問題画像の高さを戻す処理は移植しない。最初から問題画像の高さを優先する配置にする。
- リポジトリ直下を1つの Vite アプリにし、データは `public/data/` に置く。参照元にあった、`data/` を配信する独自プラグインは使わない。
- 回の一覧は `public/data/index.json` だけを読む。
- `exams/` には、午前Ⅱの問題冊子と解答例だけを置く。
- 検証として、データの検証スクリプトと、進捗の読み込みの単体テスト（Vitest）を置き、CI で実行する。
- 公開先は `https://rabut001.github.io/project-manager-training-4/` とする。

## 今回含めないもの

- 問題文（`stem`、`choices`、`visuals`）と解説（`explanation`）。空のまま公開し、`0002` で埋める。
- PWA、ダークモード。

## 触るファイル

| パス | 内容 |
| --- | --- |
| `docs/spec.md` | 現行仕様 |
| `scripts/fetch_exams.py` | IPA の年度ページから午前Ⅱの PDF を取得し、`exams/manifest.json` を書く |
| `scripts/build_exam.py` | 問題画像の切り出し、正解の抽出、回の JSON と `index.json` の生成 |
| `scripts/validate_data.py` | `public/data/` の検証 |
| `exams/` | 17回分の午前Ⅱの PDF と `manifest.json` |
| `public/data/` | `index.json`、回の JSON、問題画像 |
| `src/` | 画面 |
| `.github/workflows/deploy.yml` | 検証、ビルド、公開 |

## 手順

1. 開発コンテナ、文書、ツールの設定を置く。
2. `fetch_exams.py` で17回分の PDF を取得する。
3. `build_exam.py` で全回の問題画像と正解を作る。参照元の切り出し処理を PM の冊子で試し、うまく切れない回は調整する。全問の画像を目で見て、問の途中で切れていないことを確かめる。
4. 参照元の画面を移植し、改善の4点を入れる。
5. `npm run check` と `npm run build` が通ることを確かめる。
6. 開発サーバで利用者のレビューを受ける。
7. GitHub にリポジトリを作り、push して公開する（push の前に利用者の確認を得る）。
8. `checklist.json` を確かめる。

## 確認

`checklist.json` で確かめる。
