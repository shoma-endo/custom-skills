---
name: meishi
description: 名刺の作成・改版・入稿データ生成。「名刺を更新して」「名刺の実績数字を変えて」「名刺を刷り直す」「/meishi」で起動。HTML正本の編集→350dpi入稿PNG/PDF生成→印刷基準の検証（文字pt・マージン・線の視認性）→ZIP梱包まで。不負責：印刷発注の実行（手順の案内のみ）、LP本体の変更。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# 名刺の作成・改版・入稿

2026-07 の名刺全面刷新（アクセア入稿・実発注まで完走）で確立した再現手順。

## 正本

- ソース: `~/dev/ai-support-lp/meishi/`
  - `print-front.html` / `print-back.html` — デザイン正本（写真・QRはbase64インライン）
  - `pdf-front.html` / `pdf-back.html` — PDF化ラッパー（生成済みPNGを参照）
  - `build.sh` — PNG再生成スクリプト
- 出力先: `~/Downloads/meishi-print/`（PNG・PDF・meishi-nyuko.zip）
- 記録: memory `lp-line-funnel.md` に発注履歴あり

## 寸法の数理（これだけ守れば再現できる）

- 仕上がり **91×55mm**、塗り足し3mm込みで **97×61mm**
- 設計座標: 600×363px + 塗り足し20px = **640×403px**（1mm = 6.593px）
- `body{zoom:2.0932}` + Chrome headless `--screenshot --window-size=1340,844` → 97×61mm @ ~350dpi
- PDF: ラッパーHTMLに `@page{size:97mm 61mm;margin:0}` + `--print-to-pdf`（MediaBox 275×173pt になれば正）

## 再生成手順

```bash
# 1. print-front/back.html を編集（実績数字・文言・スタイル）
~/dev/ai-support-lp/meishi/build.sh   # 2. PNG再生成
# 3. PDF再生成
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for side in front back; do
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$HOME/Downloads/meishi-print/meishi-$side-97x61mm-bleed.pdf" \
    "file://$HOME/dev/ai-support-lp/meishi/pdf-$side.html"
done
# 4. ZIP梱包
cd ~/Downloads/meishi-print && rm -f meishi-nyuko.zip && \
  zip -jq meishi-nyuko.zip meishi-front-97x61mm-bleed.pdf meishi-back-97x61mm-bleed.pdf
```

## 印刷基準チェックリスト（編集のたびに全部通す）

**文字サイズ** — 換算: `pt = 設計px / 2.326`

| 要素 | 最小 |
|---|---|
| 氏名 | 12pt（28px） |
| 肩書 | 7pt（16px） |
| 本文・連絡先 | 6pt（14px） |
| 補足キャプション | 5.8pt（13.5px）まで許容（ゴシック・高コントラスト前提） |

**線・色（印刷で消える系）**
- 暗地の装飾線: 2px・不透明度17%以上（1px/8%は印刷で消えた実績）
- 白地の枠線: 2px以上・#94a3b8程度の濃さ（1px薄灰は消える）
- シアン #22d3ee はCMYKでやや沈む（誤差レベル、許容）
- 書体はヒラギノ角ゴ ProN で確定（LP・発信と同系。明朝/丸ゴはトンマナ違い）

**レイアウト**
- 文字はトリム線から **3mm以上** 内側（PILで実測。目視は信用しない）
- 文言変更のたびに折り返しチェック（「進呈→呈」孤立などの破綻が頻発した）
- ピルバッジとカーブのクリアランス 2mm以上

**検証ループ**: build → 出力PNGをReadで目視 → PIL実測（venv: セッションscratchpadに qrenv があれば流用、なければ `python3 -m venv` + pillow）→ 数値で合格を確認してからコミット

## 検証スクリプトの型（PIL）

```python
# トリム線からのマージン実測。px_mm = 1340/97, trim = 3*px_mm
# 明度閾値で文字行を検出し (top-trim)/px_mm >= 3.0 を確認
# 要素間クリアランスは色条件（シアン/紺の判定関数）で境界を走査
```

## デザイン原則（変更時に崩さないこと）

- **表=宣言、裏=立証**。表: 肩書ピル→名前→メニュー3行（成約3層対応）→「すべて現役エンジニアが直接担当」→アイコン連絡先。裏: コピー→実績3点→QR2つ
- 表の濃紺×方眼グリッド×ピルバッジは **LPヒーローと同調**（媒体間の反復）。LP側を変えたら名刺も追随
- QRは公式LINEが主役（緑太枠・大）、LP用は補助（`/meishi` リダイレクト経由で流入計測）
- 実績数字（顧問社数等）は変わる前提。刷り直しはHTML編集→再生成で数分

## 発注（アクセア実績: 2026-07-17 大宮駅西口店）

- **店頭受け取りが最速最安**: 正午受付→当日15時〜、20時受付→翌朝8時〜。名刺100枚
- ACCEA EXPRESS（429円キャンペーン）は**WEB入稿システムと別会員**。EXPRESS未登録なら WEB入稿（webupload.accea.co.jp、Google連携）で自由記述注文: 仕様=両面カラー/マットポスト220kg/100枚/91×55mm塗り足し込み、店頭払い
- 入稿後に**店へ電話**して受け取り時刻を固めるのが納期の保険
- 受け取り時にQR2つをスマホで実読チェック
- ブラウザ自動化で入稿する場合、ファイル選択だけは本人操作（LNA制限でJS注入不可）

## 次版の宿題（更新時に検討）

- 正面カメラ目線の写真撮り直し（名刺・LP・X・note共通資産）
- GrowMate多社展開後のツール命名→裏面の商品カード化
- Lステップ等導入時は名刺専用の流入経路QRを次ロットで
