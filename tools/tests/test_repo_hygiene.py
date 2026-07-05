"""Тест repo_hygiene.py — классификация porcelain · gitignore-предложения (дедуп) · score · sandbox visibility · WARN личных путей (C46)."""
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
sys.path.insert(0, HERE)
import repo_hygiene as rh

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []
    lines = [
        "?? sandbox/canvas-demo/",                  # scratch runtime sandbox
        "?? sandbox/tvcp_fetched/",                 # other: внешний intake должен оставаться видимым
        "?? reports/audit_20260626_151910.json",    # scratch
        "?? reports/output_x.log",                  # scratch
        "?? queues/commit-queue/123-abc.json",      # scratch
        "?? _picks.json",                           # scratch
        "?? topics/new-real-topic.md",              # canon-md (работа без коммита)
        "?? test_guard.md",                         # scratch known guard
        "?? somedir/newtool.py",                    # other
        "A  queues/outbox/codex.md",                # staged (риск)
        " M tools/view.py",                         # НЕ staged (рабочая правка, X=' ')
    ]
    c = rh.classify(lines)

    if set(c["scratch"]) != {"sandbox/canvas-demo/", "reports/audit_20260626_151910.json",
                             "reports/output_x.log", "queues/commit-queue/123-abc.json", "_picks.json", "test_guard.md"}:
        fails.append("scratch неверно: %s" % c["scratch"])
    if c["canon_md"] != ["topics/new-real-topic.md"]:
        fails.append("canon-md должно быть [topics/new-real-topic.md]: %s" % c["canon_md"])
    if c["stray_root"] != []:
        fails.append("stray-root должен быть пустым: %s" % c["stray_root"])
    if c["other"] != ["sandbox/tvcp_fetched/", "somedir/newtool.py"]:
        fails.append("other должно быть [sandbox/tvcp_fetched/, somedir/newtool.py]: %s" % c["other"])
    if c["staged"] != ["queues/outbox/codex.md"]:
        fails.append("staged (X≠пробел) должно быть [queues/outbox/codex.md]: %s" % c["staged"])

    # gitignore-предложения: класс-паттерны, дедуп, исключая существующие
    sugg = rh.gitignore_suggestions(c["scratch"], existing_patterns={"sandbox/canvas-demo/"})
    if "sandbox/canvas-demo/" in sugg:
        fails.append("уже существующий паттерн sandbox/canvas-demo/ не должен предлагаться")
    for need in ("reports/audit_*.json", "reports/output_*.log", "queues/commit-queue/", "_picks.json", "test_guard.md"):
        if need not in sugg:
            fails.append("должен предложить %s: %s" % (need, sugg))
    if len(sugg) != len(set(sugg)):
        fails.append("предложения должны быть без дублей: %s" % sugg)

    # маппинг паттернов
    if rh._gitignore_pattern("sandbox/a/b") is not None:
        fails.append("обычный sandbox не должен скрываться целиком")
    if rh._gitignore_pattern("sandbox/canvas-demo/a") != "sandbox/canvas-demo/":
        fails.append("sandbox/canvas-demo → sandbox/canvas-demo/")
    if rh._gitignore_pattern("reports/README.md") is not None:
        fails.append("reports/README.md (канон) НЕ должен давать паттерн")

    # score: чисто → 100; грязно → ниже
    if rh.hygiene_score({"scratch": [], "stray_root": [], "staged": [], "other": [], "canon_md": []}) != 100:
        fails.append("чистое дерево → score 100")
    s = rh.hygiene_score(c)
    if not (0 <= s < 100):
        fails.append("грязное дерево → score < 100: %s" % s)

    # is_scratch не ловит канон
    if rh.is_scratch("topics/x.md") or rh.is_scratch("decisions/D-001.md"):
        fails.append("канон не должен считаться scratch")
    if not rh.is_scratch("queues/commit-queue/x.json"):
        fails.append("commit-queue тикет = scratch")

    # WARN на личные абсолютные пути в новых файлах (аудит C46). Фикстуры собираем
    # конкатенацией, чтобы сам тест-файл не содержал буквального личного пути.
    users_bs = "C:" + "\\Users\\"
    users_fwd = "C:" + "/Users/"
    if rh.personal_path_hits("см. " + users_bs + "someuser" + "\\Documents\\x.md") == []:
        fails.append("личный путь (backslash) должен давать WARN")
    if rh.personal_path_hits("root=" + users_fwd + "someuser" + "/proj") == []:
        fails.append("личный путь (forward slash) должен давать WARN")
    if rh.personal_path_hits(users_bs + "<user>" + "\\x.txt") != []:
        fails.append("плейсхолдер <user> НЕ личный путь")
    if rh.personal_path_hits(users_fwd + "Public" + "/shared.txt") != []:
        fails.append("Users/Public НЕ личный путь")
    if rh.personal_path_hits("relative/users/x.md и D:/data/users.txt") != []:
        fails.append("относительные пути и не-Users-каталоги не должны WARNить")
    dup = users_fwd + "someuser" + "/a.txt"
    hits = rh.personal_path_hits(dup + " и снова " + dup)
    if len(hits) != 1:
        fails.append("дедуп совпадений WARN: %s" % hits)

    if fails:
        print("FAIL test_repo_hygiene:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_repo_hygiene: классификация(scratch/canon/stray/other/staged) · gitignore-дедуп · score · паттерны · канон≠scratch · WARN личных путей (C46)")


if __name__ == "__main__":
    main()
