#!/usr/bin/env python3
"""
Repo inventory — read-only scanner for local repositories.
Does NOT execute code. Only inspects, maps, and reports.
"""

import json
import os
import sys
from pathlib import Path

DEFAULT_MAX_FILES = 1000
RISK_READ_MAX_BYTES = 50000
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "venv",
    ".venv",
    "target",
    "build",
    "dist",
}


SUPPORTED_LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".md": "Markdown",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".dockerfile": "Docker",
    ".sql": "SQL",
}

PACKAGE_FILES = {
    "package.json": "npm",
    "requirements.txt": "pip",
    "Pipfile": "pipenv",
    "pyproject.toml": "poetry/flit",
    "setup.py": "setuptools",
    "Cargo.toml": "cargo",
    "Cargo.lock": "cargo",
    "go.mod": "go",
    "go.sum": "go",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "Makefile": "make",
    "CMakeLists.txt": "cmake",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker-compose",
    ".github/workflows": "GitHub Actions",
    ".gitlab-ci.yml": "GitLab CI",
}

TEST_INDICATORS = {
    "test": "test directory",
    "tests": "tests directory",
    "spec": "spec directory",
    "__tests__": "Jest-style tests",
    ".github/workflows": "CI/CD workflows",
    ".travis.yml": "Travis CI",
    "tox.ini": "tox",
    "pytest.ini": "pytest",
    "jest.config": "Jest",
    "karma.conf": "Karma",
}

RISK_PATTERNS = {
    "setup.py": "may execute code during install",
    "install.sh": "shell script — execute with caution",
    "build.sh": "shell script — build-time execution",
    "run.sh": "shell script — runtime execution",
    "eval(": "potentially dangerous eval",
    "exec(": "potentially dangerous exec",
    "subprocess.call": "spawns subprocess",
    "os.system": "spawns system shell",
    "requests.get": "network call",
    "urllib": "network call",
    "import requests": "imports network library",
}


class PathAccessError(ValueError):
    pass


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _resolve_repo_path(repo_path: str, base_dir: str = None) -> Path:
    if base_dir is None:
        return Path(repo_path).expanduser().resolve()
    base = Path(base_dir).expanduser().resolve()
    raw_path = Path(repo_path).expanduser()
    repo = (raw_path if raw_path.is_absolute() else base / raw_path).resolve()
    if not _is_relative_to(repo, base):
        raise PathAccessError(f"path is outside allowed root: {repo}")
    return repo


def scan_repo(repo_path: str, max_files: int = DEFAULT_MAX_FILES, base_dir: str = None) -> dict:
    """Scan a repository and return inventory report."""
    repo = _resolve_repo_path(repo_path, base_dir)
    if not repo.exists():
        return {"error": f"Path not found: {repo_path}"}
    if not repo.is_dir():
        return {"error": f"Not a directory: {repo_path}"}

    report = {
        "path": str(repo),
        "structure": [],
        "languages": {},
        "package_files": [],
        "tests": [],
        "risks": [],
        "summary": {},
        "max_files": max_files,
        "truncated": False,
    }

    total_files = 0
    total_size = 0

    for root, dirs, files in os.walk(repo):
        # skip hidden and common non-source dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]

        rel_root = Path(root).relative_to(repo)
        if str(rel_root) == '.':
            rel_root = Path('')

        for f in files:
            if total_files >= max_files:
                report["truncated"] = True
                dirs[:] = []
                break

            total_files += 1
            p = Path(root) / f
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            total_size += size

            rel = rel_root / f
            report["structure"].append(str(rel))

            ext = Path(f).suffix.lower()
            if ext in SUPPORTED_LANGUAGES:
                lang = SUPPORTED_LANGUAGES[ext]
                report["languages"][lang] = report["languages"].get(lang, 0) + 1

            if f in PACKAGE_FILES:
                report["package_files"].append({"file": str(rel), "type": PACKAGE_FILES[f]})

            if f in TEST_INDICATORS or f.startswith('test_') or f.endswith('.test.js') or f.endswith('.spec.js') or f.endswith('_test.py'):
                report["tests"].append({"file": str(rel), "type": TEST_INDICATORS.get(f, "test file")})

            # risk check for shell scripts
            if f.endswith('.sh') or f.endswith('.ps1'):
                report["risks"].append({"file": str(rel), "risk": "shell script — execute with caution", "severity": "medium"})

            # risk check for network calls in Python
            if ext == '.py' and size < RISK_READ_MAX_BYTES:
                try:
                    content = p.read_text(encoding='utf-8', errors='replace')
                    for pattern, desc in RISK_PATTERNS.items():
                        if pattern in content:
                            report["risks"].append({"file": str(rel), "risk": desc, "severity": "high" if "dangerous" in desc or "eval" in desc or "exec" in desc else "medium"})
                            break
                except Exception:
                    pass

        if report["truncated"]:
            break

    report["summary"] = {
        "total_files": total_files,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "languages": report["languages"],
        "has_tests": len(report["tests"]) > 0,
        "has_package_files": len(report["package_files"]) > 0,
        "risk_count": len(report["risks"]),
        "truncated": report["truncated"],
        "max_files": max_files,
    }

    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: python inventory.py <repo-path> [--base <allowed-root>] [--max-files N]")
        print("Example: python inventory.py /path/to/repo --max-files 1000")
        sys.exit(1)

    repo_path = sys.argv[1]
    base_dir = None
    max_files = DEFAULT_MAX_FILES
    if "--base" in sys.argv:
        base_dir = sys.argv[sys.argv.index("--base") + 1]
    if "--max-files" in sys.argv:
        max_files = int(sys.argv[sys.argv.index("--max-files") + 1])
    try:
        report = scan_repo(repo_path, max_files=max_files, base_dir=base_dir)
    except Exception as exc:
        report = {"error": type(exc).__name__, "message": str(exc)}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
