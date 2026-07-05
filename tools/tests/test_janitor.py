#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_janitor
# TYPE: test-script
# DOMAIN: core.hygiene
# DEPTH_LEVEL: 1
# SUMMARY: Тест janitor.py: dry-run ничего не удаляет и верно перечисляет кандидатов; --delete работает только на фикстуре.
# ==========================================
"""Тест janitor.py — dry-run не удаляет · кандидаты по всем секциям · ledger/хвост защищены · --delete на фикстуре."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import janitor  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

NOW = datetime(2026, 7, 5, 12, 0, 0)


def _touch(path, content="x", mtime=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    if mtime is not None:
        ts = mtime.timestamp()
        os.utime(path, (ts, ts))


def _snapshot(root):
    """Полный список путей внутри фикстуры (для проверки «ничего не удалено»)."""
    out = []
    for base, dirs, files in os.walk(root):
        for name in dirs + files:
            out.append(os.path.relpath(os.path.join(base, name), root).replace("\\", "/"))
    return sorted(out)


def build_fixture(root):
    """Мини-репозиторий: 3 audit-пары, reflection с ledger/0-байтной, tmp-work, dialog.md."""
    # 3 пары audit/output + непарный audit + файл вне паттерна (не должен попасть в кандидаты)
    for stamp in ("20260601_100000", "20260615_100000", "20260701_100000"):
        _touch(os.path.join(root, "reports", "audit_%s.json" % stamp), "{}")
        _touch(os.path.join(root, "reports", "output_%s.log" % stamp), "log")
    _touch(os.path.join(root, "reports", "audit_20260520_090000.json"), "{}")   # непарный, самый старый
    _touch(os.path.join(root, "reports", "audit-claude-2026-07-02.json"), "{}")  # канон-отчёт, вне паттерна
    # reflection: ledger + 0-байтная + 3 обычных с разным mtime
    _touch(os.path.join(root, "logs", "reflection", "ledger.json"), "{}")
    _touch(os.path.join(root, "logs", "reflection", "empty.json"), "")
    _touch(os.path.join(root, "logs", "reflection", "old1.json"), "{}", NOW - timedelta(days=30))
    _touch(os.path.join(root, "logs", "reflection", "old2.json"), "{}", NOW - timedelta(days=20))
    _touch(os.path.join(root, "logs", "reflection", "new1.json"), "{}", NOW - timedelta(days=1))
    # tmp-work: старый файл, старый каталог, свежий файл
    _touch(os.path.join(root, "tmp-work", "stale.txt"), "old", NOW - timedelta(days=30))
    old_dir = os.path.join(root, "tmp-work", "stale_dir")
    _touch(os.path.join(old_dir, "inner.txt"), "x")
    ts = (NOW - timedelta(days=30)).timestamp()
    os.utime(old_dir, (ts, ts))
    _touch(os.path.join(root, "tmp-work", "fresh.txt"), "new", NOW - timedelta(days=1))
    # dialog.md: преамбула + 4 реплики (2 старых, 2 свежих)
    dialog = "\n".join([
        "# Общая лента", "", "Преамбула.", "", "---", "",
        "### 2026-03-01 10:00 - Codex", "", "Старая реплика номер один.", "",
        "### 2026-04-02 11:30 - Claude", "", "Старая реплика номер два.", "",
        "### 2026-07-01 09:00 - Mavis", "", "Свежая реплика.", "",
        "### 2026-07-04 18:00 - Codex", "", "Самая свежая реплика.", "",
    ])
    _touch(os.path.join(root, "dialog.md"), dialog)


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="janitor_test_")
    try:
        build_fixture(tmp)
        before = _snapshot(tmp)
        args = janitor.parse_args([
            "--root", tmp, "--keep-audits", "2", "--keep-reflections", "2",
            "--tmp-age-days", "14", "--dialog-age-weeks", "8", "--dialog-keep-last", "1",
            "--now", NOW.isoformat(),
        ])
        report = janitor.collect(tmp, args, NOW)

        # 1) dry-run: сбор отчёта НИЧЕГО не удаляет
        if _snapshot(tmp) != before:
            fails.append("dry-run изменил фикстуру")
        if report["mode"] != "dry-run":
            fails.append("без --delete режим должен быть dry-run: %s" % report["mode"])

        # 2) audit-пары: keep=2 → старые 20260601 (пара) и 20260520 (непарный) — кандидаты
        a = report["sections"]["audit_reports"]
        cand_a = sorted(c["path"] for c in a["candidates"])
        want_a = ["audit_20260520_090000.json", "audit_20260601_100000.json", "output_20260601_100000.log"]
        if cand_a != want_a:
            fails.append("audit-кандидаты неверны: %s (ждали %s)" % (cand_a, want_a))
        if "audit-claude-2026-07-02.json" in cand_a:
            fails.append("канон-отчёт вне паттерна не должен быть кандидатом")
        if a["pairs_total"] != 4:
            fails.append("pairs_total должен быть 4 (3 пары + непарный stamp): %s" % a["pairs_total"])

        # 3) reflection: 0-байтная всегда кандидат; keep=2 → old1 сверх лимита; ledger защищён
        r = report["sections"]["reflection"]
        cand_r = sorted(c["path"] for c in r["candidates"])
        if cand_r != ["empty.json", "old1.json"]:
            fails.append("reflection-кандидаты неверны: %s" % cand_r)
        if any(c["path"] == "ledger.json" for c in r["candidates"]):
            fails.append("ledger.json никогда не должен быть кандидатом")

        # 4) tmp-work: старше 14 дн. — stale.txt и stale_dir; fresh.txt остаётся
        t = report["sections"]["tmp_work"]
        cand_t = sorted(c["path"] for c in t["candidates"])
        if cand_t != ["stale.txt", "stale_dir"]:
            fails.append("tmp-work кандидаты неверны: %s" % cand_t)

        # 5) dialog: 2 старых реплики → архивы 2026-03 и 2026-04; хвост (keep_last=1) защищён
        d = report["sections"]["dialog"]
        if d["candidates_total"] != 2:
            fails.append("dialog: ждали 2 кандидата, есть %s" % d["candidates_total"])
        if sorted(d["archives"]) != ["dialog-archive-2026-03.md", "dialog-archive-2026-04.md"]:
            fails.append("dialog: архивы неверны: %s" % sorted(d["archives"]))
        if d["entries_total"] != 4:
            fails.append("dialog: ждали 4 реплики, есть %s" % d["entries_total"])

        # 5б) хвост сильнее возраста: keep_last=4 закрывает ВСЕ реплики от ротации
        args_tail = janitor.parse_args(["--root", tmp, "--dialog-keep-last", "4",
                                        "--dialog-age-weeks", "8", "--now", NOW.isoformat()])
        d_tail = janitor.collect(tmp, args_tail, NOW)["sections"]["dialog"]
        if d_tail["candidates_total"] != 0:
            fails.append("dialog: keep_last=4 должен защитить все реплики: %s" % d_tail["candidates_total"])

        # 6) main() dry-run через CLI: снова ничего не удалено, JSON валиден
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = janitor.main(["--root", tmp, "--keep-audits", "2", "--keep-reflections", "2",
                               "--tmp-age-days", "14", "--now", NOW.isoformat(), "--json"])
        if rc != 0:
            fails.append("main() dry-run должен вернуть 0: %s" % rc)
        data = json.loads(buf.getvalue())
        if data["deletable_total"] != 7:  # 3 (audit) + 2 (reflection) + 2 (tmp-work)
            fails.append("deletable_total должен быть 7: %s" % data["deletable_total"])
        if "deleted" in data:
            fails.append("dry-run не должен содержать ключ deleted")
        if _snapshot(tmp) != before:
            fails.append("main() dry-run изменил фикстуру")

        # 7) --delete НА ФИКСТУРЕ (не на репозитории): кандидаты удалены, остальное цело,
        #    dialog.md не изменён даже в delete-режиме
        with open(os.path.join(tmp, "dialog.md"), encoding="utf-8") as f:
            dialog_before = f.read()
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = janitor.main(["--root", tmp, "--keep-audits", "2", "--keep-reflections", "2",
                                "--tmp-age-days", "14", "--now", NOW.isoformat(),
                                "--delete", "--json"])
        if rc2 != 0:
            fails.append("main() --delete должен вернуть 0: %s" % rc2)
        data2 = json.loads(buf2.getvalue())
        if len(data2.get("deleted", [])) != 7:
            fails.append("--delete должен удалить 7 кандидатов: %s" % data2.get("deleted"))
        after = _snapshot(tmp)
        for gone in ("reports/audit_20260601_100000.json", "logs/reflection/empty.json",
                     "tmp-work/stale.txt", "tmp-work/stale_dir"):
            if gone in after:
                fails.append("--delete не удалил кандидата %s" % gone)
        for kept in ("reports/audit_20260701_100000.json", "reports/audit-claude-2026-07-02.json",
                     "logs/reflection/ledger.json", "logs/reflection/new1.json", "tmp-work/fresh.txt"):
            if kept not in after:
                fails.append("--delete удалил защищённый файл %s" % kept)
        with open(os.path.join(tmp, "dialog.md"), encoding="utf-8") as f:
            if f.read() != dialog_before:
                fails.append("dialog.md изменён — перенос реплик запрещён даже при --delete (Q-W2-17)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("FAIL test_janitor:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_janitor: dry-run не удаляет · кандидаты(audit-пары/reflection/tmp-work/dialog) · "
          "ledger+хвост+канон защищены · --delete только на фикстуре · dialog.md неприкосновенен")


def test_janitor():
    """Обёртка для pytest: main() падает через sys.exit(1) при провале."""
    main()


if __name__ == "__main__":
    main()
