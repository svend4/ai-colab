#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
External-source intake (форк-дополнение к `docs/external-code-sandbox.md` Codex).

Автоматизирует стадии S1 (intake) + S3 (read-only inventory) + S7 (report) генерик-песочницы:
регистрирует внешний источник (любой репозиторий/папка, НЕ привязано к svend4/персоне), делает
**read-only** инвентаризацию (через repo-runner inventory — код НЕ запускается) и пишет
markdown-отчёт. Execute остаётся запрещён (gate — `docs/execute-sandbox-preflight.md`).

Контракт папки `sandbox/` (структура/policy) — за Codex (`docs/external-code-sandbox.md`).
Этот инструмент — исполняемый слой поверх неё (синтез по D-017 fork-and-synthesize).

CLI:
    python tools/sandbox.py intake <source-id> --from <путь> [--note "..."]
    python tools/sandbox.py list
"""
import os
import sys
from _ioutil import configure_output
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVERS = os.path.join(ROOT, "drivers")
SANDBOX = os.path.join(ROOT, "sandbox")
INBOX = os.path.join(SANDBOX, "inbox")
REPORTS = os.path.join(SANDBOX, "reports")

configure_output()

def _load(name, *parts):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DRIVERS, *parts))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

inv = _load("sb_inventory", "repo-runner", "inventory.py")

def intake(source_id, from_path, note="", max_files=2000):
    src = os.path.abspath(os.path.expanduser(from_path))
    if not os.path.isdir(src):
        raise NotADirectoryError("источник не найден: %s" % src)
    os.makedirs(INBOX, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)

    # S3 read-only inventory: код НЕ запускается (allowed-root = сам источник)
    report = inv.scan_repo(src, max_files=max_files, base_dir=src)
    summary = report.get("summary", {}) if isinstance(report, dict) else {}
    risks = report.get("risks", []) if isinstance(report, dict) else []

    # S1 манифест источника (committable; сырой код — нет, см. sandbox/.gitignore)
    manifest = os.path.join(INBOX, "%s.md" % source_id)
    with open(manifest, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "---\nid: %s\ntype: external-source\nfrom: %s\nstatus: quarantine\nmode: read-only\n"
            "secrets: unknown-until-reviewed\nnote: %s\n---\n\n# Внешний источник: %s\n\n"
            "Зарегистрирован для read-only intake (D-016/D-017, контракт `docs/external-code-sandbox.md`).\n"
            "Код НЕ запускается до закрытия gate `docs/execute-sandbox-preflight.md`.\n"
            % (source_id, src, note, source_id)
        )

    # S7 read-only inventory report (committable summary)
    rep = os.path.join(REPORTS, "%s-inventory.md" % source_id)
    langs = summary.get("languages", summary.get("by_lang", {}))
    with open(rep, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Inventory: %s (read-only)\n\n" % source_id)
        f.write("- Источник: `%s`\n- Файлов: %s\n- Языки: %s\n- Есть тесты: %s\n- Помечено рисков: %d\n\n"
                % (src, summary.get("files", summary.get("file_count", "?")), langs,
                   summary.get("has_tests"), len(risks)))
        if risks:
            f.write("## Риск-файлы (только пометка, НЕ запуск)\n")
            for r in risks[:50]:
                f.write("- %s\n" % (r if isinstance(r, str) else r.get("path", r)))
        f.write("\nКод НЕ запускался (read-only). Следующее — обсуждение и решение по "
                "`docs/execute-sandbox-preflight.md`.\n")
    return {"manifest": manifest, "report": rep, "files": summary.get("files"),
            "risks": len(risks)}

def list_sources():
    out = []
    if os.path.isdir(INBOX):
        for fn in sorted(os.listdir(INBOX)):
            if fn.endswith(".md") and fn != "README.md":
                out.append(fn[:-3])
    return out

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        if cmd == "list":
            for s in list_sources():
                print(s)
            return 0
        if cmd == "intake" and len(a) > 1 and "--from" in a:
            frm = a[a.index("--from") + 1]
            note = a[a.index("--note") + 1] if "--note" in a else ""
            r = intake(a[1], frm, note=note)
            print("intake %s: файлов=%s рисков=%d → %s ; %s"
                  % (a[1], r["files"], r["risks"], r["manifest"], r["report"]))
            return 0
    except Exception as exc:
        print("ОШИБКА: %s: %s" % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2

if __name__ == "__main__":
    sys.exit(main())
