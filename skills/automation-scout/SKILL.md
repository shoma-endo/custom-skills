---
name: automation-scout
description: Claude Code / Codex / Cursor の直近チャット履歴から反復パターンを抽出し、スキル化・taktワークフロー化・launchdジョブ化すべき候補を推奨度付きで提案する。「自動化候補探して」「スキル化した方がいいものある？」「/automation-scout」で起動。提案のみでファイルは作らない。不負責：スキルの実作成（skill-creator）、公開スキルの検索（find-skills）、週次の活動振り返り（weekly-report）。
disallowed-tools: AskUserQuestion
allowed-tools:
  - Bash(date:*)
  - Bash(python3:*)
  - Read
---

# 自動化候補スカウト

直近の AI エージェント履歴（Claude Code / Codex / Cursor）を横断分析し、「毎回手で指示している反復作業」を見つけて恒久化の形態を提案する。

## 実行ポリシー

- 全 Step を中断せず一気通貫で実行し、ユーザーに質問しない
- **read-only**: 提案を出力するだけ。スキル・ワークフロー・plist の実ファイルは作らない（採用されたら skill-creator 等で別途作成）
- 取得に失敗したソースは「取得失敗」と記して他を続行する

## Step 1: 期間の決定

デフォルトは直近30日。タスク指示に期間があればそれに従う。

```bash
date -v-30d +%Y-%m-%d
```

## Step 2: 3ツールの履歴抽出

**weekly-report スキル（`~/.claude/skills/weekly-report/SKILL.md`）の Step 4 スクリプトをそのまま流用する**（Read で読み、`{START}` に Step 1 の日付を入れて実行。ここに転記しない — 抽出ロジックの正は weekly-report 側）。

出力が多い場合（目安1,000行超）は、まず全体を流し読みして頻出テーマを掴み、テーマごとに代表例を拾う。全行の逐語分析はしない。

## Step 3: 既存資産のインベントリ

**既にあるものを提案しない**ための照合リストを作る:

```bash
python3 -c "
import os, glob, re
def desc_of(p):
    try:
        head = open(p, encoding='utf-8').read(2000)
        m = re.search(r'^description:\s*[\"\\']?(.{0,120})', head, re.M)
        return m.group(1).strip() if m else ''
    except Exception:
        return ''
print('== skills (.agents 実体) ==')
for d in sorted(glob.glob(os.path.expanduser('~/.agents/skills/*/SKILL.md'))):
    print(os.path.basename(os.path.dirname(d)), '|', desc_of(d)[:100])
print('== skills (.claude 実体のみ・リンク除外) ==')
for d in sorted(glob.glob(os.path.expanduser('~/.claude/skills/*'))):
    if os.path.islink(d) or not os.path.isdir(d):
        continue
    print(os.path.basename(d), '|', desc_of(os.path.join(d, 'SKILL.md'))[:100])
print('== takt workflows ==')
for f in sorted(glob.glob(os.path.expanduser('~/.takt/workflows/*.yaml'))):
    print(os.path.basename(f), '|', desc_of(f)[:100])
print('== launchd ==')
for f in sorted(glob.glob(os.path.expanduser('~/Library/LaunchAgents/*.plist'))):
    print(os.path.basename(f).replace('.plist', ''))
"
```

## Step 4: 反復パターンの抽出と選別

履歴から候補を拾う基準:

- **頻度**: 同じ意図の依頼が期間内に**3回以上**（文言でなく意図で束ねる。`[claude]`/`[codex]`/`[cursor]` をまたいだ反復は特に強いシグナル）
- **多段指示の反復**: 毎回同じ手順書きのような長い指示を打っている
- **除外**: 既存資産（Step 3）で既にカバーされているもの、一過性のプロジェクト作業（[[feedback_no_hardcoded_projects]] と同じ理由で、特定案件に固有の作業は恒久化しない）、自動ジョブ自身のプロンプト（朝刊・週次レポート等の定期実行文言）

## Step 5: 形態の判定と提案出力

| 形態 | 選ぶ条件 |
|------|---------|
| **skill** | 対話の中で呼び出す再利用手順・知識・書式。単発完結 |
| **takt workflow** | 複数ステップ＋役割分担（生成→レビュー等）＋成果物契約が要る |
| **launchd ジョブ** | 人が起動する必要がない定時・イベント駆動の無人処理 |

推奨度: ⭐⭐⭐⭐⭐=今週作るべき（頻度高×手間大） / ⭐⭐⭐=作れば効くがタイミング調整可 / ⭐=様子見（頻度が閾値ぎりぎり・一過性の疑い）。

出力フォーマット（Markdownのみ、前置き不要）:

```markdown
# 自動化候補提案 YYYY-MM-DD（対象: 直近N日）

## 候補1: <候補名> ⭐⭐⭐⭐⭐
- **形態**: skill | takt workflow | launchd
- **根拠**: 期間内N回。実例:
  - 「<実プロンプト引用（80字以内）>」[claude]
  - 「<実プロンプト引用>」[cursor]
- **既存資産との関係**: なし / <近いもの>との違い1行
- **下書き**: skill なら frontmatter の name/description 案、takt なら steps 骨子、launchd ならスケジュールとコマンド案（3〜6行）

（推奨度の高い順に最大7件。3件未満しか無ければ無理に埋めず「候補が少ない＝現状の資産化は十分」と明記）

## 見送り（惜しいが提案しないもの）
- <パターン> — <理由（頻度不足・既存でカバー・一過性）>
```
