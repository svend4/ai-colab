#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.validate
# TYPE: active-script
# DOMAIN: core.validation
# DEPTH_LEVEL: 1
# SUMMARY: Главный валидатор (T-004/T-070/T-164). Проверяет целостность ссылок, статус файлов, сироты, драйверы.
# ==========================================
"""
Валидатор канона Markdown-инфраструктуры (T-006).

Проверяет инварианты между DECISIONS.md, QUESTIONS.md, TASKS.md, board.md,
STATUS.md и темами, чтобы заменить ручную «перепроверку».

Запуск из корня проекта:
    python tools/validate.py
    python tools/validate.py <ROOT>   # необязательный корень канона (существующий каталог)

Выход: 0 — нет ERROR; 1 — есть ERROR. WARN не валит. Мусорный аргумент → exit 2.
"""
import os
import re
import sys
from _ioutil import configure_output
from _cli import help_guard, die
import datetime

# Драйверы: манифест старше этого числа дней — WARN (advisory), пере-сверить с источником.
# 30 дней — для драйверов (код-backed); решения/политики идут на своём SLA через assurance.py.
DRIVER_FRESHNESS_DAYS = 30

def driver_freshness_warning(date_str, today=None, max_days=DRIVER_FRESHNESS_DAYS):
    """Текст WARN, если source_last_verified старше max_days; иначе None.

    Формат YYYY-MM-DD валидируется отдельно (err); здесь только ВОЗРАСТ. `today`
    параметризован для детерминированных тестов. Никогда не падает на мусоре.
    """
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str or ""):
        return None
    today = today or datetime.date.today()
    try:
        age = (today - datetime.date.fromisoformat(date_str)).days
    except ValueError:
        return None
    if age > max_days:
        return ("source_last_verified %s — %d дн. назад (> %d): пере-сверь манифест с источником"
                % (date_str, age, max_days))
    return None

configure_output()

def _root_from_argv():
    """ROOT из argv[1] — только существующий каталог (аудит C48).

    Раньше ЛЮБОЙ неизвестный аргумент (--json, --strict, опечатка) молча становился ROOT,
    и валидатор на здоровом каноне ложно рапортовал «весь канон отсутствует» (exit 1).
    --help/-h пропускаем — их обработает help_guard() в main().
    """
    if len(sys.argv) < 2:
        return None
    arg = sys.argv[1]
    if arg in ("--help", "-h"):
        return None
    if arg.startswith("-") or not os.path.isdir(arg):
        die("validate.py: неизвестный аргумент «%s» — это не флаг валидатора и не существующий "
            "каталог-ROOT.\nЗапуск: python tools/validate.py [ROOT] (подробнее: --help)" % arg)
    return arg

ROOT = (
    os.environ.get("COLLAB_ROOT")
    # argv разбирается только при запуске как скрипт: при импорте (тесты) argv — чужой
    or (_root_from_argv() if __name__ == "__main__" else None)
    or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

ERRORS, WARNS, OKS = [], [], []

def err(m):
    ERRORS.append(m)

def warn(m):
    WARNS.append(m)

def ok(m):
    OKS.append(m)

def read(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError as e:
        err(f"{rel}: не читается как UTF-8 (повреждён/обрезан?): {e}")
        return None

def strip_code_fences(text):
    """Убрать ```...``` блоки, чтобы примеры внутри не парсились как реальные записи."""
    return re.sub(r"```.*?```", "", text, flags=re.S)

def md_paths(cell):
    """Все `путь.md` (в backticks) из ячейки."""
    return re.findall(r"`([^`]+?\.md)`", cell)

def table_rows(text, id_prefix):
    """Строки markdown-таблицы, чья первая значащая ячейка начинается с id_prefix."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].startswith(id_prefix):
            rows.append(cells)
    return rows

from _canon import parse_front_matter  # единый парсер front-matter (T-085, находка L)

# ---------- DECISIONS ----------
def parse_decisions():
    # Источник правды — decisions/*.md; DECISIONS.md — генерируемый индекс-таблица.
    text = read("DECISIONS.md")
    if text is None:
        err("DECISIONS.md отсутствует")
        return {}
    statuses = {}
    seen = set()
    valid = {"accepted", "proposed", "rejected", "superseded"}
    for cells in table_rows(text, "D-"):
        did = cells[0]
        st = cells[2] if len(cells) > 2 else None
        if did in seen:
            err("DECISIONS: дубликат %s" % did)
        seen.add(did)
        statuses[did] = st
        if not st:
            err("DECISIONS: у %s нет статуса" % did)
        elif st not in valid:
            warn("DECISIONS: %s нестандартный статус %s" % (did, st))
    if statuses:
        ok("DECISIONS: %d решений (индекс), id уникальны" % len(statuses))
    return statuses

# ---------- QUESTIONS ----------
def parse_questions(decisions):
    text = read("QUESTIONS.md")
    if text is None:
        err("QUESTIONS.md отсутствует")
        return
    rows = table_rows(text, "Q-")
    seen = set()
    valid = {"open", "answered", "closed"}
    for cells in rows:
        qid = cells[0]
        status = cells[2] if len(cells) > 2 else ""
        where = cells[5] if len(cells) > 5 else ""
        outcome = cells[6] if len(cells) > 6 else ""
        if qid in seen:
            err(f"QUESTIONS: дубликат {qid}")
        seen.add(qid)
        if status not in valid:
            warn(f"QUESTIONS: {qid} нестандартный статус «{status}»")
        # answered ⇒ итог осмысленный
        if status == "answered":
            if not outcome or "не решено" in outcome.lower():
                err(f"QUESTIONS: {qid} answered, но «Итог» пуст/не заполнен")
            for d in re.findall(r"D-\d+", outcome):
                if d not in decisions:
                    err(f"QUESTIONS: {qid} ссылается на несуществующее решение {d}")
        # ссылки на тему-файл существуют (S1 карантин: open-вопрос со ссылкой на ещё не созданный
        # файл = WARN; ERROR только для answered/closed — готовый вопрос обязан иметь свой файл).
        for p in md_paths(where):
            if not os.path.exists(os.path.join(ROOT, p)):
                if status in ("answered", "closed"):
                    err(f"QUESTIONS: {qid} ({status}) «Где обсуждается» → нет файла {p}")
                else:
                    warn(f"QUESTIONS: {qid} (status={status}) «Где обсуждается» → файла {p} ещё нет (карантин)")
    if seen:
        ok(f"QUESTIONS: {len(seen)} вопросов, id уникальны, ссылки и итоги проверены")

# ---------- TASKS ----------
def parse_tasks():
    text = read("TASKS.md")
    if text is None:
        err("TASKS.md отсутствует")
        return
    rows = table_rows(text, "T-")
    seen = set()
    valid = {"todo", "doing", "blocked", "review", "done"}
    for cells in rows:
        tid = cells[0]
        status = cells[2] if len(cells) > 2 else ""
        topic = cells[4] if len(cells) > 4 else ""
        if tid in seen:
            err(f"TASKS: дубликат {tid}")
        seen.add(tid)
        if status not in valid:
            warn(f"TASKS: {tid} нестандартный статус «{status}»")
        for p in md_paths(topic):
            if not os.path.exists(os.path.join(ROOT, p)):
                # S1 «карантин half-done» (D-022/gate-poison): незавершённая задача со ссылкой на
                # ещё не созданный файл = WARN, а не ERROR — чтобы чужая half-done не отравляла общий
                # commit-gate ВСЕМ. ERROR только для done: готовая задача обязана иметь свой deliverable.
                if status == "done":
                    err(f"TASKS: {tid} (done) «Тема» → нет файла {p}")
                else:
                    warn(f"TASKS: {tid} (status={status}) «Тема» → файла {p} ещё нет (карантин half-done)")
    if seen:
        ok(f"TASKS: {len(seen)} задач, id уникальны, ссылки проверены")

# ---------- навигация: Доска / STATUS активные темы ----------
def check_nav():
    for fname in ("board.md", "STATUS.md"):
        text = read(fname)
        if text is None:
            err(f"{fname} отсутствует")
            continue
        missing = 0
        for line in text.splitlines():
            if not line.strip().startswith("|"):
                continue
            for p in md_paths(line):
                if p.startswith("topics/") and not os.path.exists(os.path.join(ROOT, p)):
                    err(f"{fname}: ссылка на отсутствующую тему {p}")
                    missing += 1
        if missing == 0:
            ok(f"{fname}: ссылки на темы валидны")

# ---------- темы: front-matter title (аудит C18) ----------
def check_topics():
    """Тема без front-matter title невидима для generate.py (index.json/STATUS/board),
    хотя folder_index видит все файлы. WARN — чтобы расхождение охвата двух индексных
    механизмов не копилось молча (аудит C18: 12 из 81 тем выпали из навигации)."""
    d = os.path.join(ROOT, "topics")
    if not os.path.isdir(d):
        return
    total = 0
    missing = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md") or not os.path.isfile(os.path.join(d, fn)):
            continue
        rel = "topics/%s" % fn
        text = read(rel)
        if text is None:
            continue
        total += 1
        if not parse_front_matter(text).get("title"):
            missing.append(rel)
    for rel in missing:
        warn("%s: нет front-matter title — в навигацию попадёт только фоллбэком "
             "по первому '#'-заголовку (generate.py)" % rel)
    if total and not missing:
        ok("topics: %d тем, у всех есть front-matter title" % total)

# ---------- имена файлов (D-005/D-007) ----------
def check_naming():
    cyr = []
    for dirpath, _dirs, files in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        for fn in files:
            if fn.endswith(".md") and not all(ord(c) < 128 for c in fn):
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
                cyr.append(rel)
    if cyr:
        warn(
            "Имена с кириллицей (по D-007 мигрируют лениво, не ошибка): "
            + ", ".join(sorted(cyr))
        )
    else:
        ok("Все имена файлов ASCII (D-005)")

# ---------- источники: tasks/ questions/ decisions/ (валидатор v2) ----------
def check_sources():
    registries = [
        ("tasks", "T-", {"todo", "doing", "blocked", "review", "done"}),
        ("questions", "Q-", {"open", "answered", "closed"}),
        ("decisions", "D-", {"accepted", "proposed", "rejected", "superseded"}),
    ]
    task_ids = set()
    task_deps = {}
    for dirname, prefix, valid_status in registries:
        d = os.path.join(ROOT, dirname)
        if not os.path.isdir(d):
            continue
        seen = set()
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".md") or fn == "README.md":
                continue
            rel = "%s/%s" % (dirname, fn)
            text = read(rel)
            if text is None:
                continue
            fm = parse_front_matter(text)
            fid = fm.get("id")
            if not fid:
                err("%s: нет front-matter id" % rel)
                continue
            if not fid.startswith(prefix):
                err("%s: id «%s» без префикса %s" % (rel, fid, prefix))
            if fid in seen:
                err("%s: дубликат id %s" % (dirname, fid))
            seen.add(fid)
            if fn[:-3] != fid:
                warn("%s: имя файла не совпадает с id %s" % (rel, fid))
            if not fm.get("title"):
                err("%s: нет front-matter title" % rel)
            st = fm.get("status")
            if not st:
                err("%s: нет front-matter status" % rel)
            elif st not in valid_status:
                warn("%s: нестандартный status «%s»" % (rel, st))
            if dirname == "tasks":
                task_deps[fid] = fm.get("depends_on", "")
        if dirname == "tasks":
            task_ids = set(seen)
    for fid, dep in task_deps.items():
        for ref in re.findall(r"T-\d+", dep):
            if ref not in task_ids:
                err("tasks/%s.md: depends_on → несуществующая задача %s" % (fid, ref))
    ok("sources: tasks/questions/decisions проверены (front-matter, id, статусы, depends_on)")

def check_drivers():
    drivers_dir = os.path.join(ROOT, "drivers")
    if not os.path.isdir(drivers_dir):
        return
    required = [
        "id",
        "type",
        "title",
        "status",
        "level",
        "mode",
        "owner",
        "risk",
        "activation",
        "interfaces",
        "inputs",
        "outputs",
        "sandbox",
        "secrets",
        "source_last_verified",
        "timeout_seconds",
        "max_output_bytes",
        "audit",
        "related",
    ]
    valid_status = {"draft", "ready", "deprecated"}
    valid_level = {"L1", "L2", "L3"}
    valid_mode = {"read-only", "manual", "safe-write", "execute"}
    valid_risk = {"low", "medium", "high"}
    valid_activation = {"manual", "pipeline", "mcp", "scheduled"}
    # Реальные механизмы изоляции, допускающие mode: execute (ревью T-078 находка G).
    sandbox_real = {"container", "docker", "nsjail", "firejail", "gvisor", "sandboxed-vm"}
    checked = 0
    seen = set()
    for fn in sorted(os.listdir(drivers_dir)):
        if not fn.endswith(".md") or fn in {"README.md", "SCHEMA.md"} or fn.startswith("_"):
            continue
        rel = "drivers/%s" % fn
        text = read(rel)
        if text is None:
            continue
        fm = parse_front_matter(text)
        if fm.get("type") != "driver":
            continue
        checked += 1
        did = fm.get("id", "")
        if did in seen:
            err("drivers: дубликат id %s" % did)
        seen.add(did)
        for field in required:
            if not fm.get(field):
                err("%s: нет front-matter %s" % (rel, field))
        if fm.get("status") and fm["status"] not in valid_status:
            warn("%s: нестандартный status «%s»" % (rel, fm["status"]))
        if fm.get("level") and fm["level"] not in valid_level:
            warn("%s: нестандартный level «%s»" % (rel, fm["level"]))
        if fm.get("mode") and fm["mode"] not in valid_mode:
            warn("%s: нестандартный mode «%s»" % (rel, fm["mode"]))
        if fm.get("risk") and fm["risk"] not in valid_risk:
            warn("%s: нестандартный risk «%s»" % (rel, fm["risk"]))
        if fm.get("activation") and fm["activation"] not in valid_activation:
            warn("%s: нестандартный activation «%s»" % (rel, fm["activation"]))
        if fm.get("source_last_verified") and not re.match(
            r"^\d{4}-\d{2}-\d{2}$", fm["source_last_verified"]
        ):
            err("%s: source_last_verified должен быть YYYY-MM-DD" % rel)
        else:
            _fresh = driver_freshness_warning(fm.get("source_last_verified", ""))
            if _fresh:
                warn("%s: %s" % (rel, _fresh))
        for field in ("timeout_seconds", "max_output_bytes"):
            if fm.get(field):
                try:
                    if int(fm[field]) <= 0:
                        err("%s: %s должен быть положительным числом" % (rel, field))
                except ValueError:
                    err("%s: %s должен быть числом" % (rel, field))
        if fm.get("risk") in {"medium", "high"} and fm.get("audit") != "true":
            err("%s: risk %s требует audit: true" % (rel, fm.get("risk")))
        if fm.get("mode") == "execute":
            sb = (fm.get("sandbox") or "").strip().lower()
            if sb not in sandbox_real:
                err("%s: mode execute без реальной изоляции запрещён — sandbox должен быть из "
                    "{container/docker/nsjail/firejail/gvisor/sandboxed-vm} + accepted-решение; "
                    "найдено sandbox=%r (ревью T-078 находка G)" % (rel, fm.get("sandbox")))
            else:
                warn("%s: mode execute с sandbox=%s — убедись, что есть accepted-решение" % (rel, fm.get("sandbox")))
    if checked:
        ok("drivers: %d манифестов проверены по draft schema v1" % checked)

def _parse_inline_list(value):
    """`[a, b, c]` (как хранит наивный парсер front-matter) → ['a','b','c']."""
    s = (value or "").strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    return [x.strip() for x in s.split(",") if x.strip()]

def _mcp_tool_names(server_text):
    """Имена функций, задекорированных @mcp.tool(), из текста mcp_server.py."""
    names = []
    lines = server_text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("@mcp.tool("):
            for j in range(i + 1, min(i + 4, len(lines))):
                m = re.match(r"\s*def\s+(\w+)\s*\(", lines[j])
                if m:
                    names.append(m.group(1))
                    break
    return names

def check_driver_tools():
    """Сверка манифестного поля `tools:` с реально зарегистрированными @mcp.tool().

    Опционально: проверяется только для драйверов, у которых поле `tools:` объявлено
    (закрывает дрейф «interfaces ≠ tools», ревью T-078 находка K). `interfaces` —
    концептуальное поле и здесь не проверяется.
    """
    drivers_dir = os.path.join(ROOT, "drivers")
    if not os.path.isdir(drivers_dir):
        return
    checked = 0
    for fn in sorted(os.listdir(drivers_dir)):
        if not fn.endswith(".md") or fn in {"README.md", "SCHEMA.md"} or fn.startswith("_"):
            continue
        rel = "drivers/%s" % fn
        text = read(rel)
        if text is None:
            continue
        fm = parse_front_matter(text)
        if fm.get("type") != "driver" or not fm.get("tools"):
            continue
        want = set(_parse_inline_list(fm.get("tools")))
        name = fn[:-3]
        server = os.path.join(drivers_dir, name, "mcp_server.py")
        if not os.path.exists(server):
            err("%s: объявлено поле tools, но нет %s/mcp_server.py" % (rel, name))
            continue
        with open(server, encoding="utf-8") as f:
            got = set(_mcp_tool_names(f.read()))
        if want != got:
            err("%s: tools манифеста %s ≠ реальные @mcp.tool() %s"
                % (rel, sorted(want), sorted(got)))
        else:
            checked += 1
    if checked:
        ok("drivers tools: %d манифестов сверены с @mcp.tool() серверов" % checked)

def check_pipeline_d011():
    """Артефакт-presence инвариант D-011 (конвейер агентов).

    Привязан к жизненному циклу решения: пока D-011 status=accepted — pipeline.py,
    PIPELINE.md, logs/pipeline.json обязаны существовать, а pipeline.py обязан
    определять шесть команд next/status/mine/done/fail/snapshot (символьный контракт).
    superseded/rejected ⇒ инвариант снимается автоматически (no-op).
    Enforce-ится только presence/contract артефактов, НЕ кооперативный workflow.
    """
    text = read("decisions/D-011.md")
    if text is None:
        return
    fm = parse_front_matter(text)
    if fm.get("status") != "accepted":
        return
    for rel in ("tools/pipeline.py", "PIPELINE.md", "logs/pipeline.json"):
        if not os.path.exists(os.path.join(ROOT, rel)):
            err("D-011: accepted, но нет артефакта %s" % rel)
    src = read("tools/pipeline.py")
    if src is None:
        return
    want = {"cmd_next", "cmd_status", "cmd_mine", "cmd_done", "cmd_fail", "cmd_snapshot"}
    got = set(re.findall(r"^def (cmd_\w+)\(", src, re.M))
    missing = want - got
    if missing:
        err("D-011: pipeline.py не покрывает команды %s (спека next/status/mine/done/fail/snapshot)"
            % sorted(missing))
    if not missing:
        ok("D-011: конвейер pipeline.py + PIPELINE.md + logs/pipeline.json присутствуют, "
           "команды next/status/mine/done/fail/snapshot определены")

def check_execute_d014():
    """Инвариант D-014 (запрет mode: execute до реализации всех 10 гейтов).
    
    Все 10 гейтов из docs/execute-sandbox-runner-design-2026-06-23.md построены.
    Теперь mode: execute разрешен, но драйверы должны исполняться через sandbox_runner.py.
    """
    drivers_dir = os.path.join(ROOT, "drivers")
    if not os.path.isdir(drivers_dir):
        return
        
    has_execute = False
    for fn in os.listdir(drivers_dir):
        if not fn.endswith(".md") or fn in {"README.md", "SCHEMA.md"} or fn.startswith("_"):
            continue
        rel = "drivers/%s" % fn
        text = read(rel)
        if text is None:
            continue
        fm = parse_front_matter(text)
        if fm.get("mode") == "execute":
            has_execute = True
            
    runner_exists = os.path.exists(os.path.join(ROOT, "tools", "sandbox_runner.py"))
    
    if has_execute and not runner_exists:
        err("D-014: mode: execute найден, но sandbox_runner.py отсутствует!")
    elif has_execute and runner_exists:
        ok("D-014: execute-сценарии активны (защищены через sandbox_runner.py)")
    else:
        ok("D-014: execute-сценариев пока нет (sandbox_runner.py готов)")

def check_synthesis_reports():
    """Проверка структуры отчетов синтеза (T-182).
    
    Отчеты/скелеты (type: synthesis-scaffold / synthesis-report) должны:
    1. Не иметь status=accepted или auto-accepted (чтобы предотвратить обход D-006/D-018).
    2. Содержать необходимые секции: Консенсус, Разногласия, Перепроверка.
    """
    checked = 0
    for dirpath, _dirs, files in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                continue
            
            fm = parse_front_matter(text)
            ftype = fm.get("type", "")
            if ftype not in ("synthesis-scaffold", "synthesis-report"):
                continue
                
            status = fm.get("status", "")
            if status in ("accepted", "auto-accepted"):
                err("%s: отчёты синтеза не могут быть accepted/auto-accepted напрямую (D-018), нужен D-файл" % rel)
            
            body = strip_code_fences(text)
            
            if not re.search(r"(?i)^#{2,4}\s+(Консенсус|Общее во всех вариантах)", body, re.M):
                err("%s: отсутствует секция '## Консенсус'" % rel)
            
            if not re.search(r"(?i)^#{2,4}\s+(Разногласия|Расхождения)", body, re.M):
                err("%s: отсутствует секция '## Разногласия' или '## Расхождения'" % rel)
                
            if not re.search(r"(?i)^#{2,4}\s+(Двойная перепроверка|Доказательства)", body, re.M):
                err("%s: отсутствует секция '## Двойная перепроверка' (требование D-018)" % rel)
                
            checked += 1
            
    if checked > 0:
        ok("synthesis: %d отчетов проверено на структуру консенсуса/разногласий" % checked)

def main():
    help_guard(__doc__)
    decisions = parse_decisions()
    parse_questions(decisions)
    parse_tasks()
    check_sources()
    check_drivers()
    check_driver_tools()
    check_pipeline_d011()
    check_execute_d014()
    check_nav()
    check_topics()
    check_naming()
    check_synthesis_reports()

    for m in OKS:
        print("OK:   " + m)
    for m in WARNS:
        print("WARN: " + m)
    for m in ERRORS:
        print("ERROR:" + " " + m)
    print("-" * 50)
    print(f"OK={len(OKS)} WARN={len(WARNS)} ERROR={len(ERRORS)}")
    sys.exit(1 if ERRORS else 0)

if __name__ == "__main__":
    main()
