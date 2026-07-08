# custom-skills

Claude Code / Codex / Cursor で使える自作 Agent Skills 集。

📍 **スキルカタログ（可視化マップ）**: https://shoma-endo.github.io/custom-skills/

## スキル一覧

| スキル | 用途 |
|--------|------|
| [automation-scout](skills/automation-scout/) | AIコーディングツールのチャット履歴から反復パターンを抽出し、スキル化・自動化候補を推奨度付きで提案 |
| [e2e-testcases](skills/e2e-testcases/) | リポジトリ解析にもとづく E2E テストケース設計（機能・非機能）。`docs/TEST_CASES.md` を生成 |
| [estimate](skills/estimate/) | 受託開発の見積もり（工数・金額・スケジュール・見積書）。質問シート先行、レートカードは個人設定で分離 |
| [lark-translate](skills/lark-translate/) | Lark 機械翻訳 API によるテキスト翻訳（16言語＋glossary 対訳固定）と言語自動判定 |
| [minutes-to-visual](skills/minutes-to-visual/) | Lark ビデオ会議の文字起こしを図解画像・スライド・ドキュメントに視覚化 |
| [project-catchup](skills/project-catchup/) | 久しぶりに戻るプロジェクトの全体像を「MD 正本＋ペライチ HTML」の二層で生成 |
| [readme-audit](skills/readme-audit/) | README・主要 docs と実コードの整合を監査し、乖離を根拠付きで列挙してから更新 |

## インストール

使いたいスキルを `~/.claude/skills/`（Claude Code の user スコープ）に置くだけ。

```bash
git clone https://github.com/shoma-endo/custom-skills
cp -r custom-skills/skills/<skill-name> ~/.claude/skills/<skill-name>
```

リポジトリ更新に追従したい場合はコピーでなくシンボリックリンクにする:

```bash
ln -s /path/to/custom-skills/skills/<skill-name> ~/.claude/skills/<skill-name>
```

プロジェクト単位で使う場合は `<project>/.claude/skills/` に置く。Codex / Cursor で共通利用する場合は `~/.agents/skills/` に実体を置き、各ツールから参照する構成を推奨。

### estimate の初期設定

単価・係数は個人設定ファイルで分離してある（リポジトリには含まれない）:

```bash
cd skills/estimate
cp rate-card.example.yaml rate-card.yaml   # 自分の単価に書き換える
```

## 設計方針

- **1スキル1責務**: 各スキルの description に「不負責（やらないこと）」を明記し、隣接スキルとの境界を固定する
- **個人情報・単価の焼き込み禁止**: 環境依存値は example ファイル＋ .gitignore で分離する
- **恒久資産に案件名を焼き込まない**: スキルは汎用に書き、事業・案件は実行時に参照する

## License

MIT
