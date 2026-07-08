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
| 見せ方（ビュー） | `docs/project-overview.html` | タブ切替のペライチHTML。初見の認知負荷を下げる読み口。**MDから再生成可能な使い捨て** |

読者は「数週間ぶりに戻ってきた自分」。ゴールは網羅ではなく**30分で開発再開できる**こと。

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

構成（この順で固定）:

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
## 案件の概要（目的・背景・現状）
## 登場人物と役割（git log の Author、README・docs から。不明は TBD）
## 構成図（Mermaid コードブロック3種。該当しないものは理由付きで省略可）
### 構造・依存関係（graph/flowchart）
### 主要インターフェース（graph＋ラベル付きエッジ。抽象と実装の関係。API面明示が必要な場合のみclassDiagram）
### データ関係（erDiagram。DB/主要エンティティがある場合は必須）
## 開発・運用プロセス（ブランチ運用・CI/CD・デプロイ先・定期ジョブ）
## 技術スタック（検出したマニフェストの主要依存のみ。全列挙しない）
## 直近の状態とやりかけ（ブランチ・WIP・未解決課題。推定には「推定」と付ける）
## 関連リンク（リポジトリ内 docs・外部URL。無ければ「なし」）
```

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
- **事実に出典を付ける**（`README.md`、`git log`、`package.json` 等）。ドキュメントとコードが矛盾したら**コードを正**とし、矛盾を明記
- 不明は創作せず `TBD` と書く
- 記載する再開コマンドは定義（scripts等）の存在を確認する。**dev server起動やデプロイ等の副作用があるコマンドは実行せず記載のみ**
- 既存の `docs/PROJECT_OVERVIEW.md` がある場合は上書きでなく差分更新（frontmatter の generated / commit を更新）
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

## Step 4: ペライチHTML生成 `docs/project-overview.html`

`templates/overview.html` を Read で読み込み、プレースホルダをMD正本の内容で直接置き換えて Write する（**外部インタプリタを使わず、自分でテキストを組み立てる**）。

デザインコンセプトは「現場復帰レポート（Field Return Report）」— 数週間ぶりに現場へ戻る調査員が、状況ボード→30秒サマリー→再開手順→関係者→設計図面（構造・インターフェース・データ）→運用ログ→現場メモの順に読み進める、縦スクロール1本道の構成。**タブ切り替えは使わない**（MDと代り映えしない見せ方を避けるため2026-07-05に廃止）。

プレースホルダを埋める際の要点:

- `{{DATE}}`: `YYYY-MM-DD` 固定。テンプレのJSが `data-date` からこの資料の経過日数を閲覧時に計算し、14日以上で「再生成推奨」の警告を出す
- `{{TAGLINE}}`: 30秒サマリーから1文だけ抜き出したキャッチコピー（ヒーロー帯に大きく出す）
- `{{STATBOARD_HTML}}`: ヒーロー直下の状況ボード。1タイル＝`<a class="stat-tile ok" href="#recent"><span class="num mono">3日</span><span class="cap">最終コミットから</span></a>`（数字は `.num` に単位ごと入れる。例: `3日` `+23` `2件`）。クリックで該当セクションへ飛ぶページ内アンカー。出すタイル（該当しないものは出さない・4〜6枚）:
  - 最終コミットからの日数 → `href="#recent"`。31日以上は `warn`、それ未満は `ok`
  - 未コミット変更 N件 → `href="#recent"`。0件は `ok`、1件以上は `warn`
  - 前回比コミット +N → `href="#since-last"`。初回・比較不能時は出さない
  - 発見事項 N件 → `href="#recent"`。sev-critical があれば `crit`、warning のみは `warn`、それ以外は `ok`
  - TBD N件 → ジャンプ先が定まらないため `<span class="stat-tile warn">`（`<a>` にしない。↓印はリンクにのみ付く）。0件なら出さない
- `{{SINCE_LAST_HTML}}`: Step 1 の前回差分から組み立てる。`<p class="since-note">前回: <b>YYYY-MM-DD</b>（commit <code>abc1234</code>）</p>` ＋ `<div class="delta-row"><span class="delta">コミット <b>+23</b></span><span class="delta">変更 <b>47ファイル</b></span></div>` ＋ MDの「前回キャッチアップからの変化」節の要約文をそのまま段落化。初回は `<p class="since-note">初回キャッチアップ（比較基準なし）。次回の再生成からここに前回比が表示される。</p>` のみ
- `{{SUMMARY_HTML}}`: MDの「30秒サマリー」節をそのまま段落化する。ヒーローの`{{TAGLINE}}`と重複する冒頭文は省いてよいが、要約や言い換えはしない
- `{{RESUME_HTML}}`: MDの「再開手順」のbashコードブロックを**コメントを含めて逐語転記**する。手順番号コメント（`# 1. 環境変数` `# 2. DBマイグレーション`等）は読者が「今どのステップか」を追う唯一の手がかりなので、要約・整形の過程で間引かない（2026-07-05: 実際にこの番号コメントが転記時に消え、手順が読みにくくなる欠落が発生した）。`<pre class="mono"><code>`の直後は必ず改行してからコード本文を書く（開始タグと同じ行にコードの1行目を続けない。全行を行頭からのgrepで検出可能にするため）
- `{{OVERVIEW_HTML}}`: 段落ごとに**最も見落としてはいけない一文**を `<span class="key">...</span>` で囲む（青・太字・やや大きめ）。強調は各段落1箇所まで（多用すると効かなくなる）。「出典:」等の脚注は強調しない
- `{{PEOPLE_HTML}}`: 各人物を `.person` 行として組み立てる。アバター円には名前の頭文字、`.share-bar > .share-fill` の `width` にコミット数の比率(%)を入れて可視化する。役割不明は `<span class="pill">TBD</span>`
- `{{DIAGRAM_STRUCTURE_SVG}}` / `{{DIAGRAM_INTERFACE_SVG}}` / `{{DIAGRAM_ERD_SVG}}`: Step 3 で生成したSVGを**そのまま**（mermaid-cli出力の`style="max-width: ###px"`を書き換えず自然な幅のまま）埋め込む。インライン表示はCSSの`max-height:560px`で高さを抑えるが、各図面には拡大ボタン（クリックでライトボックス表示・原寸に近い1400px幅でスクロール可）が付いているため、インライン側を無理に大きくする必要はない（DWG-01/02/03の図面番号・出典は既にテンプレ側で固定表示。省略する場合は `.sheet-body` の中身を `<p class="sheet-omitted">この観点は該当なし（理由）</p>` に差し替える）
- `{{RECENT_HTML}}`: `.tl-item` を新しい順に並べる。最新コミットは `class="tl-item now"`、未コミット変更やWIPは `class="tl-item flag"`（amber表示）。`.tl-date` は絶対日付＋相対を併記する（例: `2026-06-28（8日前）`。相対は生成時点で計算して焼き込む）
- `{{DISCOVERY_HTML}}`: 発見事項1件＝`.discovery` カード1つ。深刻度で `sev-critical`(赤) / `sev-warning`(amber) / `sev-good`(緑・解消済み) / 指定なし(灰・neutral) をclassに付け、`.sev-pill`にも同じ接尾辞を付けて確度・深刻度ラベルを表示する。証拠（file:line等）は `.evidence` に
- `{{STACK_HTML}}`: 技術ごとに `.chip` 1つ（名前＋`.ver`にバージョン）
- 単一ファイル・外部依存ゼロ（CDN・外部フォント・外部画像なし。SVGはインライン埋め込み、アイコンはテンプレ冒頭の `<symbol>` スプライトを`<use>`で参照）
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

## Step 5: 台帳への反映（存在する場合のみ）

`~/dev/projects.yaml` が存在すれば、該当プロジェクトのエントリ（説明・スタック・状態・overview パス）を更新する。無ければスキップ。

## Step 6: 報告

- 生成した2ファイルのパス、`open docs/project-overview.html` の案内
- 前回キャッチアップ比（コミット数・変更ファイル数。初回・比較不能の場合はその旨）
- TBD として残した項目の一覧（ユーザーが埋めるべき箇所）
- ドキュメントとコードの矛盾を見つけた場合はその一覧
- 自己完結性チェックの結果（OK、またはヒットして対処した内容）
- 再開手順の逐語性チェックの結果（MD/HTMLの番号コメント件数が一致したか）
- プレースホルダ残存チェックの結果（0件になったか）
- er図を生成した場合はカーディナリティマーカーチェックの結果

## 安全ルール

- 書き込みは `docs/PROJECT_OVERVIEW.md`・`docs/project-overview.html`・`~/dev/projects.yaml` のみ。コードは変更しない
- `.env*`（sample以外）・credentials・秘密鍵は読まない。収集した内容に秘密情報らしき文字列があれば記載せず警告する
- コミットはしない（ユーザーの指示があれば行う）
