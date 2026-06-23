# DOCX text extraction result — 2026-06-21

Task: `T-142`
Related: `T-137`, `D-020`, `topics/kotel-decision-material-2026-06-21.md`

## What changed

`tools/text_extract.py` now supports `.docx` as a read-only no-dependency extraction path.

Implementation details:

- `.docx` is treated as an Open XML zip container;
- only `word/document.xml` is read;
- XML is parsed with stdlib `xml.etree.ElementTree`, not by broad tag stripping;
- WordprocessingML paragraphs, text runs, tabs and breaks are converted to plain text;
- path confinement to `base_dir` is kept;
- canonical `drivers/redaction.py` redaction is applied before returning extracted text;
- `.pdf` remains unsupported and gated by a separate dependency decision.

## Why this shape

This is a good example of the "middle of the pyramid" becoming useful without becoming heavy. It gives agents and people one more real document type for the knowledge layer, but it does not introduce a package dependency, background service, execution sandbox, or hidden state.

The important boundary is deliberate: DOCX text is data extraction; PDF parsing is dependency policy. Mixing them would make a low-risk step depend on a higher-governance decision.

## Verification

Passed locally:

- `python tools\test_text_extract.py`
- `python tools\test_knowledge.py`

The new test creates a minimal `.docx` fixture with `zipfile`, verifies extracted text, verifies redaction of `token=SUPERSECRETXYZ`, and keeps the existing Markdown/TXT/HTML checks.

## Limits

This is not full Word rendering. It intentionally does not extract images, OCR, tracked-change semantics, comments, headers/footers, footnotes, or table structure as tables. For the current engine stage that is acceptable: the target is searchable plain text for knowledge/index workflows.

Future work can add structured DOCX metadata only after real corpus examples show demand.