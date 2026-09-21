---
name: project-catchup
description: 数週間離れたリポジトリを調査し、再開用のMD正本と閲覧用HTMLを生成する。コード修正、講義資料化、継続監視には使わない。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(git:*)
  - Bash(ls:*)
  - Bash(find:*)
  - Bash(grep:*)
  - Bash(cat:*)
  - Bash(date:*)
  - Bash(wc:*)
  - Bash(npx -y @mermaid-js/mermaid-cli:*)
  - Bash(python3 ~/.agents/skills/project-catchup/scripts/build-overview-html.py:*)
  - Bash(python3 skills/project-catchup/scripts/build-overview-html.py:*)
  - Bash(open:*)
---

# Project Catch-up

対象リポジトリの事実を集め、30分以内に開発を再開できる地図を作る。正本はMarkdown、HTMLは正本から決定論的に再生成するビューとする。

## Route the task

- 調査対象、根拠、前回差分の取り方: [references/data-collection.md](references/data-collection.md)
- MD構造、生成物、検査、報告: [references/output-contract.md](references/output-contract.md)
- HTMLの意味色、情報設計、アクセシビリティ: [references/visual-spec.md](references/visual-spec.md)
- 古い完全契約や互換性の確認が必要な場合だけ: [references/legacy-full-guide.md](references/legacy-full-guide.md)

## Workflow

1. 既存の `docs/PROJECT_OVERVIEW.md` と対象リポジトリの現在状態を確認する。
2. [data-collection.md](references/data-collection.md) に沿って、意図・人・設計・運用・やりかけ・穴の根拠を集める。
3. [output-contract.md](references/output-contract.md) の構造で `docs/PROJECT_OVERVIEW.md` を更新する。推定には必ず「推定」と付ける。
4. 必要なMermaid図をSVG化する。失敗した図だけ省略し、実エラーを記録して続行する。
5. `scripts/build-overview-html.py` で完結HTMLとArtifact版を生成し、自動検査が全て通るまでMDまたはテンプレートを直す。
6. 次の一手、重大な穴、TBD、成果物パスを報告する。

## Safety and scope

- コードは変更しない。出力は3つのoverviewファイルと、存在する場合のプロジェクト台帳だけ。
- 実 `.env`、credentials、秘密鍵を読まない。sampleだけを対象にする。
- HTMLを手で直さない。MD正本かテンプレートを直して再生成する。
- コミットは依頼された場合だけ行う。

