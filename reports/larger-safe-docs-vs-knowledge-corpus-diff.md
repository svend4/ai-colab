# Knowledge report diff

| Metric | A | B | Delta |
|---|---:|---:|---:|
| documents | 8 | 69 | +61 |
| shown_query_hits | 7 | 10 | +3 |

## Reports

- A: `reports/knowledge-corpus-report.md` (`data\knowledge-corpus`)
- B: `reports/larger-safe-docs-pipeline-report.md` (`docs`)

## Type Distribution

| Type | A | B | Delta |
|---|---:|---:|---:|
| csv | 1 | 0 | -1 |
| json | 1 | 0 | -1 |
| md | 4 | 69 | +65 |
| txt | 2 | 0 | -2 |

## Interpretation

This diff is mechanical. It shows scale and type changes. Query hits are the displayed top-N hits from each report, not a full corpus-wide total. Quality still needs human/agent review of the actual hits and summaries.
