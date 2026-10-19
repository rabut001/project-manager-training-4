# プロジェクトマネージャ 午前Ⅱ 演習

IPA が公開しているプロジェクトマネージャ試験（PM）の午前Ⅱを、1問ずつ解く静的サイトです。公開先は [https://rabut001.github.io/project-manager-training-4/](https://rabut001.github.io/project-manager-training-4/) です。

平成21年度春期から令和7年度秋期までの17回（各25問）を収録しています。問題は問題冊子から切り出した画像で表示し、ア〜エを選んで結果を確認します。解説は学習用に書いたもので、IPA の公式解説ではありません。進捗はブラウザの `localStorage` に残し、端末間の同期はしません。

参照元は、同じ形のシステムアーキテクト試験の演習（[rabut001/system-arch-training](https://github.com/rabut001/system-arch-training)）です。

## 文書

| 文書 | 内容 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | エージェント向けの作業規約（`CLAUDE.md` から読み込む） |
| [docs/spec.md](docs/spec.md) | 現行仕様の正本 |
| [docs/content-guide.md](docs/content-guide.md) | 問題文の起こし方、解説の書き方、レビューの進め方 |
| [docs/changes/](docs/changes/README.md) | 変更案件ごとの管理資料。リリース後の改修もここで管理する |

## フォルダ

| パス | 内容 |
| --- | --- |
| `exams/` | IPA の午前Ⅱの問題冊子・解答例の PDF と `manifest.json`。編集しない |
| `scripts/` | PDF の取得、問題画像の切り出しと正解の抽出、データの検証（Python） |
| `public/data/` | `index.json`、回ごとの JSON、問題画像。サイトが読む |
| `src/` | 演習サイト（Vite + React + TypeScript） |
| `docs/` | 仕様と変更案件 |
| `.devcontainer/` | 開発コンテナ（Node.js 24、Python 3.13 と uv、tesseract、GitHub CLI） |
| `.github/workflows/` | 検証と GitHub Pages への公開 |
| `.claude/` | Claude Code の設定（`git push` の確認）と、チャット書き出しのスキル |

`chat-exports/` は会話の書き出しです。サイトの素材でも、仕様の参照先でもありません。

## 開発

VS Code で「Reopen in Container」を選び、開発コンテナの中で作業します。依存関係はコンテナの作成時に入ります。

```sh
npm run dev      # 開発サーバ
npm run check    # 型検査、単体テスト、データの検証
npm run build    # dist/ へビルド（404.html も作る）
```

開発サーバは [http://localhost:5173/project-manager-training-4/](http://localhost:5173/project-manager-training-4/) です。回の演習画面は `/project-manager-training-4/<id>/`（例: `/project-manager-training-4/2025-r07-aki/`）です。

`main` へ push すると、GitHub Actions が検証・ビルドし、GitHub Pages へ載せます。サイトに載るのはアプリと `public/data/` だけで、PDF と文書は載りません。

### 問題データ

```sh
uv run scripts/fetch_exams.py [id ...]        # IPA から PDF を取得し、manifest.json を更新
uv run scripts/build_exam.py [id ...]         # 問題画像の切り出し、正解の抽出、JSON と index.json の生成
uv run scripts/build_exam.py --no-cut [id ...] # 画像はそのままで、JSON と index.json だけ作り直す
uv run scripts/validate_data.py [--complete]  # データの検証（--complete は問題文と解説の有無も見る）
```

`build_exam.py` は、既にある JSON の問題文と解説を残します。新しい回を足すときは、`scripts/exams.py` の収録表に1行足してから、上の順に実行します。続きは [docs/content-guide.md](docs/content-guide.md) に従います。

## 過去問題

独立行政法人情報処理推進機構（IPA）が公開しているプロジェクトマネージャ試験の午前Ⅱの問題冊子と解答例です。取得日は `exams/manifest.json` にあります。

出典: [過去問題 | IPA](https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html)

IPA は、公表している過去の試験問題について、法令に特別の定めがある場合を除き許諾や使用料は不要としています。著作権は放棄されていません。使用時の留意点は [試験制度に関するよくある質問](https://www.ipa.go.jp/shiken/faq.html) を確認してください。

| 期間 | 実施時期 |
| --- | --- |
| 平成21年度〜平成31年度 | 春期（平成23年度は特別試験） |
| 令和2年度 | 10月（春期は中止） |
| 令和3年度〜令和7年度 | 秋期 |

平成28年度春期の問2は、解答例で「誤りにより問題として成立しない」とされています。問題冊子にも「問2は問題誤りにつき受験者全員正解の措置済み」と付記されています。このサイトでは採点の対象外として扱います。
