---
name: minutes-to-visual
description: Larkビデオ会議（minutes URL）の文字起こしを取得し、図解画像・Larkスライド・Lark Docsまとめのいずれかに視覚化する。「この会議を図解して」「会議内容をスライドにして」「minutesをDocsにまとめて」「/minutes-to-visual」で起動。不負責：議事録のVaultノート化・タスク照合（meeting-followup）、議事録の定期自動生成（com.shoma.auto-meeting-workflow）、スライド・Docs単体の編集（lark-slides / lark-doc）。
allowed-tools:
  - Read
  - Write
  - Bash(lark-cli minutes:*)
  - Bash(lark-cli vc:*)
  - Bash(lark-cli drive:*)
  - Bash(lark-cli api:*)
  - Bash(date:*)
  - Bash(npx -y @mermaid-js/mermaid-cli:*)
---

# 会議の視覚化スキル（Lark minutes → 図解 / スライド / Docs）

会議の文字起こしは長くて読み返されない。決定事項・構造・流れを**1枚で頭に入る形**に変換する。

## 実行ポリシー

- 出力形態はユーザーの指示から判断する。指示が曖昧なら聞くのではなく**図解を既定**とし、他形態も1行で案内する
- **文字起こしにない情報を推測で足さない**。不明な固有名詞・数字は「(不明)」と明記
- すべて日本語で出力する（原文が他言語でも翻訳する）
- 中間ファイル（transcript・Mermaidソース等）はセッションのスクラッチパッドに置く。`/tmp` 直書きしない

## Step 1: 文字起こしの取得

minutes URL（`…/minutes/<token>`）から token を取り、**lark-minutes スキル（`~/.agents/skills/lark-minutes/SKILL.md`）の手順に従って**文字起こしを取得する（コマンド詳細はスキル側が正。ここに転記しない）。

- 目安: `lark-cli minutes +detail --minute-tokens <token> --as user` 系で発話テキストを取得
- VC の URL（meeting）しか無い場合は `lark-cli vc +detail --meeting-ids` で `minute_token` を引いてから同様に
- 取得できない場合（403・権限）はその旨と対処（会議オーナーへの共有依頼等）を報告して終了

## Step 2: 内容の構造化

文字起こしから以下を抽出してから視覚化に入る（いきなり描かない）:

- テーマと結論（3行以内）
- 登場人物と役割
- 話の流れ（フェーズ分け）
- 決定事項 / 未決事項 / 宿題（担当付き）
- 出てきた数字・固有名詞（サービス名・金額・期日）

## Step 3: 出力形態別の生成

### A. 図解画像（既定）

1. Step 2 の構造を図の文法に落とす: 流れ→フローチャート、関係→相関図、階層→マインドマップ、収益・ファネル→ファネル図
2. 実行環境に画像生成手段があればそれを使う。無い場合（Claude Code 等）は **Mermaid ソースを書き `npx -y @mermaid-js/mermaid-cli` でSVG/PNG化**する（project-catchup と同じ方式・1コマンド1呼び出し）
3. ノード内の文言は文字起こしの言葉を使い、1ノード1メッセージに保つ

### B. Lark スライド

**lark-slides スキル（`~/.agents/skills/lark-slides/SKILL.md`）の手順に従って**作成する。構成の既定: 表紙（テーマ・日付・参加者）→ 結論 → 流れ（1フェーズ1枚）→ 決定事項・宿題 → 補足。文章は要点のみ、1枚に3ポイントまで。

### C. Lark Docs まとめ

**lark-doc スキル（`~/.agents/skills/lark-doc/SKILL.md`）の手順に従って** Docs を作成し、Step 3-A の図も配置する。構成: 結論 → 決定事項・宿題（表）→ 流れの図解 → 詳細メモ。

## Step 4: 報告

- 生成物の場所（ローカルパス or Lark URL）
- 「(不明)」として残した箇所の一覧
- 未決事項・宿題のうち期日が無いものの指摘（あれば）
