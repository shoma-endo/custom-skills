# Data collection

Collect evidence before writing. If a fact cannot be established, write `TBD`; do not invent it.

## Baseline

Run relevant commands independently:

```bash
git status --short
git log --oneline -20
git branch -a
git remote -v
```

Read in this order where present: README, AGENTS/CLAUDE instructions, project docs, manifests, then major entry points. Detect manifests rather than assuming Node: `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`, or `appsscript.json`.

## Evidence by question

### Intent

Use README purpose/motivation, requirements, ADRs, and commit bodies. Identify the beneficiary and desired outcome. Mark UI- or vocabulary-based inference explicitly.

```bash
git log --format="%h %ad %s%n%b" --date=short -30
```

### People

Use authorship, CODEOWNERS, manifest maintainers, and documented contacts.

```bash
git shortlog -sne --all
git log --format="%an %ad" --date=short -1
```

Report role gaps only with evidence: single-person dependency, missing reviewer, unknown deploy authority, or apparently inactive maintainer.

### Design and operation

Trace service boundaries, primary interfaces, persistent entities, CI/CD, deploy targets, scheduled jobs, and only the major technologies. Prefer project-local architecture docs when current.

### Current work and gaps

Inspect branches, uncommitted changes, recent commits, TODO/FIXME markers, disabled workflows, missing scripts referenced by docs, environment-sample mismatches, unreferenced endpoints or modules, and manual-only operations. Cite `file:line` when possible.

## Delta from the previous catch-up

When an existing overview has `generated` and `commit` frontmatter, compare it with HEAD:

```bash
git log --oneline <previous>..HEAD
git diff --stat <previous>..HEAD
```

If the commit no longer exists, record `比較不能`; on the first run, record `初回キャッチアップ（比較基準なし）` and continue.

