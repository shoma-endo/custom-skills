# DADS Markdown の読み順

`dads-markdown/` はサイト全体の変換物だ。必要なページだけ開く。各ファイル先頭の `source_url` が公式ページ。

## 最初に（ほぼ毎回）

| 目的 | ファイル |
| --- | --- |
| 利用条件・出典 | [introduction/notices/index.md](dads-markdown/introduction/notices/index.md) |
| 色・コントラスト・機能色 | [foundations/color/index.md](dads-markdown/foundations/color/index.md) |
| 文字サイズ・太さ・行間 | [foundations/typography/index.md](dads-markdown/foundations/typography/index.md) |
| 余白の考え方 | [foundations/spacing/index.md](dads-markdown/foundations/spacing/index.md) |

業務コンソールや一覧 UI では typography の「管理画面向け行間（120% / 130%）」節を優先して読む。

## レイアウトを決めるとき

| 目的 | ファイル |
| --- | --- |
| 段組み・読み順 | [foundations/layout/index.md](dads-markdown/foundations/layout/index.md) |
| 角丸 | [foundations/corner-shapes/index.md](dads-markdown/foundations/corner-shapes/index.md) |
| 影・高さ | [foundations/elevation/index.md](dads-markdown/foundations/elevation/index.md) |
| スタイルガイドの作り方 | [guidance/style-guides/index.md](dads-markdown/guidance/style-guides/index.md) |

## コンポーネント（使うものだけ）

一覧は [components/index.md](dads-markdown/components/index.md)。頻出のみ下記。

| 用途 | ファイル |
| --- | --- |
| 状態・分類ラベル | [components/chip-label/index.md](dads-markdown/components/chip-label/index.md) |
| ユーザー付与タグ | [components/chip-tag/index.md](dads-markdown/components/chip-tag/index.md) |
| 通知 | [components/notification-banner/index.md](dads-markdown/components/notification-banner/index.md) |
| 緊急告知 | [components/emergency-banner/index.md](dads-markdown/components/emergency-banner/index.md) |
| ボタン | [components/button/index.md](dads-markdown/components/button/index.md) |
| テキスト入力 | [components/input-text/index.md](dads-markdown/components/input-text/index.md) |
| テーブル | [components/table/index.md](dads-markdown/components/table/index.md) |
| 見出し | [components/heading/index.md](dads-markdown/components/heading/index.md) |
| ディスクロージャー | [components/disclosure/index.md](dads-markdown/components/disclosure/index.md) |

## 触らなくてよいもの（このスキルの既定）

- `updates/`（変更履歴の追従作業でない限り）
- `webaccessibility/` の結果一覧ページ（プロジェクトの適合宣言作業でない限り）
- 使わないコンポーネントの全文書
