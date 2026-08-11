---
name: readme-audit
description: README・主要docsと実コードの整合を監査し、乖離を根拠ファイル付きで列挙してから承認を得て更新する。「READMEは最新？」「README監査して」「README更新して」「/readme-audit」で起動。不負責：新規参画向けの全体像ドキュメント生成（project-catchup）、READMEの新規作成。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(git status:*)
  - Bash(ls:*)
  - Bash(date:*)
---

# README 監査・更新スキル

READMEは書いた瞬間から腐り始める。このスキルは「実コードを正」として README との乖離を検出し、根拠付きで列挙 → 承認後に最小差分で更新する。

## 実行ポリシー

- **監査フェーズは read-only**。README を編集するのは乖離リストをユーザーが承認した後（最初から「更新して」と言われた場合は、乖離リスト提示→そのまま更新まで一気に進めてよい）
- 乖離には必ず**根拠ファイル（`path:line` または該当コミット）**を付ける。推測で「古そう」と書かない
- 乖離ゼロのセクションは「✓ 一致」と1行で流す（監査した事実を残す）
- 日本語で報告する

## Step 1: 対象と基準時点の特定

```bash
git log -1 --format="%ad %h %s" --date=short -- README.md
```

- 対象はリポジトリ直下の `README.md`（指示があれば docs/ 配下も追加）
- README の最終更新コミット日時を「基準時点」として控える

## Step 2: 実態の収集

READMEが言及しがちな実態ソースを読む（存在するものだけ）:

| 観点 | 実態ソース |
|------|-----------|
| 環境変数 | `src/env.ts` / `.env.example` / `process.env` 直接参照（grep） |
| セットアップ・動作確認 | `package.json` scripts / `engines` / lockファイルの有無 |
| 主な機能・構成 | `app/` `src/` `scripts/` のディレクトリ実態、主要エントリポイント |
| デプロイ・運用 | `vercel.json` / `Dockerfile` / `.github/workflows/` / launchd・cron 参照 |
| 基準時点以降の変化 | `git log --oneline --since=<基準時点> -- . ':!README.md'`（新機能・削除・改名の痕跡）。`docs/specs/` `docs/plans/` `supabase/migrations/` 等の追加も見る |
| アーキテクチャ図 | README内の図の有無・最終更新（あれば） vs 実コード構成 |

秘密情報（`.env.local` 等の実env・credentials）は読まない。

## Step 3: 突合と乖離リスト

乖離を3分類で列挙する:

```markdown
# README 監査結果（README最終更新: YYYY-MM-DD abc1234）

## 🔴 誤り（現状と矛盾 — 読者が事故る）
- <READMEの記述> → 実態: <正しい内容>（根拠: `path:line`）

## 🟡 陳腐化・不足（基準時点以降の変化が未反映）
- <新機能・変更> が未記載（根拠: コミット `abc1234` / `docs/specs/xxx.md`）
- アーキテクチャ図が無い/実態と乖離（該当する場合。根拠: 実コード構成）

## 🟢 削除候補（実態が消えたのに残っている記述）
- <記述> — 対応する実態なし（根拠: <探した場所>）

## ✓ 一致していたセクション
- <セクション名>, …
```

## Step 4: 更新（承認後）

- 乖離リストの承認された項目だけを**最小差分**で README に反映する（全面書き換えしない。文体・構成は既存に合わせる）
- ドキュメントとコードが矛盾する場合は**コードを正**とする。コード側が明らかにバグの場合のみ、その旨を報告して指示を仰ぐ
- 承認された乖離に「アーキテクチャ図の欠如/陳腐化」が含まれる場合のみ:
  1. diagram-designスキルの **architecture** タイプ（`references/type-architecture.md`）で図を生成する（初回スタイルガイドgateは「(e) デフォルトで進める」を選び作業を止めない）
  2. `references/export.md` のSVG手順で書き出す。Google Fonts `@import` 注入ステップはスキップする（GitHub上のREADME表示は外部フォント依存を持ち込まない方が安全）
  3. `docs/architecture.svg` として保存し、README該当箇所に `![Architecture](docs/architecture.svg)` を追記/差し替える
  4. 複数図・全体像ドキュメントが要る規模だと判断したら、ここでは対応せず project-catchup へ誘導する（このスキルは単一のアーキテクチャ図のみ扱う。不負責宣言のとおり全体像ドキュメント生成はproject-catchupの管轄）
- 更新後、反映した項目と見送った項目を1行ずつ報告する。アーキテクチャ図を生成した場合はそのパスも報告する
