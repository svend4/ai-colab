# file-inventory driver

No-deps Python read-only scanner for a project folder.

This driver overlaps with `drivers/files/inventory.py`, but `T-059` adds fields useful for a project-wide inventory report: `mtime`, MIME guess, risk flags, optional SHA-256, JSON/Markdown output, and allowed-root support.

Runtime tests are blocked until `T-039` is resolved.

