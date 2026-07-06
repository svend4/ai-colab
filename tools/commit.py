# ast: allow-subprocess
#!/usr/bin/env python3
# [FILE ID CARD]
# id: tools/commit.py
# purpose: Безопасная обёртка коммита — убирает нужду в `git commit --no-verify`
#          и `git add -A`. Стейджит только явные пути, ловит массовое удаление
#          (D-026) ДО коммита, гоняет guard'ы, коммитит БЕЗ обхода хуков.
# inputs: список путей зоны + сообщение; opts --agent --allow-deletions N
# outputs: коммит (или отказ с диагнозом); exit 0/1/2
# mode: write (git commit), но безопасно — с проверками и без --no-verify
# related: D-026 (запрет bulk-стирания), bulk_guard.py, tools/githooks/pre-commit
"""commit.py — безопасная обёртка коммита (D-026, анти-`--no-verify`).

Почему: `git commit --no-verify` выключает ВЕСЬ pre-commit, включая bulk_guard
(страховку от массового удаления). Причина, по которой агенты тянутся к
`--no-verify` — pre-commit блокирует по чужому entangled-навигационному состоянию
в общем дереве. Эта обёртка убирает причину: стейджит ТОЛЬКО объявленную зону
(никогда `-A`), сама ловит массовое удаление, и коммитит БЕЗ обхода хуков.

Инварианты:
  1. Стейджит только явные пути; `-A`, `.`, `*` — ОТКАЗ.
  2. Считает удаления в staged; > порога без --allow-deletions <N> — ОТКАЗ (D-026).
  3. Прогоняет bulk_guard.py --staged (если есть) и validate.py (ERROR=0).
  4. `git commit` БЕЗ `--no-verify` — хуки остаются финальным гейтом.

Использование:
  python tools/commit.py <path> [<path>...] -m "сообщение" [--agent claude]
      [--allow-deletions N]   # осознанно разрешить до N удалений (с обоснованием в msg)
  python tools/commit.py --help
Коды выхода: 0 успех; 1 отказ по безопасности; 2 ошибка использования/git.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys

# UTF-8 вывод в Windows-консоли (cp1252 не кодирует кириллицу — F-006 mojibake).
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# Порог массового удаления по умолчанию (согласован с bulk_guard/D-026).
DELETION_THRESHOLD = 5
FORBIDDEN_PATHSPECS = {"-A", "--all", ".", "*", ":/", "-u", "--update"}


def _run(args, **kw):
    """Запуск git/py без падения; возвращает CompletedProcess."""
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def _git(*args):
    return _run(["git", *args])


def _repo_root() -> str:
    r = _git("rev-parse", "--show-toplevel")
    return r.stdout.strip() if r.returncode == 0 else os.getcwd()


def _staged_name_status():
    """Список (status, path) staged-изменений."""
    r = _git("diff", "--cached", "--name-status")
    out = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            out.append((parts[0][0], parts[-1]))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="commit.py",
        description="Безопасная обёртка коммита (D-026, без --no-verify / без git add -A).")
    p.add_argument("paths", nargs="*", help="явные пути зоны для коммита")
    p.add_argument("-m", "--message", required=False, help="сообщение коммита")
    p.add_argument("--agent", default=os.environ.get("CANON_AGENT", ""),
                   help="имя агента (для провенанса)")
    p.add_argument("--allow-deletions", type=int, default=0,
                   help="осознанно разрешить до N удалений (обоснуй в сообщении)")
    p.add_argument("--dry-run", action="store_true",
                   help="проверить и показать план, НЕ коммитить")
    # --- Пред-скан argv ДО argparse: словить -A/./*/-u раньше, чем argparse
    #     отвергнет их своим кодом 2 с невнятным сообщением ---
    raw = list(argv) if argv is not None else sys.argv[1:]
    hit = [x for x in raw if x in FORBIDDEN_PATHSPECS]
    if hit:
        print(f"ОТКАЗ: запрещённые pathspec {hit}. Массовый стейдж "
              f"(`-A`/`.`/`*`/`-u`) запрещён (D-026) — перечисли конкретные файлы.",
              file=sys.stderr)
        return 1

    args = p.parse_args(argv)

    # --- Инвариант 1: явные пути, никаких wildcard/-A ---
    if not args.paths:
        print("ОТКАЗ: не заданы явные пути зоны. Обёртка не делает `git add -A`.\n"
              "       Укажи файлы: python tools/commit.py <файл>... -m \"...\"", file=sys.stderr)
        return 2
    bad = [x for x in args.paths if x in FORBIDDEN_PATHSPECS]
    if bad:
        print(f"ОТКАЗ: запрещённые pathspec {bad}. Массовый стейдж (`-A`/`.`/`*`) "
              f"запрещён (D-026) — перечисли конкретные файлы.", file=sys.stderr)
        return 1
    if not args.message and not args.dry_run:
        print("ОТКАЗ: нужно -m \"сообщение\".", file=sys.stderr)
        return 2

    root = _repo_root()
    os.chdir(root)

    # --- Стейдж только явных путей ---
    add = _git("add", "--", *args.paths)
    if add.returncode != 0:
        print(f"ОТКАЗ: git add не прошёл:\n{add.stderr}", file=sys.stderr)
        return 2

    staged = _staged_name_status()
    if not staged:
        print("ОТКАЗ: после стейджа указанных путей нечего коммитить "
              "(нет изменений в этих файлах).", file=sys.stderr)
        return 1

    dels = [pth for st, pth in staged if st == "D"]
    print(f"Staged: {len(staged)} файлов ({len(dels)} удалений). Зона: {args.paths}")

    # --- Инвариант 2: порог массового удаления (D-026) ---
    if len(dels) > max(args.allow_deletions, DELETION_THRESHOLD if args.allow_deletions else 0):
        if len(dels) > args.allow_deletions:
            print(f"\n*** ОТКАЗ (D-026): в staged {len(dels)} удалений, "
                  f"порог {args.allow_deletions}. ***\n"
                  f"Массовое удаление файлов запрещено недеструктивной политикой.\n"
                  f"Удаляемые файлы:", file=sys.stderr)
            for d in dels[:30]:
                print(f"   - {d}", file=sys.stderr)
            if len(dels) > 30:
                print(f"   ... ещё {len(dels) - 30}", file=sys.stderr)
            print("\nЕсли удаление осознанно и мало — повтори с --allow-deletions <N> "
                  "и обоснованием в сообщении. Массовое стирание истории — только через\n"
                  "accepted-решение и человека (reconcile: помечай closed/deprecated, не удаляй).",
                  file=sys.stderr)
            # снять со стейджа, чтобы не оставлять опасное staged-состояние
            _git("reset", "--quiet", "HEAD", "--", *args.paths)
            return 1

    # --- Инвариант 3: guard'ы ДО коммита ---
    def _guard(name, cmd):
        r = _run(cmd)
        ok = r.returncode == 0
        tail = (r.stdout or r.stderr or "").strip().splitlines()[-1:] or [""]
        print(f"  [{'OK ' if ok else 'FAIL'}] {name}: {tail[0][:120]}")
        return ok, r

    py = sys.executable
    print("Быстрые проверки перед коммитом (validate/generate/gap_scan — в pre-commit хуке):")
    # bulk_guard на staged, если есть — это БЫСТРАЯ ключевая проверка D-026.
    # validate.py НЕ дублируем здесь: его гоняет pre-commit хук как финальный гейт
    # (двойной прогон удваивал время до таймаута).
    if os.path.exists(os.path.join("tools", "bulk_guard.py")):
        okb, rb = _guard("bulk_guard", [py, "tools/bulk_guard.py", "--staged"])
        if not okb and "ERROR" in (rb.stdout + rb.stderr).upper():
            print("ОТКАЗ: bulk_guard заблокировал (массовое стирание) — не коммичу.", file=sys.stderr)
            _git("reset", "--quiet", "HEAD", "--", *args.paths)
            return 1

    if args.dry_run:
        print("\n[dry-run] Проверки пройдены. Коммит НЕ сделан. Снимаю staged.")
        _git("reset", "--quiet", "HEAD", "--", *args.paths)
        return 0

    # --- Инвариант 4: git commit БЕЗ --no-verify (хуки — финальный гейт) ---
    msg = args.message
    if args.agent and "Co-Authored-By" not in msg:
        msg += f"\n\n(агент: {args.agent}; безопасный коммит через tools/commit.py, без --no-verify)"
    cm = _run(["git", "commit", "-m", msg])  # НЕТ --no-verify — принципиально
    print(cm.stdout.strip()[-500:])
    if cm.returncode != 0:
        print(f"Коммит не прошёл (хук/гейт заблокировал — это ПРАВИЛЬНО, "
              f"не обходи через --no-verify):\n{cm.stderr[-800:]}", file=sys.stderr)
        return 1
    print("OK: коммит сделан безопасно (хуки отработали, --no-verify не использован).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
