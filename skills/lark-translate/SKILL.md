---
name: lark-translate
version: 1.0.0
description: "Lark機械翻訳API：テキスト翻訳（zh/ja/en ほか16言語）と言語自動判定。「これ翻訳して」「中国語の記事を日本語に」「何語か判定して」、収集した中国語・英語コンテンツの日本語化、固有名詞の対訳（glossary）を固定した翻訳が必要なときに使用。不負責：ドキュメント全体の取得（lark-doc）、翻訳結果のメッセージ送信（lark-im）。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark 機械翻訳

> **前置条件：** 先に [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md) を読むこと。

## コマンド

```bash
# テキスト翻訳（例: 中国語→日本語）
lark-cli api POST /open-apis/translation/v1/text/translate \
  --data '{"source_language":"zh","target_language":"ja","text":"<原文>"}' \
  --as bot

# 言語判定（source_language が不明なとき先に実行）
lark-cli api POST /open-apis/translation/v1/text/detect \
  --data '{"text":"<テキスト>"}' --as bot
# → data.language が ISO 639-1 で返る（例: "zh"）

# 多步編成: Step 1 detect → 返った language を Step 2 translate の source_language に渡す
```

### glossary（固有名詞の対訳固定・最大128組）

```bash
lark-cli api POST /open-apis/translation/v1/text/translate \
  --data '{"source_language":"zh","target_language":"ja","text":"<原文>","glossary":[{"from":"多维表格","to":"Lark Base"},{"from":"智能总结","to":"AIスマート要約"}]}' \
  --as bot
```

**Lark関連の翻訳では次の既定 glossary を必ず入れる**（[[feedback-japanese-only-output]] の再発防止）:

| from | to |
|------|-----|
| 飞书多维表格 | Lark Base |
| 飞书 | Lark |
| 多维表格 | Lark Base |
| 智能总结 | AIスマート要約 |
| 妙记 | 妙記（Minutes） |
| 知识库 | Wiki |
| 云文档 | ドキュメント |

## 対応言語コード

`zh` `zh-Hant` `en` `ja` `ru` `de` `fr` `it` `pl` `th` `hi` `id` `es` `pt` `ko` `vi`

## 使用ルール

- **identity は tenant token（`--as bot`）のみ**。`--as user` は不可
- レート制限: テナントあたり 20 QPS。**実測では数回の連続呼び出しでも HTTP 429 が返ることがある** → 失敗したら数秒待って1回リトライする。バッチ翻訳は直列実行
- **同一原文はサーバ側でキャッシュされる（実測）**: 直前に glossary なしで翻訳した文を glossary ありで再翻訳しても旧結果が返ることがある。glossary の効果検証は必ず新しい文で行う
- 改行・引用符を含むテキストは JSON エスケープが必要。長文や特殊文字が多い場合は python3 で JSON を組み立てる:

```bash
python3 -c 'import json,sys; print(json.dumps({"source_language":"zh","target_language":"ja","text":sys.stdin.read()}, ensure_ascii=False))' < input.txt
```

- 長文は段落単位に分割して翻訳し、結合する（1リクエスト数KB目安）

## 権限

| 操作 | 所需 scope | identity |
|------|-----------|----------|
| translate / detect | `translation:text` | bot（tenant token） |

scope 未開通のエラー（`app_scope_not_applied`）が出た場合は、エラー内の `console_url` をそのままユーザーに提示して開発者コンソールでの開通を依頼する（bot scope なので `auth login` は実行しない）。開通が反映されるまで数分かかることがある。
