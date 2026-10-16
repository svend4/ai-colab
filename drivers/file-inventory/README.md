# file-inventory driver

No-deps Python read-only scanner for a project folder.

This driver overlaps with `drivers/files/inventory.py`, but `T-059` adds fields useful for a project-wide inventory report: `mtime`, MIME guess, risk flags, optional SHA-256, JSON/Markdown output, and allowed-root support.

Boundary: the CLI requires `--base`. A path outside the base gets the same error whether it exists or not. A symlink that leads outside the base (or loops) is left out of the report: no name, size or SHA-256. `~` is not expanded under the base. Without `base_dir` in library use, the scanned root is the boundary.

Runtime tests are blocked until `T-039` is resolved.

