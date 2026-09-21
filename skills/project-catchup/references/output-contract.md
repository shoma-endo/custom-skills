# Output contract

## Files

| File | Role |
|---|---|
| `docs/PROJECT_OVERVIEW.md` | Searchable, diffable source of truth |
| `docs/project-overview.html` | Self-contained desktop view |
| `docs/project-overview.artifact.html` | Artifact-compatible view without document shell tags |

The HTML files are disposable views. Never use them as the next update's source.

## Markdown structure

Use frontmatter with `generated`, `commit`, and `generator: project-catchup`, followed by these responsibilities in order:

1. `30秒サマリー` and previous-run delta
2. Restart commands and up to three evidence-backed next actions
3. Intent: background, purpose, beneficiaries
4. People: contributors, owners, role gaps
5. Design: structure, interfaces, and data relationships
6. Operation: development flow, CI/CD, deploys, scheduled work, major stack
7. Current work and gaps: WIP, bottlenecks, contradictions, TBD, unconnected paths
8. Related links

Use three Mermaid diagrams only when the repository supports them: structure/dependencies, major interfaces, and ER relationships. Each diagram includes a source line. Omit an inapplicable diagram with a reason.

## Generate views

```bash
python3 ~/.agents/skills/project-catchup/scripts/build-overview-html.py --md docs/PROJECT_OVERVIEW.md --out docs/project-overview.html
```

Pass generated SVGs with `--svg-structure`, `--svg-interface`, and `--svg-erd`. Keep Mermaid SVG `<defs>` intact because ER cardinality markers live there.

The generator must pass:

- zero unresolved placeholders
- no external scripts, stylesheets, images, iframes, or network calls
- seven panels: six project questions plus generated `grow`
- no `doctype`, `html`, `head`, or `body` tags in the Artifact version
- restart-step numbering preserved from Markdown

Fix the Markdown or template and rerun on failure; do not patch generated HTML.

## Final report

Lead with next actions, then list the three output paths, delta since the last run, critical gaps, role gaps, remaining TBDs, documentation/code contradictions, and generator checks. Include actual Mermaid error output when a diagram fails; do not speculate about its cause.

