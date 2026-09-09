#!/usr/bin/env python3
"""project-catchup: MD正本 → ペライチHTML／Artifact版 の機械生成。

`docs/PROJECT_OVERVIEW.md`（意味の正本）を `templates/overview.html`（見せ方）へ
決定論的に流し込み、`docs/project-overview.html` と `docs/project-overview.artifact.html`
を書く。LLM はこの変換に介在しない。

方針:
- 推測・要約・創作をしない。取れなかった項目は規約文（「該当なし」等）で明示する。
- 未知のプレースホルダが残ったら黙って空にせず exit 1（変換ロジックのバグとして落とす）。
- 終了前に4種の検査を必ず走らせる: プレースホルダ残存 / 外部依存 / Artifact シェル禁止タグ /
  data-tab-panel の7件（6つの問いセクション + 「増やす」）。加えて再開手順の番号コメントの
  逐語性も件数で突き合わせる。

使い方（リポジトリ根で）:
    python3 <この位置>/build-overview-html.py \
        --md docs/PROJECT_OVERVIEW.md \
        --out docs/project-overview.html \
        [--template path/to/overview.html] \
        [--svg-structure structure.svg] [--svg-interface interface.svg] [--svg-erd erd.svg] \
        [--svg-structure-src "出典: ..."] [--svg-interface-src ...] [--svg-erd-src ...] \
        [--check-only]
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import date
from pathlib import Path

# ── 節が無い／取れない場合に出す規約文（空文字で黙って落とさない） ──────────────
NA_SECTION = '<p class="since-note">この節は正本に該当なし（<code>docs/PROJECT_OVERVIEW.md</code> に追記すると次回から反映される）。</p>'
NA_SHEET = '<p class="sheet-omitted">該当なし（SVG未指定）</p>'

KINDS = ("ボトルネック", "矛盾", "TBD", "未配線", "デッドパス")

# 深刻度 → (alert 変種, badge 変種, 表示語)
SEVERITY = {
    "critical": ("danger", "danger", "要対処"),
    "danger": ("danger", "danger", "要対処"),
    "要対処": ("danger", "danger", "要対処"),
    "重大": ("danger", "danger", "要対処"),
    "warning": ("warning", "warning", "注意"),
    "warn": ("warning", "warning", "注意"),
    "注意": ("warning", "warning", "注意"),
    "good": ("success", "success", "解消済み"),
    "解消済み": ("success", "success", "解消済み"),
    "info": ("default", "default", "参考"),
}
SEVERITY_DEFAULT = ("default", "default", "参考")


# ── インライン変換 ───────────────────────────────────────────────────────────
_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
_URL_RE = re.compile(r"(?<![\"'=(])(https?://[^\s<>）」、。]+)")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def inline(text: str, key_first: bool = False) -> str:
    """MDのインライン記法を安全なHTMLへ。key_first=True なら最初の **強調** を .key にする。"""
    stash: list[str] = []

    def _stash(m: re.Match[str]) -> str:
        stash.append(m.group(1))
        return f"\x00{len(stash) - 1}\x00"

    t = _CODE_RE.sub(_stash, text)
    t = esc(t)
    t = _LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = _URL_RE.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', t)

    used = [False]

    def _bold(m: re.Match[str]) -> str:
        if key_first and not used[0]:
            used[0] = True
            return f'<span class="key">{m.group(1)}</span>'
        return f"<strong>{m.group(1)}</strong>"

    t = _BOLD_RE.sub(_bold, t)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{esc(stash[int(m.group(1))])}</code>", t)


def plain(text: str) -> str:
    """記法を落とした素のテキスト（見出し照合・チップのラベル・avatarの頭文字用）。"""
    t = _CODE_RE.sub(r"\1", text)
    t = _LINK_RE.sub(r"\1", t)
    t = _BOLD_RE.sub(r"\1", t)
    return t.replace("*", "").strip()


def _cjk(ch: str) -> bool:
    return bool(ch) and ("　" <= ch <= "ヿ" or "㐀" <= ch <= "鿿" or "＀" <= ch <= "￯")


def join_lines(lines: list[str]) -> str:
    """和文は空白を挟まず、欧文は空白で連結する（折り返しで語が潰れないように）。"""
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not out:
            out = ln
            continue
        out += "" if (_cjk(out[-1]) or _cjk(ln[:1])) else " "
        out += ln
    return out


# ── 節分割 ──────────────────────────────────────────────────────────────────
_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
_HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _heading_positions(lines: list[str]) -> list[tuple[int, int, str]]:
    heads: list[tuple[int, int, str]] = []
    in_fence = False
    for i, ln in enumerate(lines):
        if _FENCE_RE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEAD_RE.match(ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    return heads


def split_sections(lines: list[str]) -> list[dict]:
    """見出しごとに raw（下位見出しを含む全行）と body（下位見出しの手前まで）を持つ節を作る。"""
    heads = _heading_positions(lines)
    secs: list[dict] = []
    for n, (idx, level, title) in enumerate(heads):
        end = len(lines)
        for j in range(n + 1, len(heads)):
            if heads[j][1] <= level:
                end = heads[j][0]
                break
        body_end = end
        for j in range(n + 1, len(heads)):
            if heads[j][0] >= end:
                break
            body_end = heads[j][0]
            break
        secs.append(
            {
                "level": level,
                "title": title,
                "raw": lines[idx + 1 : end],
                "body": lines[idx + 1 : body_end],
            }
        )
    return secs


def norm_title(title: str) -> str:
    t = plain(title)
    for ch in ("（", "("):
        if ch in t:
            t = t.split(ch)[0]
    return t.strip()


def find(secs: list[dict], *names: str, level: int | None = None) -> dict | None:
    """見出し文言の接頭一致で節を引く（括弧付き副題は無視）。"""
    for s in secs:
        if level is not None and s["level"] != level:
            continue
        nt = norm_title(s["title"])
        if any(nt.startswith(n) for n in names):
            return s
    return None


# ── ブロック分割 ────────────────────────────────────────────────────────────
_UL_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_TSEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")


def blocks(lines: list[str]) -> list[tuple]:
    """節の本文を ('h'|'p'|'list'|'table'|'fence'|'quote', ...) の並びに落とす。"""
    out: list[tuple] = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        if _FENCE_RE.match(ln):
            lang = ln.strip().lstrip("`~").strip()
            j, buf = i + 1, []
            while j < n and not _FENCE_RE.match(lines[j]):
                buf.append(lines[j])
                j += 1
            out.append(("fence", lang, buf))
            i = j + 1
            continue
        if not ln.strip():
            i += 1
            continue
        h = _HEAD_RE.match(ln)
        if h:
            out.append(("h", len(h.group(1)), h.group(2).strip()))
            i += 1
            continue
        if ln.lstrip().startswith("|") and i + 1 < n and _TSEP_RE.match(lines[i + 1]):
            rows, j = [], i
            while j < n and lines[j].lstrip().startswith("|"):
                rows.append(lines[j].strip())
                j += 1
            header = [c.strip() for c in rows[0].strip("|").split("|")]
            body = [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]
            out.append(("table", header, body))
            i = j
            continue
        if _UL_RE.match(ln) or _OL_RE.match(ln):
            ordered = bool(_OL_RE.match(ln))
            items: list[list[str]] = []
            j = i
            while j < n:
                mu, mo = _UL_RE.match(lines[j]), _OL_RE.match(lines[j])
                if not (mu or mo):
                    break
                cur = [(mu.group(2) if mu else mo.group(3)).strip()]
                j += 1
                # 継続行（インデントされた続き。「根拠:」のような2行目を落とさない）
                while (
                    j < n
                    and lines[j].strip()
                    and lines[j][:1] in (" ", "\t")
                    and not _UL_RE.match(lines[j])
                    and not _OL_RE.match(lines[j])
                    and not _FENCE_RE.match(lines[j])
                ):
                    cur.append(lines[j].strip())
                    j += 1
                items.append(cur)
                k = j
                while k < n and not lines[k].strip():
                    k += 1
                if k < n and (_UL_RE.match(lines[k]) or _OL_RE.match(lines[k])):
                    j = k
                else:
                    break
            out.append(("list", ordered, items))
            i = j
            continue
        if ln.lstrip().startswith(">"):
            j, buf = i, []
            while j < n and lines[j].lstrip().startswith(">"):
                buf.append(lines[j].lstrip()[1:].strip())
                j += 1
            out.append(("quote", buf))
            i = j
            continue
        j, buf = i, []
        while (
            j < n
            and lines[j].strip()
            and not _HEAD_RE.match(lines[j])
            and not _FENCE_RE.match(lines[j])
            and not _UL_RE.match(lines[j])
            and not _OL_RE.match(lines[j])
            and not lines[j].lstrip().startswith("|")
            and not lines[j].lstrip().startswith(">")
        ):
            buf.append(lines[j])
            j += 1
        if buf:
            out.append(("p", join_lines(buf)))
        i = j if j > i else i + 1
    return out


# ── 汎用レンダラ（節の形が想定と違うときの安全な受け皿） ──────────────────────
def render_code(lines: list[str]) -> str:
    body = "\n".join(esc(l.rstrip()) for l in lines).strip("\n")
    # 開始タグの直後は必ず改行（全行を行頭からの grep で検出可能にするため）
    return f'<pre class="mono"><code>\n{body}\n</code></pre>'


def render_table(header: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{inline(c)}</th>" for c in header)
    trs = []
    for r in rows:
        tds = "".join(f"<td>{inline(c)}</td>" for c in r)
        trs.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


def render_prose(bs: list[tuple], key_first_para: bool = False, h_level: int = 3) -> str:
    out: list[str] = []
    for b in bs:
        if b[0] == "h":
            out.append(f"<h{h_level}>{inline(b[2])}</h{h_level}>")
        elif b[0] == "p":
            out.append(f"<p>{inline(b[1], key_first=key_first_para)}</p>")
        elif b[0] == "quote":
            out.append(f'<p class="since-note">{inline(join_lines(b[1]))}</p>')
        elif b[0] == "list":
            tag = "ol" if b[1] else "ul"
            lis = "".join(f"<li>{inline(join_lines(it))}</li>" for it in b[2])
            out.append(f"<{tag}>{lis}</{tag}>")
        elif b[0] == "table":
            out.append(render_table(b[1], b[2]))
        elif b[0] == "fence":
            out.append(render_code(b[2]))
    return "\n".join(out) if out else NA_SECTION


def first_table(bs: list[tuple]) -> tuple[list[str], list[list[str]]] | None:
    for b in bs:
        if b[0] == "table":
            return b[1], b[2]
    return None


def all_list_items(bs: list[tuple]) -> list[list[str]]:
    items: list[list[str]] = []
    for b in bs:
        if b[0] == "list":
            items.extend(b[2])
    return items


def col_index(header: list[str], *keys: str) -> int | None:
    for i, h in enumerate(header):
        hp = plain(h)
        if any(k in hp for k in keys):
            return i
    return None


# ── 各プレースホルダの組み立て ───────────────────────────────────────────────
def split_sentence(text: str) -> tuple[str, str]:
    """先頭1文と残りに分ける（和文の句点優先、無ければピリオド）。"""
    for sep in ("。", ". "):
        idx = text.find(sep)
        if idx != -1:
            return text[: idx + len(sep)].strip(), text[idx + len(sep) :].strip()
    return text.strip(), ""


def build_tagline(summary_bs: list[tuple]) -> tuple[str, str]:
    """30秒サマリー先頭文をタグラインに。(tagline, 取り除いた文) を返す。"""
    for b in summary_bs:
        if b[0] == "p":
            head, _rest = split_sentence(plain(b[1]))
            if len(head) > 120:
                return esc(head[:118].rstrip() + "…"), ""
            return esc(head), head
    return "", ""


def build_summary(summary_bs: list[tuple], drop_sentence: str) -> str:
    if not summary_bs:
        return NA_SECTION
    out: list[str] = []
    dropped = False
    key_used = False
    for b in summary_bs:
        if b[0] == "p":
            text = b[1]
            if not dropped and drop_sentence:
                head, rest = split_sentence(plain(text))
                # 先頭文がタグラインと同一で、かつ残りがあるときだけ落とす（内容は捨てない）
                if head == drop_sentence and rest:
                    idx = text.find("。")
                    if idx != -1:
                        text = text[idx + 1 :].strip()
                        dropped = True
            out.append(f"<p>{inline(text, key_first=not key_used)}</p>")
            key_used = True
        else:
            out.append(render_prose([b]))
    return "\n".join(out)


_PREV_DATE_RE = re.compile(r"前回[:：]?\s*\*{0,2}(\d{4}-\d{2}-\d{2})")
_PREV_SHA_RE = re.compile(r"commit\s*`([0-9a-fA-F]{6,40})`")
_COMMITS_RE = re.compile(r"コミット\s*\*{0,2}\+?(\d+)")
_FILES_RE = re.compile(r"(?:変更ファイル|変更)\s*\*{0,2}(\d+)")


def build_since(since_sec: dict | None) -> tuple[str, int | None]:
    if since_sec is None:
        return (
            '<p class="since-note">初回キャッチアップ（比較基準なし）。次回の再生成からここに前回比が表示される。</p>',
            None,
        )
    text = "\n".join(since_sec["raw"])
    bs = blocks(since_sec["raw"])
    m_date = _PREV_DATE_RE.search(text)
    m_sha = _PREV_SHA_RE.search(text)
    m_commits = _COMMITS_RE.search(text)
    m_files = _FILES_RE.search(text)
    plus = int(m_commits.group(1)) if m_commits else None

    if not m_date:
        # 初回・比較不能はMD本文がそう言っている。そのまま段落化する（創作しない）。
        return render_prose(bs), None

    head = f'<p class="since-note">前回: <b>{esc(m_date.group(1))}</b>'
    if m_sha:
        head += f"（commit <code>{esc(m_sha.group(1))}</code>）"
    head += "</p>"

    deltas = []
    if plus is not None:
        deltas.append(f'<span class="delta">コミット <b>+{plus}</b></span>')
    if m_files:
        deltas.append(f'<span class="delta">変更 <b>{esc(m_files.group(1))}ファイル</b></span>')
    delta_row = f'<div class="delta-row">{"".join(deltas)}</div>' if deltas else ""

    # 前回日付を含む段落は head/delta に写したので本文からは落とす（重複させない）
    rest = [b for b in bs if not (b[0] == "p" and _PREV_DATE_RE.search(b[1]))]
    body = render_prose(rest) if rest else ""
    if body == NA_SECTION:
        body = ""
    return "\n".join(x for x in (head, delta_row, body) if x), plus


def build_resume(resume_sec: dict | None) -> str:
    if resume_sec is None:
        return NA_SECTION
    return render_prose(blocks(resume_sec["raw"]))


_WHY_RE = re.compile(r"^\s*(?:根拠|理由)[:：]\s*(.*)$")


def build_next(next_sec: dict | None) -> str:
    if next_sec is None:
        return '<p class="since-note">提案なし（正本に「次の一手」節がない）</p>'
    bs = blocks(next_sec["raw"])
    items = all_list_items(bs)
    out: list[str] = []
    for k, it in enumerate(items[:3], 1):
        act = it[0]
        why_lines = []
        for extra in it[1:]:
            m = _WHY_RE.match(extra)
            why_lines.append(m.group(1) if m else extra)
        why = join_lines(why_lines)
        why_html = f'<span class="why">根拠: {inline(why)}</span>' if why else ""
        out.append(
            f'<div class="next-item"><span class="n">{k}</span>'
            f'<div><span class="act">{inline(act)}</span>{why_html}</div></div>'
        )
    if not out:
        return '<p class="since-note">提案なし（直近の状態に判断材料が不足）</p>'
    # 「いずれも推定であり…」のような末尾の但し書きは残す
    tail = [b for b in bs if b[0] == "p" and ("推定" in b[1] or "判断" in b[1])]
    if tail:
        out.append(f'<p class="since-note">{inline(tail[-1][1])}</p>')
    return "\n".join(out)


def build_intent(secs: list[dict]) -> str:
    intent = find(secs, "意図", level=2)
    if intent is not None:
        # ### 背景／目的／対象読者 は blocks() が ('h',3,...) として拾うのでそのまま h3 になる
        return render_prose(blocks(intent["raw"]), key_first_para=True)
    legacy = find(secs, "案件の概要", "概要", level=2)
    if legacy is None:
        return NA_SECTION
    return render_prose(blocks(legacy["raw"]), key_first_para=True)


def initial_of(name: str) -> str:
    n = plain(name).strip()
    return esc(n[:1]) if n else "?"


def build_people(secs: list[dict]) -> str:
    sec = find(secs, "作成者・関係者", "作成者", level=3) or find(secs, "人と役割", "登場人物", level=2)
    if sec is None:
        return NA_SECTION
    bs = blocks(sec["raw"])
    tbl = first_table(bs)
    if tbl is None:
        return render_prose(bs)
    header, rows = tbl
    i_name = col_index(header, "人物", "名前", "氏名", "Author", "担当", "メンバー") or 0
    i_role = col_index(header, "役割", "ロール", "Role")
    i_cnt = col_index(header, "コミット", "件数", "commits", "Commits")

    counts: list[int | None] = []
    for r in rows:
        c = None
        if i_cnt is not None and i_cnt < len(r):
            m = re.search(r"(\d[\d,]*)", plain(r[i_cnt]))
            if m:
                c = int(m.group(1).replace(",", ""))
        counts.append(c)
    top = max([c for c in counts if c is not None], default=0)

    out: list[str] = []
    for r, cnt in zip(rows, counts):
        if not any(cell.strip() for cell in r):
            continue
        name = r[i_name] if i_name < len(r) else ""
        role_raw = r[i_role] if i_role is not None and i_role < len(r) else ""
        role = plain(role_raw)
        meta_cells: list[str] = []
        # 役割が1行に収まらない長さならバッジにせず meta へ回す（ピルが文章になると読めない）
        if role and len(role) > 18:
            meta_cells.append(role_raw)
            role = ""
        if cnt is not None:
            meta_cells.append(f"コミット {cnt}件")
        # 名前・役割・件数以外の列（最終コミット日・根拠・出典など）は落とさず全部 meta へ
        for k, cell in enumerate(r):
            if k in (i_name, i_role, i_cnt) or not cell.strip():
                continue
            meta_cells.append(cell)
        badge = esc(role) if role else "TBD"
        bar = ""
        if cnt is not None and top > 0:
            pct = max(3, round(cnt * 100 / top))
            bar = f'<div class="share-bar"><div class="share-fill" style="width:{pct}%"></div></div>'
        meta = inline(" ・ ".join(m.strip() for m in meta_cells if m.strip()))
        out.append(
            f'<div class="person"><span class="avatar"><span class="avatar__fallback">{initial_of(name)}</span></span>'
            f'<div class="person-body"><div class="person-name">{inline(name)} '
            f'<span class="badge badge--outline">{badge}</span></div>'
            f'<div class="person-meta">{meta}</div>{bar}</div></div>'
        )
    return "\n".join(out) if out else render_prose(bs)


def warn_alert(title_html: str, desc_html: str) -> str:
    desc = f'<p class="alert__description">{desc_html}</p>' if desc_html else ""
    return (
        '<div class="alert alert--warning"><span class="alert__indicator">'
        '<svg class="icon"><use href="#i-warn"/></svg></span>'
        f'<div class="alert__content"><p class="alert__title">{title_html}</p>{desc}</div></div>'
    )


def split_bar(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[｜|]", text) if p.strip()]
    return parts


def build_role_gaps(secs: list[dict]) -> tuple[str, int]:
    sec = find(secs, "役割の穴", "役割", level=3)
    if sec is None:
        return (
            '<p class="since-note">役割の穴は正本に記載なし（<code>### 役割の穴</code> を追記すると次回から反映される）。</p>',
            0,
        )
    raw_text = "\n".join(sec["raw"])
    if re.search(r"検出なし|該当なし|なし。|問題なし", raw_text) and len(raw_text.strip()) < 200:
        return f'<p class="since-note">{inline(raw_text.strip())}</p>', 0

    bs = blocks(sec["raw"])
    out: list[str] = []
    tbl = first_table(bs)
    if tbl is not None:
        header, rows = tbl
        for r in rows:
            if not any(c.strip() for c in r):
                continue
            out.append(warn_alert(inline(r[0]), inline(" ／ ".join(c for c in r[1:] if c.strip()))))
    else:
        for it in all_list_items(bs):
            text = join_lines(it)
            parts = split_bar(text)
            if len(parts) >= 2:
                out.append(warn_alert(inline(parts[0]), inline(" ／ ".join(parts[1:]))))
            else:
                head, rest = split_sentence(text)
                out.append(warn_alert(inline(head), inline(rest)))
    if not out:
        return render_prose(bs), 0
    return "\n".join(out), len(out)


def build_process(secs: list[dict]) -> str:
    sec = find(secs, "開発・運用プロセス", "開発運用プロセス", "運用プロセス")
    if sec is None:
        return NA_SECTION
    bs = blocks(sec["raw"])
    entries: list[str] = []
    for it in all_list_items(bs):
        entries.append(join_lines(it))
    if not entries:
        tbl = first_table(bs)
        if tbl is not None:
            entries = [" ／ ".join(c for c in r if c.strip()) for r in tbl[1] if any(c.strip() for c in r)]
    if not entries:
        return render_prose(bs)

    def icon_for(text: str) -> str:
        t = plain(text)
        if "ブランチ" in t or "branch" in t.lower():
            return "i-branch"
        if "デプロイ" in t or "Deploy" in t or "Vercel" in t or "リリース" in t:
            return "i-plug"
        if "定期" in t or "cron" in t.lower() or "ジョブ" in t or "スケジュール" in t:
            return "i-clock"
        if "CI" in t or "テスト" in t or "品質" in t or "lint" in t.lower():
            return "i-terminal"
        return "i-branch"

    lis = "".join(
        f'<li><svg class="icon"><use href="#{icon_for(e)}"/></svg><div>{inline(e)}</div></li>' for e in entries
    )
    return f'<ul class="process-list">{lis}</ul>'


def build_stack(secs: list[dict]) -> str:
    sec = find(secs, "技術スタック", "技術")
    if sec is None:
        return f"<p>{esc('技術スタックは正本に記載なし')}</p>"
    bs = blocks(sec["raw"])
    tbl = first_table(bs)
    if tbl is None:
        items = all_list_items(bs)
        if items:
            return "".join(
                f'<span class="chip chip--secondary"><span class="chip__dot"></span>'
                f'<span class="chip__label">{esc(plain(join_lines(it)))}</span></span>'
                for it in items
            )
        return render_prose(bs)
    header, rows = tbl
    i_name = col_index(header, "技術", "名称", "ライブラリ", "パッケージ") or 0
    i_ver = col_index(header, "バージョン", "版", "Version")
    chips: list[str] = []
    for r in rows:
        if not any(c.strip() for c in r):
            continue
        name = plain(r[i_name]) if i_name < len(r) else ""
        if not name:
            continue
        ver = plain(r[i_ver]) if i_ver is not None and i_ver < len(r) else ""
        meta = f'<span class="chip__meta">{esc(ver)}</span>' if ver else ""
        chips.append(
            f'<span class="chip chip--secondary"><span class="chip__dot"></span>'
            f'<span class="chip__label">{esc(name)}</span>{meta}</span>'
        )
    return "".join(chips) if chips else render_prose(bs)


_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_FLAG_RE = re.compile(r"WIP|未コミット|未着手|持ち越し|やりかけ|ブロッカー|待ち|⚠")


def _reldays(d: str, base: date | None) -> str:
    if base is None:
        return ""
    try:
        y, m, dd = (int(x) for x in d.split("-"))
        delta = (base - date(y, m, dd)).days
    except ValueError:
        return ""
    if delta < 0:
        return ""
    return "本日" if delta == 0 else f"{delta}日前"


def build_recent(secs: list[dict], generated: date | None) -> tuple[str, str | None]:
    """`.tl-item` の並びと、最終コミット日（取れれば YYYY-MM-DD）を返す。"""
    sec = find(secs, "直近の状態", "直近")
    if sec is None:
        return NA_SECTION, None
    bs = blocks(sec["raw"])
    raw_text = "\n".join(sec["raw"])
    dates = sorted(set(m.group(0) for m in _DATE_RE.finditer(raw_text)))
    last_commit = dates[-1] if dates else None

    entries: list[tuple[str, str]] = []  # (date or "", text)
    for b in bs:
        if b[0] == "p":
            entries.append(("", b[1]))
        elif b[0] == "list":
            for it in b[2]:
                entries.append(("", join_lines(it)))
        elif b[0] == "table":
            header, rows = b[1], b[2]
            for r in rows:
                if not any(c.strip() for c in r):
                    continue
                d = ""
                md = _DATE_RE.search(" ".join(r))
                if md:
                    d = md.group(0)
                head = r[0]
                rest = " ／ ".join(c for c in r[1:] if c.strip())
                entries.append((d, f"**{head}** {rest}".strip()))
        elif b[0] == "h":
            entries.append(("", f"**{b[2]}**"))
        elif b[0] == "fence":
            continue

    if not entries:
        return NA_SECTION, last_commit

    out: list[str] = []
    for k, (d, text) in enumerate(entries):
        cls = "tl-item"
        if k == 0:
            cls += " now"
        elif _FLAG_RE.search(plain(text)):
            cls += " flag"
        stamp = ""
        if d:
            rel = _reldays(d, generated)
            stamp = f'<div class="tl-date">{esc(d)}{f"（{rel}）" if rel else ""}</div>'
        out.append(f'<div class="{cls}">{stamp}<div class="tl-msg">{inline(text)}</div></div>')
    return "\n".join(out), last_commit


def _severity_of(parts: list[str]) -> tuple[str, str, str] | None:
    for p in parts:
        key = plain(p).strip().lower()
        if key in SEVERITY:
            return SEVERITY[key]
        for k, v in SEVERITY.items():
            if k in plain(p):
                return v
    return None


def _kind_of(parts: list[str]) -> str | None:
    for p in parts:
        pp = plain(p).strip()
        for k in KINDS:
            if pp == k or pp.startswith(k):
                return k
    return None


def _discovery_alert(parts: list[str], body_lines: list[str]) -> tuple[str, str]:
    sev = _severity_of(parts) or SEVERITY_DEFAULT
    kind = _kind_of(parts)
    ident = None
    rest: list[str] = []
    for p in parts:
        pp = plain(p).strip()
        if ident is None and re.fullmatch(r"[A-Z]?\d{1,3}", pp):
            ident = pp
            continue
        if kind and (pp == kind or pp.startswith(kind)):
            continue
        if _severity_of([p]) and len(pp) <= 12:
            continue
        rest.append(p)
    title = rest[0] if rest else (parts[-1] if parts else "")
    evidence_parts = rest[1:]
    for ln in body_lines:
        if ln.strip():
            evidence_parts.append(ln.strip())
    evidence = " ／ ".join(e for e in evidence_parts if e.strip())

    meta = f'<span class="badge badge--{sev[1]} badge--mono">{esc(sev[2])}</span>'
    if kind:
        meta += f'<span class="badge badge--outline kind-pill">{esc(kind)}</span>'
    if ident:
        meta += f'<span class="badge badge--outline badge--mono">{esc(ident)}</span>'
    desc = f'<p class="alert__description">{inline(evidence)}</p>' if evidence else ""
    alert = (
        f'<div class="alert alert--{sev[0]}"><span class="alert__indicator">'
        '<svg class="icon"><use href="#i-warn"/></svg></span>'
        f'<div class="alert__content"><div class="alert__meta">{meta}</div>'
        f'<p class="alert__title">{inline(title)}</p>{desc}</div></div>'
    )
    return alert, sev[0]


def build_discovery(secs: list[dict]) -> tuple[str, int, str]:
    """(HTML, 件数, 最悪の深刻度) を返す。"""
    sec = find(secs, "穴・発見事項", "発見事項", "穴")
    if sec is None:
        return (
            '<p class="since-note">穴・発見事項は正本に記載なし（<code>## 穴・発見事項</code> を追記すると次回から反映される）。</p>',
            0,
            "default",
        )
    lines = sec["raw"]
    out: list[str] = []
    worst = "default"
    rank = {"default": 0, "success": 1, "warning": 2, "danger": 3}

    def note(alert: str, sev: str) -> None:
        nonlocal worst
        out.append(alert)
        if rank[sev] > rank[worst]:
            worst = sev

    # 形式1: `### G01｜種類｜深刻度｜題` の見出し
    subs = [s for s in split_sections(lines) if s["level"] >= 3 and re.search(r"[｜|]", s["title"])]
    for s in subs:
        alert, sev = _discovery_alert(split_bar(s["title"]), s["body"])
        note(alert, sev)

    if not out:
        bs = blocks(lines)
        # 形式2: 箇条書き 1件＝「種類｜深刻度｜内容｜証拠」
        for it in all_list_items(bs):
            text = join_lines(it)
            parts = split_bar(text)
            if len(parts) >= 2:
                alert, sev = _discovery_alert(parts, [])
                note(alert, sev)
        # 形式3: 表
        if not out:
            tbl = first_table(bs)
            if tbl is not None:
                for r in tbl[1]:
                    if not any(c.strip() for c in r):
                        continue
                    alert, sev = _discovery_alert(r, [])
                    note(alert, sev)
        if not out:
            body = render_prose(bs)
            return body, 0, "default"
    return "\n".join(out), len(out), worst


def build_links(secs: list[dict]) -> str:
    sec = find(secs, "関連リンク", "リンク")
    if sec is None:
        return "<li>なし</li>"
    bs = blocks(sec["raw"])
    items = all_list_items(bs)
    if not items:
        text = " ".join(b[1] for b in bs if b[0] == "p").strip()
        if not text or "なし" in text:
            return "<li>なし</li>"
        items = [[text]]
    lis = [
        f'<li><svg class="icon"><use href="#i-link"/></svg><div>{inline(join_lines(it))}</div></li>'
        for it in items
    ]
    return "".join(lis) if lis else "<li>なし</li>"


# ── 状況ボード（変換結果からの機械導出。取れないタイルは出さない） ─────────────
def tile(cls: str, label: str, value: str, href: str | None) -> str:
    inner = f'<span class="stat-tile__label">{esc(label)}</span><span class="stat-tile__value mono">{esc(value)}</span>'
    if href:
        return f'<a class="stat-tile {cls}" href="{href}">{inner}</a>'
    return f'<span class="stat-tile {cls}">{inner}</span>'


_UNCOMMITTED_RE = re.compile(r"未コミット[^\d]{0,12}(\d+)\s*件")
_CLEAN_RE = re.compile(r"(?:作業ツリー|ワーキングツリー)[^。]{0,10}クリーン|未コミットの変更(?:は)?なし")


def build_statboard(
    generated: date | None,
    last_commit: str | None,
    recent_text: str,
    commits_plus: int | None,
    discoveries: int,
    worst: str,
    role_gaps: int,
    tbd_count: int,
) -> str:
    tiles: list[str] = []
    if last_commit and generated:
        rel = _reldays(last_commit, generated)
        if rel:
            days = 0 if rel == "本日" else int(rel.replace("日前", ""))
            tiles.append(tile("warn" if days >= 31 else "ok", "最終コミットから", f"{days}日", "#recent"))
    m_unc = _UNCOMMITTED_RE.search(recent_text)
    if m_unc:
        n = int(m_unc.group(1))
        tiles.append(tile("ok" if n == 0 else "warn", "未コミット変更", f"{n}件", "#recent"))
    elif _CLEAN_RE.search(recent_text):
        tiles.append(tile("ok", "未コミット変更", "0件", "#recent"))
    if commits_plus is not None:
        tiles.append(tile("ok", "前回比コミット", f"+{commits_plus}", "#since-last"))
    if discoveries:
        cls = {"danger": "crit", "warning": "warn"}.get(worst, "ok")
        tiles.append(tile(cls, "穴・発見事項", f"{discoveries}件", "#discovery"))
    if role_gaps:
        tiles.append(tile("warn", "役割の穴", f"{role_gaps}件", "#people"))
    if tbd_count and len(tiles) < 6:
        tiles.append(tile("warn", "TBD", f"{tbd_count}件", None))
    return "".join(tiles[:6])


# ── Artifact 版 ─────────────────────────────────────────────────────────────
ARTIFACT_FORBIDDEN = ("<!doctype", "<html", "</html>", "<head>", "</head>", "<body", "</body>")


def to_artifact(full_html: str) -> str:
    """完結HTMLから doctype/html/head/body を持たない派生を組み立てる。"""
    m_title = re.search(r"<title>(.*?)</title>", full_html, re.S | re.I)
    m_head = re.search(r"</title>(.*?)</head>", full_html, re.S | re.I)
    m_body = re.search(r"<body[^>]*>(.*?)</body>", full_html, re.S | re.I)
    if not (m_title and m_head and m_body):
        sys.exit("build-overview-html.py: 完結HTMLから title/head/body を切り出せない（テンプレ構造の想定違い）")
    head_extra = re.sub(r"<meta\b[^>]*>", "", m_head.group(1)).strip()
    return f"<title>{m_title.group(1)}</title>\n{head_extra}\n\n{m_body.group(1).strip()}\n"


# ── 「増やす」セクション: このレポートの育て方 ────────────────────────────────
# 数週間ぶりに戻った読者が「穴の節をもっと掘りたい」「引き継ぎ先に渡したい」と思ったとき、
# SKILL.md を開き直すところから始めさせない。成果物自身に、そのまま別のエージェントへ
# 投げられるプロンプトを載せる。
#
# プロンプトが指すのは **MD正本の絶対パス**であって、この HTML ではない。HTML は MD から
# 再生成できる使い捨てのビューなので、それを入力にすると劣化コピーが増える。
#
# カードは本スクリプトが書く。LLM には書かせない ── シェルとプロンプトの作者を1つに保つ。
# 「この HTML を作り直す」テンプレートは意図的に置かない（作り直すのは /project-catchup）。

READERS = "R1 自分（復帰）／ R2 引き継ぎ先・新規参画 ／ R3 外部（クライアント・上長）"

_GROW_COMMON = """# 参照（必ず開いてから書く。中身はこのプロンプトに貼っていない）
- 意味の正本: {md}
- リポジトリ: {repo}

**正本は MD。この HTML を入力にしないこと**（HTML は MD から再生成できる使い捨てのビュー）。
正本に無い事実は書かない。取れないものは「該当なし」と書く。推測は「推定」と明記する。

# 出力
{outdir}/{outfile} に、<!DOCTYPE html> から始まる完結した HTML document を1枚書く。
既存の docs/project-overview.html は書き換えない（併存させる）。

# 制約
- inline CSS / inline JS のみ。外部CDN・外部CSS・外部スクリプト・外部フォント・外部画像を
  読み込まない。ネットワーク通信もしない（自己完結でないと検査に落ちる）。
- 色は意味にだけ使う: 緑=健全・解消済み ／ amber=注意・WIP・人待ち ／ 赤=危険・要対処 ／
  青=次の一手・強調・リンク。装飾目的で色を付けない。
- 形が先、文字が後。構造・流れ・比較・状態は図・タイル・レイアウトで先に掴ませ、
  文章は判断点だけに絞る。強調は各段落1箇所まで。
- 事実で終わらず判断材料で終わる。「で、次に何をするか」まで書く（提案は推定と明記）。
"""

GROW_CARDS: list[dict[str, str]] = [
    {
        "id": "handoff",
        "file": "project-overview-handoff.html",
        "title": "引き継ぎ版を作る（読者 R2）",
        "desc": "他の人にこのリポジトリを渡すとき。前提知識・地雷・読む順を1枚に。",
        "task": "引き継ぎ先（このリポジトリもドメインも初見の開発者）が最初に読む1枚を作る。\n"
                "前提知識 → 読む順（どのファイル・どの docs から）→ 触ると危ない箇所 →\n"
                "誰に何を聞くか → まだ決まっていないこと、の順で構成する。\n"
                "「次の一手」は薄くてよい（引き継ぎ直後は着手しない）。\n"
                "逆に「なぜこうなっているか」は省略しない ── 引き継ぎ先の最初の事故は\n"
                "理由が分からず作り直すこと。",
    },
    {
        "id": "brief",
        "file": "project-overview-brief.html",
        "title": "外部説明版を作る（読者 R3）",
        "desc": "クライアント・上長に状況を説明するとき。実装語を落として意思決定だけ残す。",
        "task": "実装を知らない相手（クライアント・上長）向けの1枚を作る。\n"
                "何のためのものか → 今どこまで進んでいるか → 相手の判断が要ることは何か →\n"
                "リスクと、それが放置されるとどうなるか、の順。\n"
                "テーブル名・関数名・型・コマンドは出さない。ドメイン語は使ってよい。\n"
                "「あなたの返事待ち」の項目を先頭に集約する。",
    },
    {
        "id": "deep",
        "file": "project-overview-{{セクションID}}.html",
        "title": "1セクションを深掘りする",
        "desc": "穴・設計・運用など、1つの問いだけを掘り下げた別ページを作る。",
        "task": "{{どのセクションを掘るか（resume / intent / people / design / ops / gaps のどれか）}}\n"
                "の内容だけを掘り下げた1枚を作る。\n"
                "正本の該当節を起点に、リポジトリを実際に読んで裏を取り、\n"
                "正本に書ける粒度まで具体化する（ファイル名・行・コマンドまで落とす）。\n"
                "掘った結果 正本に足すべき事実が見つかったら、HTML の末尾に\n"
                "「正本へ追記すべき事実」として列挙する（正本は書き換えない）。",
    },
    {
        "id": "free",
        "file": "project-overview-{{id}}.html",
        "title": "自由記述で1枚足す",
        "desc": "上のどれでもないとき。1行目とファイル名を書き換えてから投げる。",
        "task": "{{どんな1枚が欲しいか（例: 依存関係だけの図 / 定期ジョブの一覧 / コスト構造）}}",
    },
]


def build_grow(md_path: Path, out_path: Path) -> str:
    """「増やす」セクションの中身を組む。YAML ではなく MD正本の絶対パスを渡す。"""
    md_abs = md_path.resolve()
    outdir = out_path.resolve().parent
    repo = md_abs.parent.parent if md_abs.parent.name == "docs" else md_abs.parent

    cards: list[str] = []
    for i, card in enumerate(GROW_CARDS, 1):
        body_id = f"pc-body-{i}"
        common = _GROW_COMMON.format(
            md=md_abs, repo=repo, outdir=outdir, outfile=card["file"])
        body = f"# やること\n{card['task']}\n\n{common}"
        cards.append(
            f'<article class="pc">'
            f'<h3>{esc(card["title"])}</h3>'
            f'<p class="pc-desc">{esc(card["desc"])}</p>'
            f'<details><summary>プロンプトを見る</summary>'
            f'<pre id="{body_id}">{esc(body)}</pre></details>'
            f'<button type="button" class="btn btn--secondary btn--sm pc-copy" '
            f'data-for="{body_id}" data-label="コピー">コピー</button>'
            f'</article>'
        )

    paths = (
        '<div class="pc-paths">'
        f'<div><b>正本（MD）</b>{esc(str(md_abs))}</div>'
        f'<div><b>出力先</b>{esc(str(outdir))}</div>'
        f'<div><b>リポジトリ</b>{esc(str(repo))}</div>'
        "</div>"
    )

    lead = (
        '<p class="pc-lead">このレポートは<b>読者1人ぶん</b>（数週間ぶりに戻った自分）に'
        "最適化されている。別の読者・別の深さが要るときは、下のプロンプトをコピーして"
        "ローカルのファイルを開けるエージェント（Claude Code / Cursor / Codex）に投げると、"
        f"別ページが1枚返ってくる。読者は {esc(READERS)} の3種を想定している。"
        "<br>プロンプトが渡すのは<b>MD正本の絶対パス</b>で、この HTML ではない。"
        "正本さえ最新なら、投げ直すだけで最新の事実から書かれる。</p>"
    )
    return lead + paths + "".join(cards)


# ── 検査 ────────────────────────────────────────────────────────────────────
# ドキュメント面: 実際に外部リソースを読みに行くタグ・属性だけを見る。
DOC_FORBIDDEN: list[tuple[str, str]] = [
    (r"<script[^>]*\ssrc\s*=", "外部スクリプト読み込み"),
    (r"<link[^>]*rel\s*=\s*[\"']?stylesheet", "外部スタイルシート"),
    (r"@import\s+(?:url\()?\s*[\"']?(?:https?:)?//", "リモート @import"),
    (r"<img[^>]*\ssrc\s*=\s*[\"']?(?:https?:)?//", "外部画像"),
    (r"<iframe\b", "iframe"),
    (r"<(?:object|embed)\b", "<object> / <embed>"),
    (r"(?:src|href)\s*=\s*[\"']?(?:https?:)?//(?:cdn\.|[^\"'\s>]*(?:jsdelivr|unpkg\.com|fonts\.googleapis\.com))", "CDN / 外部フォント"),
]
# 実行面（<script> 本文と on* 属性）だけを見る。本文テキストに現れた語は何も実行しない。
JS_FORBIDDEN: list[tuple[str, str]] = [
    (r"\bfetch\s*\(", "fetch()"),
    (r"\bXMLHttpRequest\b", "XMLHttpRequest"),
    (r"\bWebSocket\b", "WebSocket"),
]
_SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)
_HANDLER_RE = re.compile(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*')", re.I)


def check_self_contained(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    lines = text.splitlines()
    for pattern, label in DOC_FORBIDDEN:
        rx = re.compile(pattern, re.I)
        for lineno, line in enumerate(lines, 1):
            if rx.search(line):
                findings.append(f"{path}:{lineno}: {label} — {line.strip()[:110]}")
    executable: list[tuple[int, str]] = [
        (text.count("\n", 0, m.start(1)) + 1, m.group(1)) for m in _SCRIPT_RE.finditer(text)
    ]
    executable += [(text.count("\n", 0, m.start(1)) + 1, m.group(1)) for m in _HANDLER_RE.finditer(text)]
    for base, chunk in executable:
        for pattern, label in JS_FORBIDDEN:
            for m in re.finditer(pattern, chunk):
                lineno = base + chunk.count("\n", 0, m.start())
                findings.append(f"{path}:{lineno}: {label}（実行面）")
    return findings


def run_checks(out: Path, art: Path, md: Path | None) -> int:
    ng = 0
    for path in (out, art):
        if not path.is_file():
            print(f"NG  {path}: ファイルが無い")
            ng += 1
            continue
        text = path.read_text(encoding="utf-8")

        leftovers = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text)))
        if leftovers:
            print(f"NG  {path}: プレースホルダ残存 {len(leftovers)} 種 — {' '.join(leftovers)}")
            ng += 1
        else:
            print(f"OK  {path}: プレースホルダ残存 0")

        findings = check_self_contained(path, text)
        if findings:
            print(f"NG  {path}: 外部依存 {len(findings)} 件")
            for f in findings:
                print(f"      {f}")
            ng += 1
        else:
            print(f"OK  {path}: 外部依存なし（自己完結）")

        # 6つの問いセクション + 「増やす」（MD正本に対応する見出しを持たない機械生成セクション）
        panels = text.count("data-tab-panel=")
        if panels == 7:
            print(f"OK  {path}: data-tab-panel= 7件")
        else:
            print(f"NG  {path}: data-tab-panel= {panels}件（7件であること）")
            ng += 1

    art_text = art.read_text(encoding="utf-8") if art.is_file() else ""
    hits = [t for t in ARTIFACT_FORBIDDEN if t in art_text.lower()]
    if hits:
        print(f"NG  {art}: Artifact シェル禁止タグ — {' '.join(hits)}")
        ng += 1
    else:
        print(f"OK  {art}: Artifact シェル禁止タグなし")

    if md is not None and md.is_file() and out.is_file():
        md_n = len([l for l in md.read_text(encoding="utf-8").splitlines() if re.match(r"^# \d", l)])
        html_n = len([l for l in out.read_text(encoding="utf-8").splitlines() if re.match(r"^# \d", l)])
        if md_n == html_n:
            print(f"OK  再開手順の番号コメント: MD {md_n}件 = HTML {html_n}件")
        else:
            print(f"NG  再開手順の番号コメント: MD {md_n}件 ≠ HTML {html_n}件（逐語転記できていない）")
            ng += 1
    return ng


# ── 本体 ────────────────────────────────────────────────────────────────────
def read_svg(path: str | None, label: str) -> str:
    if not path:
        return NA_SHEET
    p = Path(path)
    if not p.is_file():
        sys.exit(f"build-overview-html.py: {label} の SVG が見つからない: {p}")
    return p.read_text(encoding="utf-8").strip()


_SRC_LINE_RE = re.compile(r"^\s*(?:出典|Source)[:：]\s*(.*)$")


def diagram_src(secs: list[dict], cli_value: str | None, *names: str) -> str:
    if cli_value:
        return inline(cli_value if cli_value.startswith("出典") else f"出典: {cli_value}")
    sec = find(secs, *names, level=3)
    if sec is not None:
        for ln in sec["raw"]:
            m = _SRC_LINE_RE.match(plain(ln))
            if m:
                return inline(f"出典: {m.group(1)}")
    return esc("出典: 未指定")


def main() -> None:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="PROJECT_OVERVIEW.md からペライチHTML／Artifact版を機械生成する")
    ap.add_argument("--md", default="docs/PROJECT_OVERVIEW.md", help="MD正本のパス")
    ap.add_argument("--out", default="docs/project-overview.html", help="出力する完結HTMLのパス")
    ap.add_argument("--template", default=str(here.parent / "templates" / "overview.html"), help="テンプレHTML")
    ap.add_argument("--svg-structure", help="構造・依存関係の SVG ファイル")
    ap.add_argument("--svg-interface", help="主要インターフェースの SVG ファイル")
    ap.add_argument("--svg-erd", help="データ関係の SVG ファイル")
    ap.add_argument("--svg-structure-src", help="構造・依存関係の出典1行")
    ap.add_argument("--svg-interface-src", help="主要インターフェースの出典1行")
    ap.add_argument("--svg-erd-src", help="データ関係の出典1行")
    ap.add_argument("--check-only", action="store_true", help="生成せず既存の出力を検査するだけ")
    args = ap.parse_args()

    md_path = Path(args.md)
    out_path = Path(args.out)
    art_path = out_path.with_suffix(".artifact.html")

    if args.check_only:
        sys.exit(1 if run_checks(out_path, art_path, md_path) else 0)

    if not md_path.is_file():
        sys.exit(f"build-overview-html.py: MD正本が無い: {md_path}")
    tpl_path = Path(args.template)
    if not tpl_path.is_file():
        sys.exit(f"build-overview-html.py: テンプレが無い: {tpl_path}")

    md_text = md_path.read_text(encoding="utf-8")
    md_lines = md_text.splitlines()

    # frontmatter
    generated_s, sha = "", ""
    if md_lines and md_lines[0].strip() == "---":
        for ln in md_lines[1:]:
            if ln.strip() == "---":
                break
            k, _, v = ln.partition(":")
            k, v = k.strip(), v.strip()
            if k == "generated":
                generated_s = v
            elif k == "commit":
                sha = v
    body_start = 0
    if md_lines and md_lines[0].strip() == "---":
        for i, ln in enumerate(md_lines[1:], 1):
            if ln.strip() == "---":
                body_start = i + 1
                break
    body_lines = md_lines[body_start:]

    generated: date | None = None
    if _DATE_RE.fullmatch(generated_s):
        y, m, d = (int(x) for x in generated_s.split("-"))
        generated = date(y, m, d)
    if not generated_s:
        generated = date.today()
        generated_s = generated.isoformat()

    # プロジェクト名: 最初の H1 から「全体像」を落とす
    project = md_path.resolve().parent.parent.name
    for ln in body_lines:
        m = re.match(r"^#\s+(.*)$", ln)
        if m:
            project = re.sub(r"\s*全体像\s*$", "", plain(m.group(1))).strip() or project
            break

    secs = split_sections(body_lines)

    summary_sec = find(secs, "30秒サマリー", "サマリー")
    summary_bs = blocks(summary_sec["raw"]) if summary_sec else []
    tagline, dropped = build_tagline(summary_bs)
    summary_html = build_summary(summary_bs, dropped)

    since_sec = find(secs, "前回キャッチアップからの変化", "前回からの変化", "前回キャッチアップ")
    since_html, commits_plus = build_since(since_sec)

    resume_html = build_resume(find(secs, "再開手順"))
    next_html = build_next(find(secs, "次の一手"))
    intent_html = build_intent(secs)
    people_html = build_people(secs)
    role_gaps_html, role_gaps_n = build_role_gaps(secs)
    process_html = build_process(secs)
    stack_html = build_stack(secs)
    recent_sec = find(secs, "直近の状態", "直近")
    recent_html, last_commit = build_recent(secs, generated)
    discovery_html, discovery_n, worst = build_discovery(secs)
    links_html = build_links(secs)

    recent_text = "\n".join(recent_sec["raw"]) if recent_sec else ""
    tbd_count = len(re.findall(r"\bTBD\b", md_text))
    statboard_html = build_statboard(
        generated, last_commit, recent_text, commits_plus, discovery_n, worst, role_gaps_n, tbd_count
    )

    values = {
        "PROJECT_NAME": esc(project),
        "DATE": esc(generated_s),
        "SHA": esc(sha or "unknown"),
        "TAGLINE": tagline or esc(project),
        "STATBOARD_HTML": statboard_html,
        "SUMMARY_HTML": summary_html,
        "SINCE_LAST_HTML": since_html,
        "RESUME_HTML": resume_html,
        "NEXT_HTML": next_html,
        "INTENT_HTML": intent_html,
        "PEOPLE_HTML": people_html,
        "ROLE_GAPS_HTML": role_gaps_html,
        "DIAGRAM_STRUCTURE_SVG": read_svg(args.svg_structure, "構造・依存関係"),
        "DIAGRAM_INTERFACE_SVG": read_svg(args.svg_interface, "主要インターフェース"),
        "DIAGRAM_ERD_SVG": read_svg(args.svg_erd, "データ関係"),
        "DIAGRAM_STRUCTURE_SRC": diagram_src(secs, args.svg_structure_src, "構造・依存関係", "構造"),
        "DIAGRAM_INTERFACE_SRC": diagram_src(secs, args.svg_interface_src, "主要インターフェース", "インターフェース"),
        "DIAGRAM_ERD_SRC": diagram_src(secs, args.svg_erd_src, "データ関係", "データ"),
        "PROCESS_HTML": process_html,
        "STACK_HTML": stack_html,
        "RECENT_HTML": recent_html,
        "DISCOVERY_HTML": discovery_html,
        "LINKS_HTML": links_html,
        "GROW_HTML": build_grow(md_path, out_path),
    }

    tpl = tpl_path.read_text(encoding="utf-8")
    needed = set(re.findall(r"\{\{([A-Z_]+)\}\}", tpl))
    unknown = sorted(needed - set(values))
    if unknown:
        # 未知のプレースホルダは黙って空にせずバグとして落とす
        sys.exit(f"build-overview-html.py: 未知のプレースホルダ: {' '.join('{{' + u + '}}' for u in unknown)}")

    full = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values[m.group(1)], tpl)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(full, encoding="utf-8")
    print(f"build-overview-html.py: wrote {out_path} ({len(full.encode('utf-8')) / 1024:.0f} KB)")

    artifact = to_artifact(full)
    art_path.write_text(artifact, encoding="utf-8")
    print(f"build-overview-html.py: wrote {art_path} ({len(artifact.encode('utf-8')) / 1024:.0f} KB, Artifact 版)")

    ng = run_checks(out_path, art_path, md_path)
    if ng:
        sys.exit(f"build-overview-html.py: 検査 NG {ng} 件")


if __name__ == "__main__":
    main()
