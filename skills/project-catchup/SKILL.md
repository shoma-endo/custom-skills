---
name: project-catchup
description: 数週間ぶりに戻るプロジェクトの全体像を「意味（MD正本）＋見せ方（ペライチHTML）」の二層で生成し、30分で開発再開できる状態を作る。「この案件キャッチアップして」「プロジェクト把握して」「オンボーディングドキュメント作って」「/project-catchup」で起動。不負責：コードの修正・リファクタ（把握のみ）、講義資料化（lecture-builder）、リポジトリ健全性の定期監視（repo-health）。
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
  - Bash(open:*)
---

# 案件キャッチアップスキル

対象リポジトリを解析し、二層のドキュメントを生成する:

| 層 | ファイル | 役割 |
|----|---------|------|
| 意味（正本） | `docs/PROJECT_OVERVIEW.md` | grep・diff・AI読み込み用の構造化された事実。**次回更新はこれだけ読めばよい** |
| 見せ方（ビュー） | `docs/project-overview.html` | 左サイドバー＋メインの6セクション（復帰・意図・人・設計・運用・穴）ダッシュボード型ペライチHTML。責務ごとに読み口を分け、初見の認知負荷を下げる。**MDから再生成可能な使い捨て**。メインPCではこれを `open` する |
| 見せ方（Artifact） | `docs/project-overview.artifact.html` | 上と同じ内容の **claude.ai Artifact 用派生**。doctype / html / head / body を持たず、`<title>` + `<style>` + 本文 + `<script>` だけ。スマホ／クラウドから見るときに Artifact として publish する（`spec-to-html` の `<slug>.artifact.html` と同じ約束） |

読者は「数週間ぶりに戻ってきた自分」。ゴールは網羅ではなく**30分で開発再開できる**こと。技術スタックの列挙ではなく、リポジトリから読み取れる**背景・目的・関係者・作成者・気づいていないボトルネックや穴**まで掴ませる。

## 設計原則（視覚化ファースト）

読者の脳リソースは有限。このスキルの成果物はドキュメントではなく**「決断しやすさ」**である:

- **形が先、文字が後**: 構造・流れ・比較・状態は図解（Mermaid SVG）・数字タイル・色・レイアウトで先に全体を掴ませ、文章は判断点に絞る。文字の羅列は読む地図であって見る地図ではない
- **色は意味にのみ使う**（装飾に使わない）: 緑=健全・解消済み ／ amber=注意・WIP・人待ち ／ 赤=危険・要対処 ／ 青=次の一手・強調・リンク。この意味論を全セクションで一貫させる — 色の一貫性が崩れた地図は嘘をつく地図より認知に悪い
- **責務で分ける**: 1セクションは1つの問いにだけ答える（復帰=今どう動く／意図=なぜある／人=誰に聞く／設計=どういう形／運用=どう回る／穴=何を見落としているか）。問いに合わない内容はそのセクションに書かず、該当セクションへ移す。MD正本の見出し順もこのサイドバーの並び順と1対1
- **レポートは事実で終わらず判断材料で終わる**: 状況把握（何が起きたか）で止めず「次の一手」まで導出する。ただし着手の判断は読者の専権 — 提案は推定と明記する
- **削る勇気込みの視覚化**: 図解・強調・タイルが増えすぎたらそれも情報過多の再発。強調は各段落1箇所まで、タイルは4〜6枚まで、次の一手は3個まで。迷ったら削る

**視覚方針（2026-09-05 改定）**: HTMLは**HeroUI 風のダッシュボード骨格 × ダーク計器**。左に固定幅（〜268px）のサイドバー（案件名＋6セクションのナビ）、右にトップバー（現在地・生成日・SHA・経過警告）＋状況ボード＋選択セクション本文を置く。紺黒〜チャコールの背景に少し明るいパネル、大きな角丸（カード本体 24px・内側の要素 14〜20px）と柔らかい多層影、広めの余白、細い境界、monoラベル・数値、insetの数字窓で区画を示す。サイドバー項目はアイコン＋ラベル＋短い説明で、ホバーは無彩色、選択は意味色の淡い塗り（通常は青、穴だけamber）。薄いグローは意味色（緑=健全／amber=注意／赤=危険／青=次の一手・強調・リンク）にだけ許可する。ネオンピンク／シアンの演出・スキャン線・ノブ／鍵盤・過剰なグラデーションやガラス表現は使わない。和文本文の明るさとAAコントラストを優先し、モーションは短い状態遷移とドロワーのスライドだけ（`prefers-reduced-motion`で無効化）。自己完結（CDN・外部フォント・React禁止。素のHTML/CSS/JSのみ）・6セクション・既存プレースホルダ・hash／キーボード操作・JS無効時の縦並びを維持し、印刷は明るい紙に戻す。

**サーフェス強度（2026-09-05 追記）**: 画面上の面は全部「一目でカードと分かる」強さを持たせる。`--surface` / `--surface-2` / `--surface-3` / `--surface-4` / `--surface-5` は明度差を広く取った1本の段（ladder）で、上に載るものほど明るい。カードは大きな角丸（`--radius-card` 24px）＋3層の柔らかい影（`--shadow`／ホバーは `--shadow-lg`）＋上端の内側ハイライトで厚みを出し、ホバーで 3px 浮いて縁が `--line-strong` に上がる（`prefers-reduced-motion` で transform だけ止める）。**カード内の行は `.row-card` プリミティブで「親の1段上」に浮かせる**: `.card` の変種が `--row` / `--row-hover` を差し替えるので、`.next-item` / `.alert` / `.discovery` / `.gap-list li` / `.person` / `.tl-item` / `.link-list li` / `.process-list li` は default・secondary・tertiary・transparent どの親の中でも正しい段に乗る（個別に背景色を書かない）。逆にへこませるのはコードブロック（`--well` ＋ inset 影）だけ。`.card--tertiary` は「次の一手」のように読者に一番効くブロックで実際に使う（CSS定義だけで終わらせない）。**並列に置くカードは同じ変種で揃える**: 左右に並ぶ2枚（例「作成者・関係者」と「役割の穴」）が別の面段だと、片方だけ浮いて見えて同じ部品群に読めない。意味色は変種ではなく帯・アイコン・薄い面で出す。**意味色の左帯は `border-left` で描かない**（角丸を食って三日月に欠け、角が硬く見える）: カードは `.card--accent` / `.card--warning` の `::after`、行は `.alert` / `.discovery` / `.gap-list li` の `::before` で、上下を詰めた `--radius-full` の丸帯を内側に置く。行の意味色の面は `--critical-soft` / `--warning-soft` / `--good-soft` / `--blue-soft`（不透明度10%上限）を `--row` の上に重ねるだけにし、`--row` を置き換えない（置き換えると親との段差が消える）。面を持たない `.card--transparent` はテンプレ本文では使わない（節はすべて実カードにする）— 変種自体は旧HTML互換のため CSS に残す。`.btn` / `.chip` / `.badge` / `.stamp` / `.delta` はピル（`--radius-full`）、`.alert` 系と行カードは `--radius` で統一する。テーブルも外周を `--radius` で囲った面として扱い、内側は横罫だけにする。

**コンポーネント方針（2026-09-05 追記）**: 部品は **HeroUI 風のカード構造**で組む（`@heroui/react` も Tailwind CDN も使わない。https://heroui.com/docs/react/components/card ほかの構造・変種名だけを vanilla CSS に写す）。テンプレの CSS に BEM のプリミティブが定義済みで、生成側はこの語彙を使う: `.card`＋`.card__header` / `.card__heading` / `.card__title` / `.card__description` / `.card__actions` / `.card__content` / `.card__footer`、変種は `.card--default` / `--secondary` / `--tertiary` / `--transparent`（＋意味色の左帯 `.card--accent`＝青 / `.card--warning`＝amber）。ほかに `.chip`（`.chip__dot` / `__label` / `__meta`、`--primary/--secondary/--tertiary/--soft` × `--default/--accent/--success/--warning/--danger` × `--sm/--lg`）、`.badge`（同じ色変種＋分類用の `.badge--outline`）、`.btn`（`--primary/--secondary/--tertiary/--outline/--ghost` × `--sm/--lg` × `--icon-only`）、`.avatar`（`.avatar__image` / `.avatar__fallback`、`--sm/--lg/--soft`）、`.divider`、`.alert`（`.alert__indicator` / `__content` / `__meta` / `__title` / `__description`、`--default/--accent/--success/--warning/--danger`）、そして**カード内の1行を浮かせる `.row-card`**（`.next-item` などが同じ見た目を共有する）。**階層の原則**: 見出しは `card__header` の中だけに置き、節の凡例は `card__description` に書く（本文の頭で説明し直さない）。色変種は意味色ルールに従い、装飾目的で色付き変種を選ばない。BEM化前に生成された HTML を壊さないため、旧クラス（`.discovery` / `.sev-pill` / `.kind-pill` / `.pill` / `.gap-list` / `.expand-btn` / `.chip .dot` / `.chip .ver` / `.stat-tile .num` / `.stat-tile .cap`）は互換エイリアスとして CSS に残してある — 消さない。

## 実行方針（確認プロンプトを発生させない）

このスキルは `allowed-tools`（Read / Write / Edit / 下記の narrow な Bash 許可リスト）だけで完走できるように設計されている。ユーザー確認が挟まると自動走行が止まるため、以下を徹底する:

- **Bashコマンドは1コマンド1呼び出し**。`&&` `;` `|` で他コマンドと連結しない（連結すると許可パターンにマッチせず確認が発生しうる）
- 一時ファイル（Mermaidソース等）は **Write ツールで直接書く**。heredocやシェルリダイレクトを使わない
- プレースホルダ置換・テキスト加工は **Read の内容を自分で組み立てて Write/Edit する**。`python3` `node` 等の外部インタプリタを呼び出さない
- 一時ファイルの置き場所は `/tmp` ではなくセッションのスクラッチパッドディレクトリを使う（`/tmp` 直書きは許可リスト外の挙動を誘発しやすい）

## Step 1: 事実収集（推測禁止）

以下を**1本ずつ**実行する（連結しない）:

```bash
git log --oneline -20
git branch -a
git remote -v
git status --short
ls docs/
ls .github/workflows/
```

- 読む優先順: README → CLAUDE.md / AGENTS.md → docs/ 配下 → 主要エントリポイント
- **マニフェスト自動検出**（Node決め打ちにしない）: `package.json` / `requirements.txt` / `pyproject.toml` / `go.mod` / `composer.json` / `Gemfile` / `appsscript.json` / `Cargo.toml` のうち存在するものを読む
- デプロイ・運用の痕跡: `vercel.json` / `Dockerfile` / `launchd` 参照 / CI workflow / `.env.sample`（**`.env.local` 等の実env は読まない**）
- 直近の状態: 現在ブランチ・未コミット変更・直近コミットの流れから「やりかけの作業」を推定（推定と明記する）

### セクション別の追加収集（意図・人・穴）

技術スタック中心にならないよう、以下を**セクションの責務ごとに**集める。どれも読めなければ TBD にし、創作しない。

**意図（背景・目的・誰のための何）**

- README の冒頭・「背景」「目的」「Motivation」節、CLAUDE.md / AGENTS.md のプロジェクト説明、`docs/` の要件・ADR・企画メモ
- コミットメッセージ本文の「なぜ」（件名だけでなく body を読む。1本で実行）:

```bash
git log --format="%h %ad %s%n%b" --date=short -30
```

- 「誰のための何か」が README に無い場合は、UI文言・ドメイン語彙（モデル名・画面名）から受益者を推定し「推定」と付ける

**人（作成者・関係者・役割の穴）**

```bash
git shortlog -sne --all
```

```bash
git log --format="%an %ad" --date=short -1
```

- `CODEOWNERS`（`.github/CODEOWNERS` / `CODEOWNERS` / `docs/CODEOWNERS`）、マニフェストの `author` / `maintainers`、README・docs の担当・連絡先記述
- 役割の穴の観点（該当する事実があるときだけ書く。各項に出典）:
  - 単一人依存: コミット比率が概ね80%以上の人が1人しかいない
  - レビュアー不在: PR/レビューの痕跡（CODEOWNERS・workflow の required reviewers）が無い
  - デプロイ権限者不明: デプロイ手順はあるが誰が実行できるか docs に無い
  - 離脱の疑い: 主要 Author の最終コミットが長期間前（目安90日以上）

**穴（ボトルネック・矛盾・TBD・未配線・デッドパス）**

```bash
grep -rln -E "TODO|FIXME|HACK|XXX" --include=*.ts --include=*.tsx --include=*.js --include=*.py --include=*.go --include=*.rb --include=*.php --include=*.rs --include=*.md .
```

- docs↔コードの矛盾: README に書かれたコマンドが scripts に無い、docs が参照するファイル・ディレクトリが存在しない、docs の構成図とコードの依存方向が食い違う
- 未配線: `.env.sample` に定義された変数がコードで参照されていない／逆にコードが参照する変数が sample に無い。定義されているが呼ばれないエンドポイント・モジュール・feature flag
- デッドパス: 参照されない workflow・スクリプト、無効化（`if: false`・コメントアウト）された CI job、消えたブランチ向けの設定
- ボトルネック: テスト・CI が無い／手動デプロイのみ／単一人依存（人と重複する場合は人に書き、穴からは参照）
- 直近の状態から見える TBD: WIP ブランチ、未コミット変更、`git status` に出る未追跡ファイル

### 前回キャッチアップとの差分（既存の docs/PROJECT_OVERVIEW.md がある場合のみ）

「数週間ぶりに戻った読者」が一番知りたいのは前回から何が変わったか。既存MDの frontmatter が比較アンカーになる:

1. Read で既存 `docs/PROJECT_OVERVIEW.md` の frontmatter から前回の `generated` と `commit` を控える
2. 以下を**1本ずつ**実行する（連結しない）:

```bash
git log --oneline <前回commit>..HEAD
```

```bash
git diff --stat <前回commit>..HEAD
```

- 前回SHAが履歴に無くコマンドが失敗する場合（rebase・shallow clone等）は「比較不能（前回SHAが履歴に見つからない）」として扱い、止まらず続行する
- 初回（既存MDなし）はスキップし「初回キャッチアップ（比較基準なし）」として扱う

## Step 2: MD正本の生成 `docs/PROJECT_OVERVIEW.md`

構成（この順で固定。見出し順はHTMLのサイドバーの並び順と1対1）:

```markdown
---
generated: YYYY-MM-DD
commit: <生成時点の HEAD SHA 短縮形>
generator: project-catchup
---

# <プロジェクト名> 全体像

## 30秒サマリー（何のためのリポジトリか・今どういう状態か）
## 前回キャッチアップからの変化（前回: YYYY-MM-DD / <SHA短縮形>。コミット数・変更ファイル数と、git log の傾向から主な変更を1〜3行で要約。推定には「推定」と付ける。初回は「初回キャッチアップ（比較基準なし）」、SHA不明なら「比較不能」とだけ書く）
## 再開手順（コマンドは定義元を確認したもののみ。出典: package.json scripts 等。主要ステップは`# 1. 環境変数`のように`# N. ラベル`の番号コメントを付ける。Step 4で番号コメントの生存確認に使う）
## 次の一手（提案。1〜3個・優先順。各項は「アクション1行＋根拠1行（出典: 直近の状態・穴・やりかけ等）」。全て推定であり着手判断は読者が行う旨を末尾に1行）
## 意図（背景・目的・対象読者／受益者）
### 背景（何が困っていて、このリポジトリが生まれたか。出典: README / docs / コミット本文）
### 目的（何を達成したいか。「〜できる状態」の形で）
### 対象読者・受益者（誰が使い、誰が得をするか。推定なら明記）
## 人と役割（作成者・関係者・役割の穴／欠員）
### 作成者・関係者（git shortlog の Author、CODEOWNERS、README・docs の担当記述。役割不明は TBD）
### 役割の穴（単一人依存・レビュアー不在・デプロイ権限者不明・離脱の疑い。事実があるものだけ、各項に出典。無ければ「検出なし」）
## 構成図（Mermaid コードブロック3種。該当しないものは理由付きで省略可）
### 構造・依存関係（graph/flowchart）
### 主要インターフェース（graph＋ラベル付きエッジ。抽象と実装の関係。API面明示が必要な場合のみclassDiagram）
### データ関係（erDiagram。DB/主要エンティティがある場合は必須）
## 開発・運用プロセスと技術スタック
### 開発・運用プロセス（ブランチ運用・CI/CD・デプロイ先・定期ジョブ）
### 技術スタック（検出したマニフェストの主要依存のみ。全列挙しない）
## 直近の状態とやりかけ（ブランチ・WIP・未解決課題。推定には「推定」と付ける）
## 穴・発見事項（1件＝「種類｜深刻度｜内容｜証拠 file:line」。種類は ボトルネック／矛盾／TBD／未配線／デッドパス のいずれか。証拠の無い指摘は書かない）
## 関連リンク（リポジトリ内 docs・外部URL。無ければ「なし」）
```

各節の冒頭に「（HTML: ○○）」と1行添えてよい（任意）。MD↔サイドバー項目の対応:

| MD節 | HTMLセクション |
|------|---------|
| 30秒サマリー／前回キャッチアップからの変化／再開手順／次の一手 | 復帰 `resume` |
| 意図 | 意図 `intent` |
| 人と役割 | 人 `people` |
| 構成図 | 設計 `design` |
| 開発・運用プロセスと技術スタック | 運用 `ops` |
| 直近の状態とやりかけ／穴・発見事項 | 穴 `gaps` |
| 関連リンク | セクション外（末尾に常時表示） |

構成図の3観点（読者が「これ1枚で頭に入る」ことが目的。網羅よりも代表的な関係を選ぶ）:

| 観点 | 何を描くか | 描かない場合 |
|------|-----------|-------------|
| 構造・依存関係 | 主要コンポーネント（画面/API/外部サービス/DB/主要ライブラリ層）とその依存の向き | 単一ファイル・単一機能の極小リポジトリは省略可 |
| 主要インターフェース | 抽象と実装の関係（例: `interface X` を複数の実装が満たす、プラグイン/アダプタパターン、DSL型とその処理系）。**graphでラベル付きエッジ**（例: `Impl -->|implements| Interface`）を既定とする。実装のAPI面（メソッド/プロパティ）を明示する必要がある場合のみclassDiagram（`<<interface>>` 表記）を例外的に使う | コードにインターフェース/抽象層が存在しない場合は省略し「抽象層なし」と明記 |
| データ関係 | 主要エンティティとリレーション（外部キー・所有関係） | DB/永続化がないツールは省略し「永続化なし」と明記 |

- 各図は**出典**（例: `prisma/schema.prisma`、`lib/adapters/types.ts`）を図の直下に1行添える
- 3図とも既存の設計ドキュメント内に相当図があればそれを出典付きで再利用・要約する（車輪の再発明をしない）。無ければコードから新規に起こす
- 主要インターフェース図でclassDiagramを避ける理由: UML矢印（`..|>`実現／`--|>`継承）は凡例なしのSVGでは読者に意味を推測させ、図1（構造・依存関係）のgraphと視覚文法が食い違う。graph＋ラベル付きエッジなら矢印の意味がテキストで明示され、many-to-many（1実装が複数インターフェースを満たす等）も自然に描ける（2026-07-05に決定）

主要インターフェース図・データ関係図は、各ノード/エンティティに日本語1行の説明を付ける（構造・依存関係図は既にノード内に役割/パスを書いているため対象外）。図単体で「これが何か」が読めることが目的（2026-07-05に決定）。

- **説明文は出典付きの事実から書く**。コード中のコメント/docstring（例: `interface`宣言直上の`//`、Prismaモデル直上の`///`）を根拠にする。コメントがない場合はフィールド構成から要約し、創作しない
- 埋め込み方法（図の種類ごとに構文が違う）:
  - graphの各ノード: ラベルの最終行に説明を追加（`\n`で改行）。例: `OutputAdapter["OutputAdapter&lt;TConfig&gt;\nwrite(table, config): WriteResult\n出力先ごとの書き込み処理を共通化するインターフェース"]`
  - erDiagramの各エンティティ: 属性ブロックに`note`型の1行を追加。例:
    ```
    User {
      note 概要 "ログインユーザー。Organizationに所属し各種データを保有"
    }
    ```
- **肥大化した場合は埋め込まず表に分離**する。目安: 対象の図（ノード/エンティティ数）が12以下なら埋め込み、13以上、または埋め込むと図が縦に間延びして「これ1枚で頭に入る」を損なう場合は、図はノード名のみ（説明なし）に留め、図の直下にMarkdown表を添える:
  ```markdown
  | ノード/エンティティ | 説明 |
  |---|---|
  | User | ログインユーザー。Organizationに所属し各種データを保有 |
  ```

ルール:
- **事実に出典を付ける**（`README.md`、`git log`、`package.json` 等）。ドキュメントとコードが矛盾したら**コードを正**とし、矛盾を「穴・発見事項」に種類=矛盾で記載
- 不明は創作せず `TBD` と書く
- 記載する再開コマンドは定義（scripts等）の存在を確認する。**dev server起動やデプロイ等の副作用があるコマンドは実行せず記載のみ**
- 既存の `docs/PROJECT_OVERVIEW.md` がある場合は上書きでなく差分更新（frontmatter の generated / commit を更新）。旧構成（「案件の概要」「登場人物と役割」「発見事項」「技術スタック」が独立節）のMDは、この節構成に**並べ替え・改名して**更新する（内容は捨てない）
- 日本語のみで書く

## Step 3: Mermaid図の事前レンダリング

HTML用にSVG化する（HTMLにJSライブラリを埋め込まない。オフライン自己完結＆軽量のため）。**MDに書いた3種の図それぞれ**に対して行う:

1. Write ツールで各図のMermaidソースをセッションのスクラッチパッドディレクトリに書く（例: `structure.mmd` / `interface.mmd` / `erd.mmd`）
2. 図ごとに **1コマンド1呼び出し**でSVG化する（他コマンドと連結しない）:

```bash
npx -y @mermaid-js/mermaid-cli -i structure.mmd -o structure.svg -b transparent
```

```bash
npx -y @mermaid-js/mermaid-cli -i interface.mmd -o interface.svg -b transparent
```

```bash
npx -y @mermaid-js/mermaid-cli -i erd.mmd -o erd.svg -b transparent
```

3. 生成された `.svg` は Read ツールで読み込み、Step 4 のHTML埋め込みに**そのまま**使う。特にer図は`<defs>`内のマーカー定義（`er-onlyOne`/`er-zeroOrMore`等、カーディナリティを示す線端の図形）がSVGの本体。CSSや`<defs>`を手で間引くとこれらのマーカーが消え、「1対多」「1対1」の情報が図から失われる（2026-07-05: 実際にこの欠落が発生し気付かれた）。

### er図の生成後チェック（自動・1コマンド）

散文ルールだけに頼らず、カーディナリティマーカーが生成SVGに実在するかを機械的に確認する（HTML埋め込み前に実行）:

```bash
grep -c -E "er-onlyOne|er-zeroOrMore|er-zeroOrOne|er-oneOrMore" erd.svg
```

- 1以上（exit 0）ならマーカーはSVG内に存在し、埋め込んでよい
- 0件（exit 1）はマーカー欠落。再レンダリングするか、CSS/`<defs>`を手で間引いていないか確認して再生成する

図ごとに失敗してよい（1図の失敗で他を止めない）。失敗した図はHTMLに入れず「この図はMD参照」と書いて完走する（止まらない）。省略した観点（インターフェース抽象なし・永続化なし等）はSVG生成自体をスキップし、HTML側にもその旨を1行書く。

**失敗時、原因を推測で書かない**（2026-08-17: 実際に「macOS sandboxのChrome headless権限エラー」という未検証の原因文がHTMLに書かれ、後日の再現テストでは同一コマンドが問題なく成功した実例あり）。npxコマンドの標準出力・標準エラーは切り捨てず、失敗した図の直下に実際のエラーメッセージの末尾数行をそのまま引用する（「この図はMD参照（生成失敗、エラー: `<実際のstderr末尾>`）」の形）。原因の特定・説明はしない — 症状の事実だけを記録し、原因究明は次回の人間またはエージェントに委ねる。

## Step 4: ペライチHTML生成 `docs/project-overview.html`

`templates/overview.html` を Read で読み込み、プレースホルダをMD正本の内容で直接置き換えて Write する（**外部インタプリタを使わず、自分でテキストを組み立てる**）。

### 見せ方の設計（サイドバー・6セクション責務分離）

骨格は**左サイドバー＋メイン**のダッシュボード。サイドバーには案件名（`h1.title`）と6セクションのナビ（`.nav-item[role=tab]`）が入り、デスクトップでは `position:sticky` で貼り付く。メイン側は上から sticky なトップバー（ハンバーガー・現在地・生成日／SHA・経過警告・読了バー）、タグライン＋状況ボード（数字タイル）、選択セクション本文、関連リンク、フッターの順。タグライン・状況ボード・関連リンク・フッターは**セクション外に常時表示**。

| セクションID | ラベル | 責務（このセクションが答える問い） | 埋めるプレースホルダ |
|--------|--------|------|------|
| `resume` | 復帰 | 今どう動けばよいか。30秒サマリー・前回差・再開手順・次の一手 | `{{SUMMARY_HTML}}` `{{SINCE_LAST_HTML}}` `{{RESUME_HTML}}` `{{NEXT_HTML}}` |
| `intent` | 意図 | なぜあるのか。背景・目的・誰のための何 | `{{INTENT_HTML}}` |
| `people` | 人 | 誰に聞けばよいか。作成者・関係者・役割の穴 | `{{PEOPLE_HTML}}` `{{ROLE_GAPS_HTML}}` |
| `design` | 設計 | どういう形か。構造・IF・データの3図 | `{{DIAGRAM_*_SVG}}` `{{DIAGRAM_*_SRC}}` |
| `ops` | 運用 | どう回っているか。ブランチ・CI・デプロイ・定期ジョブ＋技術スタック | `{{PROCESS_HTML}}` `{{STACK_HTML}}` |
| `gaps` | 穴 | 何を見落としているか。やりかけ・ボトルネック・矛盾・TBD・未配線 | `{{RECENT_HTML}}` `{{DISCOVERY_HTML}}` |

- 6セクションは固定。該当内容が無いセクションも消さず、中身に「該当なし（理由）」を書く（項目が減ると読者は「見落としたのか無いのか」を判断できない）
- 「技術スタック」は独立セクションにせず運用側にチップで置く。技術の話は設計（形）と運用（回し方）に分散させ、意図・人・穴には持ち込まない
- セクション切替は素のJS（外部CDN・React・Tailwind CDNなし）。クリックと ↑↓ ←→ Home End キーで切り替わる。選択セクションは URL hash に保存され（`#gaps` 等）、リロード・共有で復元される。hash がセクション内ブロックのID（`#recent` `#since-last` `#discovery`）なら、含まれるセクションを開いてからそのブロックへスクロールする — 状況ボードのタイルはこの仕組みで別セクションへ飛ぶ
- 狭幅（〜900px）ではサイドバーはドロワーになり、トップバーのハンバーガー（`#nav-toggle`）で開閉する。スクリム（`#scrim`）クリック・Esc・項目選択で閉じ、メインは全幅になる
- JS無効・印刷時は全セクションが縦に並び、サイドバーのナビは畳んで案件名だけ残す（`hidden` を外す処理が走らない／`noscript` と印刷CSSで解除）ので、劣化しても読める

**方針転換の記録（レイアウト）**: 2026-09-05 にユーザー指示で**上部の横タブバーを廃止し、HeroUI 風の左サイドバー＋メインのダッシュボード**へ移行した。理由は、6項目のラベル＋責務説明が横一列では狭幅で潰れて横スクロール頼みになり、「どのセクションを今見ているか」と「他に何があるか」が同時に見えなかったため。縦のサイドバーなら6項目すべてが常時見え、各項目に短い説明を添えられる。責務分離・hash ルーティング・プレースホルダは横タブ時代のものをそのまま引き継ぐ。

**方針転換の記録（タブ導入）**: 2026-07-05 に「タブ切替は使わない（MDと代り映えしない見せ方を避けるため、縦スクロール1本道の現場復帰レポート）」と決めていたが、2026-09-05 にユーザー指示で**タブを再導入**した。理由は責務分離 — 「今どう動くか（復帰）」と「なぜあるか（意図）」「誰に聞くか（人）」「何を見落としているか（穴）」は読む動機が異なり、1本道に並べると復帰に不要な情報が再開の邪魔をし、逆に穴・意図が末尾に埋もれて読まれなかった。縦1本道の良さ（読み順の強制）は各セクション内の順序と復帰の先頭配置で残す。

### プレースホルダの埋め方

- `{{PROJECT_NAME}}` / `{{SHA}}`: プロジェクト名（README の見出し or ディレクトリ名）と HEAD SHA 短縮形
- `{{DATE}}`: `YYYY-MM-DD` 固定。テンプレのJSが `data-date` からこの資料の経過日数を閲覧時に計算し、14日以上で「再生成推奨」の警告を出す
- `{{TAGLINE}}`: 30秒サマリーから1文だけ抜き出したキャッチコピー（ヒーロー帯に大きく出す）
- `{{STATBOARD_HTML}}`: トップバー直下の状況ボード。1タイル＝小さな HeroUI Card で、Header（ラベル）→ Content（数値）の順に書く: `<a class="stat-tile ok" href="#recent"><span class="stat-tile__label">最終コミットから</span><span class="stat-tile__value mono">3日</span></a>`（数字は `.stat-tile__value` に単位ごと入れる。例: `3日` `+23` `2件`。意味色の `ok` / `warn` / `crit` はラベル先頭のドットとラベル色になる。旧 `.num` / `.cap` も、旧来の数値→ラベル順のまま同じ見た目で動く）。クリックで該当ブロックへ飛ぶページ内アンカー（別セクション内でもJSがそのセクションを開いて飛ぶ）。出すタイル（該当しないものは出さない・4〜6枚）:
  - 最終コミットからの日数 → `href="#recent"`（穴）。31日以上は `warn`、それ未満は `ok`
  - 未コミット変更 N件 → `href="#recent"`（穴）。0件は `ok`、1件以上は `warn`
  - 前回比コミット +N → `href="#since-last"`（復帰）。初回・比較不能時は出さない
  - 穴・発見事項 N件 → `href="#discovery"`（穴）。sev-critical があれば `crit`、warning のみは `warn`、それ以外は `ok`
  - 役割の穴 N件 → `href="#people"`（人）。1件以上のときだけ出し `warn`
  - TBD N件 → ジャンプ先が定まらないため `<span class="stat-tile warn">`（`<a>` にしない。↓印はリンクにのみ付く）。0件なら出さない
- `{{SUMMARY_HTML}}`（復帰）: MDの「30秒サマリー」節をそのまま段落化する。ヒーローの`{{TAGLINE}}`と重複する冒頭文は省いてよいが、要約や言い換えはしない
- `{{SINCE_LAST_HTML}}`（復帰）: Step 1 の前回差分から組み立てる。`<p class="since-note">前回: <b>YYYY-MM-DD</b>（commit <code>abc1234</code>）</p>` ＋ `<div class="delta-row"><span class="delta">コミット <b>+23</b></span><span class="delta">変更 <b>47ファイル</b></span></div>` ＋ MDの「前回キャッチアップからの変化」節の要約文をそのまま段落化。初回は `<p class="since-note">初回キャッチアップ（比較基準なし）。次回の再生成からここに前回比が表示される。</p>` のみ
- `{{RESUME_HTML}}`（復帰）: MDの「再開手順」のbashコードブロックを**コメントを含めて逐語転記**する。手順番号コメント（`# 1. 環境変数` `# 2. DBマイグレーション`等）は読者が「今どのステップか」を追う唯一の手がかりなので、要約・整形の過程で間引かない（2026-07-05: 実際にこの番号コメントが転記時に消え、手順が読みにくくなる欠落が発生した）。`<pre class="mono"><code>`の直後は必ず改行してからコード本文を書く（開始タグと同じ行にコードの1行目を続けない。全行を行頭からのgrepで検出可能にするため）
- `{{NEXT_HTML}}`（復帰）: MDの「次の一手」を1項目＝`<div class="next-item"><span class="n">1</span><div><span class="act">アクション1行</span><span class="why">根拠: 出典付き1行</span></div></div>` として優先順に並べる（最大3個）。導出できる材料が無ければ `<p class="since-note">提案なし（直近の状態に判断材料が不足）</p>` と正直に書く — 創作しない
- `{{INTENT_HTML}}`（意図）: MDの「意図」節を `<h3>背景</h3>` `<h3>目的</h3>` `<h3>対象読者・受益者</h3>` の3見出し＋段落で組む。段落ごとに**最も見落としてはいけない一文**を `<span class="key">...</span>` で囲む（青・太字・やや大きめ）。強調は各段落1箇所まで。「出典:」等の脚注は強調しない。推定した箇所は文末に「（推定）」を残す
- `{{PEOPLE_HTML}}`（人）: 各人物を `.person` 行として組み立てる。`<div class="person"><span class="avatar"><span class="avatar__fallback">頭文字</span></span><div class="person-body"><div class="person-name">名前 <span class="badge badge--outline">役割</span></div><div class="person-meta">コミット N件・最終 YYYY-MM-DD・出典</div><div class="share-bar"><div class="share-fill" style="width:NN%"></div></div></div></div>`。`.share-fill` の `width` はコミット数の比率(%)。役割不明は `<span class="badge badge--outline">TBD</span>`
- `{{ROLE_GAPS_HTML}}`（人）: MDの「役割の穴」を1件＝amber の Alert にする。`<div class="alert alert--warning"><span class="alert__indicator"><svg class="icon"><use href="#i-warn"/></svg></span><div class="alert__content"><p class="alert__title">単一人依存</p><p class="alert__description">根拠: コミット 92% が1人（出典: git shortlog）</p></div></div>`。検出なしなら `<p class="since-note">役割の穴は検出なし（出典: git shortlog / CODEOWNERS）</p>`
- `{{DIAGRAM_STRUCTURE_SVG}}` / `{{DIAGRAM_INTERFACE_SVG}}` / `{{DIAGRAM_ERD_SVG}}`（設計）: Step 3 で生成したSVGを**そのまま**（mermaid-cli出力の`style="max-width: ###px"`を書き換えず自然な幅のまま）埋め込む。インライン表示はCSSの`max-height:560px`で高さを抑えるが、各図面には拡大ボタン（クリックでライトボックス表示・原寸に近い1400px幅でスクロール可）が付いているため、インライン側を無理に大きくする必要はない（DWG-01/02/03の図面番号は既にテンプレ側で固定表示。省略する場合は `.card__content.sheet-body` の中身を `<p class="sheet-omitted">この観点は該当なし（理由）</p>` に差し替える）
- `{{DIAGRAM_STRUCTURE_SRC}}` / `{{DIAGRAM_INTERFACE_SRC}}` / `{{DIAGRAM_ERD_SRC}}`（設計）: 各図の出典1行（例: `出典: prisma/schema.prisma`）
- `{{PROCESS_HTML}}`（運用）: `<ul class="process-list">` に1項目＝`<li><svg class="icon"><use href="#i-branch"/></svg><div>ブランチ運用: main 直push（出典: git log）</div></li>`。ブランチ運用・CI・デプロイ先・定期ジョブの順。無いものは「なし（出典）」と書く
- `{{STACK_HTML}}`（運用）: 技術ごとに `<span class="chip chip--secondary"><span class="chip__dot"></span><span class="chip__label">Next.js</span><span class="chip__meta">15.1</span></span>`（名前は `.chip__label`、バージョンは `.chip__meta`）。色は付けない（技術名は状態ではないので `chip--secondary` 固定）
- `{{RECENT_HTML}}`（穴）: `.tl-item` を新しい順に並べる。最新コミットは `class="tl-item now"`、未コミット変更やWIPは `class="tl-item flag"`（amber表示）。`.tl-date` は絶対日付＋相対を併記する（例: `2026-06-28（8日前）`。相対は生成時点で計算して焼き込む）
- `{{DISCOVERY_HTML}}`（穴）: 発見事項1件＝Alert 1つ。`<div class="alert alert--warning"><span class="alert__indicator"><svg class="icon"><use href="#i-warn"/></svg></span><div class="alert__content"><div class="alert__meta"><span class="badge badge--warning badge--mono">注意</span><span class="badge badge--outline">矛盾</span></div><p class="alert__title">本文1行</p><p class="alert__description">証拠: README.md:42 / package.json scripts</p></div></div>`。深刻度で `alert--danger`＋`badge--danger`(赤・要対処) / `alert--warning`＋`badge--warning`(amber・注意) / `alert--success`＋`badge--success`(緑・解消済み) / `alert--default`＋`badge--default`(灰・中立) を選ぶ。種類（ボトルネック／矛盾／TBD／未配線／デッドパス）は色を持たない `badge--outline` で、テンプレの凡例と同じ語を使う。証拠（file:line等）は `.alert__description` に必須
- `{{LINKS_HTML}}`（セクション外）: `<li><svg class="icon"><use href="#i-link"/></svg><a href="...">ラベル</a></li>`。無ければ `<li>なし</li>`
- 単一ファイル・外部依存ゼロ（CDN・外部フォント・外部画像なし。SVGはインライン埋め込み、アイコンはテンプレ冒頭の `<symbol>` スプライトを`<use>`で参照）
- テンプレの構造（サイドバー・トップバー・パネル・カードの `card__*` 階層・`data-tab-panel`・ブロックの `id`）は変更しない。変更するのはプレースホルダの中身だけ
- HTMLは使い捨てなので手編集しない前提。直したくなったらMDを直して再生成

### 再開手順の逐語性チェック（自動・2コマンド）

散文ルールだけに頼らず、番号コメントがHTMLでも生存しているかを機械的に確認する（それぞれ1コマンドで実行し、件数を見比べる）:

```bash
grep -c "^# [0-9]" docs/PROJECT_OVERVIEW.md
```

```bash
grep -c "^# [0-9]" docs/project-overview.html
```

- 両方の件数が**一致すればOK**。番号コメントが全て転記されている
- HTML側の件数がMD側より少なければ転記時に間引かれている。`{{RESUME_HTML}}`を該当箇所から逐語で書き直す

### 生成後の自己完結性チェック（自動・1コマンド）

散文ルールだけに頼らず、外部依存が紛れ込んでいないか機械的に確認する:

```bash
grep -nE '<script[^>]*\ssrc=|<link[^>]*stylesheet|@import|<img[^>]*src=.{0,3}(https?:|//)|fetch\(|XMLHttpRequest|WebSocket|cdn\.|googleapis\.com|jsdelivr|unpkg\.com' docs/project-overview.html
```

- ノーヒット（exit 1）なら自己完結性OK。`関連リンク`セクション等の`<a href>`テキストリンクはこの条件式に含まれないため誤検知しない
- ヒットした場合（exit 0）は該当行が実際に外部リソース読み込みを起こしている。インライン化するか記載を削って再生成し、再度ノーヒットになるまで繰り返す

### プレースホルダ残存チェック（自動・1コマンド）

散文ルールだけに頼らず、置換漏れを機械的に確認する:

```bash
grep -c '{{' docs/project-overview.html
```

- 0件（exit 1）なら全プレースホルダが置換済み
- ヒットした場合（exit 0）は置換漏れ。「該当なし」のタイル・図は空文字ではなく規約どおりの差し替え文にした上で、`{{` が消えるまで再生成する

### セクション整合チェック（自動・1コマンド）

6セクションが揃っているか（置換時にパネルを壊していないか）を機械的に確認する:

```bash
grep -c 'data-tab-panel=' docs/project-overview.html
```

- **6件**ならOK（resume / intent / people / design / ops / gaps の各パネルが1つずつ）
- 6件以外ならテンプレ構造を崩している。`templates/overview.html` を再読して、プレースホルダの中身だけを差し替え直す

### Artifact 版の同時生成 `docs/project-overview.artifact.html`

claude.ai の Artifact は publish 時に `<!doctype html>…<head></head><body>` を被せる。完結 HTML（`docs/project-overview.html`）をそのまま渡すと文書が二重になるため、**同じ内容から Artifact 版を必ず同時に書く**（`spec-to-html` / `scripts/spec-html.py` と同じ約束）。

手順（完結 HTML の Write と自己完結性・プレースホルダ・セクション整合チェックの**あと**）:

1. `docs/project-overview.html` を Read する
2. 次だけを残した派生を組み立て、`docs/project-overview.artifact.html` に Write する:
   - `<title>…</title>`（完結 HTML の `<title>` と同じ文言）
   - `<style>…</style>`（`<head>` 内のスタイルブロックをそのまま）
   - 本文（完結 HTML の `<body>…</body>` の**中身だけ**。サイドバー・メイン・ライトボックス・インライン SVG・末尾の `<script>…</script>` を含む）
3. Artifact 版に次のタグが**1つも残っていない**ことを確認する（残っていたら変換ミス）:

```bash
grep -niE '<!doctype|<html|</html>|<head>|</head>|<body|</body>' docs/project-overview.artifact.html
```

- ノーヒット（exit 1）ならOK
- ヒットしたら組み立て直す。`<html>` や `<body>` を残したまま publish しない

4. 自己完結性チェックを Artifact 版にも同じ正規表現で再実行する（両方ノーヒットになるまで）:

```bash
grep -nE '<script[^>]*\ssrc=|<link[^>]*stylesheet|@import|<img[^>]*src=.{0,3}(https?:|//)|fetch\(|XMLHttpRequest|WebSocket|cdn\.|googleapis\.com|jsdelivr|unpkg\.com' docs/project-overview.artifact.html
```

5. プレースホルダ残存・セクション整合も Artifact 版で確認する（`{{` が0件、`data-tab-panel=` が6件）

**閲覧の使い分け**:
- メインPC: `open docs/project-overview.html`（完結 HTML）
- スマホ／クラウド: `docs/project-overview.artifact.html` を Claude Artifact として publish（デフォルト非公開）。概要を更新して再生成したら、**同じファイルパスで再 publish**すれば同じ URL が更新される（新しい URL にはならない）

## Step 5: 台帳への反映（存在する場合のみ）

`~/dev/projects.yaml` が存在すれば、該当プロジェクトのエントリ（説明・スタック・状態・overview パス）を更新する。無ければスキップ。

## Step 6: 報告

報告も視覚化ファーストの縮図にする — 判断材料を先頭に、作業ログは後ろに:

- **冒頭に「次の一手」を1行ずつ**（読者が報告だけ読んでも動き出せるように）
- 生成した3ファイルのパス（`docs/PROJECT_OVERVIEW.md` / `docs/project-overview.html` / `docs/project-overview.artifact.html`）、`open docs/project-overview.html` の案内（穴へ直接: `open docs/project-overview.html#gaps` のように hash で開けることも添える）。スマホ／クラウド閲覧時は Artifact 版を publish する旨も1行添える
- 前回キャッチアップ比（コミット数・変更ファイル数。初回・比較不能の場合はその旨）
- 穴・発見事項のうち sev-critical と役割の穴の一覧（人・穴の要点。読者が報告だけで危険箇所を知れるように）
- TBD として残した項目の一覧（ユーザーが埋めるべき箇所）
- ドキュメントとコードの矛盾を見つけた場合はその一覧
- 自己完結性チェックの結果（完結 HTML と Artifact 版の両方。OK、またはヒットして対処した内容）
- Artifact 版のシェル禁止タグチェックの結果（`<!doctype` / `<html` / `<head>` / `<body` が残っていないか）
- 再開手順の逐語性チェックの結果（MD/HTMLの番号コメント件数が一致したか）
- プレースホルダ残存チェックの結果（完結 HTML と Artifact 版の両方で0件になったか）
- セクション整合チェックの結果（両方で `data-tab-panel=` が6件か）
- er図を生成した場合はカーディナリティマーカーチェックの結果

## 安全ルール

- 書き込みは `docs/PROJECT_OVERVIEW.md`・`docs/project-overview.html`・`docs/project-overview.artifact.html`・`~/dev/projects.yaml` のみ。コードは変更しない
- `.env*`（sample以外）・credentials・秘密鍵は読まない。収集した内容に秘密情報らしき文字列があれば記載せず警告する
- コミットはしない（ユーザーの指示があれば行う）
