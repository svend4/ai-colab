#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.status_drift
# TYPE: active-script
# DOMAIN: core.drift
# DEPTH_LEVEL: 1
# SUMMARY: Advisory-детектор рассинхрона ручных утверждений STATUS.md с машинной реальностью канона (C17).
# ==========================================
"""
status_drift.py — детектор рассинхрона ручного текста STATUS.md с фактами канона (находка C17 mavis).

C17: секция «Текущий фокус» STATUS.md — ручной прозаический текст, который отстаёт от реальности.
Пример из ревью mavis: строка «7 нератифицированных: D-024, D-026, D-027, D-028, D-030, D-032, D-033»,
хотя 6 из 7 решений уже accepted (реально proposed только D-033). Числа задач/решений/тем в ручной
прозе тоже дрейфуют (аудит 2026-07-02 нашёл отставание на десятки; те счётчики с тех пор вынесены
в GEN-блок, но ручная проза вне GEN-блоков всё ещё может утверждать неверное).

Детектор СРАВНИВАЕТ утверждения в РУЧНЫХ секциях STATUS.md (строки ВНЕ `<!-- GEN:... -->`-блоков,
которые генерируются автоматически и не могут устареть) с машинной реальностью:

  (a) числовые утверждения «N задач/решений/вопросов/тем/драйверов» vs фактические счётчики
      (из index.json, фоллбэк — подсчёт файлов-источников канона);
  (b) утверждения о статусах решений — «N нератифицированных/proposed: D-XXX, D-YYY, ...» — vs
      фактический front-matter decisions/D-*.md (нератифицированное = статус НЕ accepted): проверяется
      и число, и что каждый перечисленный D-id реально нератифицирован;
  (c) ссылки на задачи в блоке «текущий фокус» — закрыта ли задача (status done). Задача, поданная
      как ЖИВОЙ фокус, но уже done — дрейф (фокус описывает несуществующую работу).

Всё read-only и advisory. STATUS.md НЕ правится: это генерируемо-ручной гибрид (GEN-блоки +
ручная проза), ручная правка канона запрещена — детектор только СИГНАЛИТ (dry-run).

CLI:
    python tools/status_drift.py            # check по умолчанию, человекочитаемо
    python tools/status_drift.py check      # то же явно
    python tools/status_drift.py check --json
    python tools/status_drift.py --help

exit 0 — расхождений не найдено; exit 1 — есть расхождения (advisory-сигнал, не блокирует).
"""
import os
import sys
import re
import glob
import json

from _ioutil import configure_output
from _cli import help_guard
from _canon import parse_front_matter

configure_output()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Метки существительных канона → ключ секции index.json (и каталог-источник для фоллбэка счёта).
# Ключ — регэксп-основа существительного в родительном/множественном (русская проза STATUS.md),
# value — (index.json-секция, каталог-источник, префикс id для подсчёта файлов).
_NOUNS = (
    ("задач", "tasks", "tasks", "T-"),
    ("решени", "decisions", "decisions", "D-"),
    ("вопрос", "questions", "questions", "Q-"),
    ("тем", "topics", "topics", None),      # тем в навигации; файлы topics/*.md без строгого префикса
    ("драйвер", "drivers", "drivers", None),
)

# «Нератифицированное» решение = статус НЕ accepted (proposed/draft/superseded и т.п. — не ратифицировано
# человеком как действующее). accepted — единственный статус «ратифицировано».
_RATIFIED_STATUS = "accepted"

# Ссылка на решение/задачу в тексте.
_DEC_RE = re.compile(r"\bD-\d{3}\b")
_TASK_RE = re.compile(r"\bT-\d{3}\b")

# Утверждение о нератифицированных решениях: «N нератифицированных» / «N proposed» рядом со списком D-id.
# Ловим число + список решений в той же строке (проза STATUS.md держит их вместе, напр.
# «7 нератифицированных: D-024, D-026, ...»).
_UNRATIFIED_RE = re.compile(
    r"(\d+)\s*(?:нератифицирован\w*|proposed|непринят\w*|не\s+ратифицирован\w*)", re.IGNORECASE)

# Маркеры строки, которая говорит о ПРОШЛОМ (delta/находка/аудит/дата), а не утверждает ТЕКУЩИЙ
# счётчик. Числа в такой строке — историческое повествование («отстали на 59 задач», «волна 1
# (27 находок)»), не живое утверждение о размере канона; числовую сверку (a) на них НЕ делаем,
# иначе повествование о самом дрейфе C17 даёт ложные срабатывания. Датированная строка (YYYY-MM-DD
# или явный «аудит 2026-…») — тоже историческая запись.
_DELTA_MARKERS = (
    "отстал", "находк", "волна", "волны", "delta", "дельта", "устарел",
    "было ", "стало ", "закоммичен", "верифицирован", "заморозк", "стабилизацион",
)
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def _read(path):
    """Прочитать текст файла (utf-8, replace); отсутствующий/битый → пустая строка (advisory не падает)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def strip_gen_blocks(text):
    """Убрать содержимое GEN-блоков `<!-- GEN:x START ... --> ... <!-- GEN:x END -->`.

    Возвращает текст ТОЛЬКО ручных секций (генерируемые блоки не могут устареть — сравнивать
    надо ручную прозу). Реализация построчная, чтобы номера оставшихся строк были осмысленны
    в сообщениях: строки внутри GEN-диапазона заменяются пустой строкой (нумерация сохраняется).
    Незакрытый START (нет END) — выкидываем всё до конца файла (безопасный дефолт: не считаем
    генерируемый хвост ручным)."""
    lines = text.splitlines()
    out = []
    in_gen = False
    for line in lines:
        if not in_gen and re.search(r"<!--\s*GEN:[\w-]+\s+START", line):
            in_gen = True
            out.append("")  # сама строка-маркер — тоже не ручная проза
            continue
        if in_gen:
            out.append("")
            if re.search(r"<!--\s*GEN:[\w-]+\s+END", line):
                in_gen = False
            continue
        out.append(line)
    return "\n".join(out)


def manual_lines(text):
    """Список (номер_строки, текст) ручных (не-GEN) непустых строк STATUS.md."""
    stripped = strip_gen_blocks(text)
    result = []
    for i, line in enumerate(stripped.splitlines(), start=1):
        if line.strip():
            result.append((i, line))
    return result


def canon_counts(root):
    """Фактические счётчики канона: {секция: N}. Источник — index.json; фоллбэк — счёт файлов.

    index.json — генерируемый машинный индекс (актуальность гарантирует generate.py --check),
    поэтому он авторитетнее ручной прозы. Если index.json недоступен/битый — считаем файлы-источники
    напрямую (tasks/T-*.md и т.п.), чтобы детектор оставался работоспособным без индекса.
    """
    counts = {}
    idx = _read(os.path.join(root, "index.json"))
    data = None
    if idx:
        try:
            data = json.loads(idx)
        except ValueError:
            data = None
    for _noun, section, srcdir, prefix in _NOUNS:
        n = None
        if isinstance(data, dict) and isinstance(data.get(section), list):
            n = len(data[section])
        if n is None:
            pat = os.path.join(root, srcdir, ("%s*.md" % prefix) if prefix else "*.md")
            files = [f for f in glob.glob(pat) if os.path.basename(f) != "README.md"]
            n = len(files)
        counts[section] = n
    return counts


def decision_statuses(root):
    """{D-id: status} из front-matter decisions/D-*.md (id из файла, фоллбэк — имя файла)."""
    result = {}
    for f in sorted(glob.glob(os.path.join(root, "decisions", "D-*.md"))):
        fm = parse_front_matter(_read(f)[:4096])
        did = (fm.get("id") or os.path.splitext(os.path.basename(f))[0]).strip()
        result[did] = (fm.get("status") or "").strip().lower()
    return result


def task_statuses(root):
    """{T-id: status} из front-matter tasks/T-*.md."""
    result = {}
    for f in sorted(glob.glob(os.path.join(root, "tasks", "T-*.md"))):
        fm = parse_front_matter(_read(f)[:4096])
        tid = (fm.get("id") or os.path.splitext(os.path.basename(f))[0]).strip()
        result[tid] = (fm.get("status") or "").strip().lower()
    return result


def _focus_scope(lines):
    """Строки блока «Текущий фокус» (от заголовка до следующего заголовка `## `).

    Проверку (c) — задача-как-живой-фокус — ограничиваем секцией фокуса, чтобы не флажить
    задачи из исторической таблицы «Что изменилось недавно» (там done — норма).
    `lines` — вывод manual_lines (номер, текст). Если заголовок фокуса не найден, scope пуст.
    """
    scope = []
    in_focus = False
    for lineno, text in lines:
        stripped = text.strip()
        if stripped.startswith("## "):
            in_focus = "фокус" in stripped.lower()
            continue
        if in_focus:
            scope.append((lineno, text))
    return scope


def _is_historical(text):
    """Строка говорит о прошлом (delta/находка/дата) — числа в ней историческое повествование."""
    low = text.lower()
    if _DATE_RE.search(text):
        return True
    return any(m in low for m in _DELTA_MARKERS)


def check_numeric(lines, counts):
    """(a) числовые утверждения «N <существительное>» о ТЕКУЩЕМ размере канона vs факт.

    Сверяем только в блоке «Текущий фокус» (живые утверждения; исторический changelog «Что
    изменилось недавно» — про прошлое, там числа фиксируют снимок момента и не должны краснеть).
    Дополнительно пропускаем строки-повествования о дельте/находке/дате (_is_historical): проза,
    объясняющая САМ дрейф C17 («ручные числа отстали на 59 задач…»), — не живое утверждение счётчика.
    Спец-случай: «N вопросов котла» — это вопросы котла (Q-W2-*), а не вопросы канона questions/*;
    для существительного questions такие строки пропускаем.
    """
    findings = []
    scope = _focus_scope(lines)
    for noun, section, _srcdir, _prefix in _NOUNS:
        actual = counts.get(section)
        if actual is None:
            continue
        rx = re.compile(r"(\d+)\s+%s\w*" % noun)
        for lineno, text in scope:
            if _is_historical(text):
                continue
            if section == "questions" and "котл" in text.lower():
                continue  # «N вопросов котла» — не вопросы канона
            for m in rx.finditer(text):
                claimed = int(m.group(1))
                if claimed != actual:
                    findings.append({
                        "kind": "numeric",
                        "line": lineno,
                        "noun": section,
                        "claimed": claimed,
                        "actual": actual,
                        "msg": "STATUS.md:%d ручное «%d %s», фактически %d (%s)" % (
                            lineno, claimed, noun, actual, section),
                    })
    return findings


def check_decision_status(lines, statuses):
    """(b) утверждения «N нератифицированных: D-XXX, ...» vs фактический статус решений.

    В каждой ручной строке с паттерном «N нератифицированных/proposed» собираем перечисленные D-id
    и сверяем: (1) реально нератифицированные среди них (статус != accepted); (2) заявленное число N.
    Находка, если хоть один перечисленный D-id уже accepted ЛИБО N не совпадает с числом реально
    нератифицированных из списка.
    """
    findings = []
    for lineno, text in lines:
        m = _UNRATIFIED_RE.search(text)
        if not m:
            continue
        # Ложное срабатывание: строка ОПИСЫВАЕТ принятие решений («приняты N (D-…→accepted)»),
        # а не заявляет их нератифицированными. Слово «proposed» тут — прилагательное к «решений».
        # Guard из ОДНОЗНАЧНЫХ позитивных фраз: не «ратифицир» (оно есть в «не-ратифицир-ованных»!)
        # и не «принят» (есть в «непринятых»), а «приняты/принято/→ accepted/уже accepted».
        if re.search(r"приняты|принято|→\s*accepted|уже\s+accepted", text, re.IGNORECASE):
            continue
        claimed_n = int(m.group(1))
        ids = _DEC_RE.findall(text)
        if not ids:
            # число без явного списка id — сверяем с общим количеством нератифицированных в каноне
            real_total = sum(1 for s in statuses.values() if s and s != _RATIFIED_STATUS)
            if claimed_n != real_total:
                findings.append({
                    "kind": "decision-count",
                    "line": lineno,
                    "claimed": claimed_n,
                    "actual": real_total,
                    "msg": "STATUS.md:%d ручное «%d нератифицированных», фактически %d в каноне" % (
                        lineno, claimed_n, real_total),
                })
            continue
        # список id есть — проверяем каждое и число
        ratified_listed = [d for d in ids if statuses.get(d) == _RATIFIED_STATUS]
        really_unratified = [d for d in ids if statuses.get(d, "") != _RATIFIED_STATUS]
        if ratified_listed:
            findings.append({
                "kind": "decision-status",
                "line": lineno,
                "wrong": ratified_listed,
                "msg": "STATUS.md:%d перечислены как нератифицированные, но уже accepted: %s" % (
                    lineno, ", ".join(ratified_listed)),
            })
        if claimed_n != len(really_unratified):
            findings.append({
                "kind": "decision-count",
                "line": lineno,
                "claimed": claimed_n,
                "actual": len(really_unratified),
                "msg": "STATUS.md:%d заявлено «%d нератифицированных», реально нератифицированных "
                       "в списке %d" % (lineno, claimed_n, len(really_unratified)),
            })
    return findings


def check_focus_tasks(lines, statuses):
    """(c) задачи, поданные как ЖИВОЙ «текущий фокус», но уже закрытые (status done).

    Сканируем только блок «Текущий фокус». Каждая T-id в нём, чей статус done, — дрейф:
    фокус описывает завершённую работу. Пропускаем пустой scope.
    """
    findings = []
    scope = _focus_scope(lines)
    seen = set()
    for lineno, text in scope:
        for tid in _TASK_RE.findall(text):
            if tid in seen:
                continue
            seen.add(tid)
            # Явная пометка «(done)»/«(закрыт)»/«(готов)» рядом с id — осознанная ссылка
            # на завершённую работу как контекст, а не претензия «живой фокус». Не дрейф.
            if re.search(re.escape(tid) + r"\s*\((?:done|закрыт\w*|готов\w*|выполнен\w*)\)",
                         text, re.IGNORECASE):
                continue
            if statuses.get(tid) == "done":
                findings.append({
                    "kind": "focus-task-done",
                    "line": lineno,
                    "task": tid,
                    "msg": "STATUS.md:%d «текущий фокус» ссылается на %s, но задача done (закрыта)" % (
                        lineno, tid),
                })
    return findings


def run(root=ROOT):
    """Собрать все находки дрейфа STATUS.md. Возвращает список dict (пустой = дрейфа нет)."""
    text = _read(os.path.join(root, "STATUS.md"))
    lines = manual_lines(text)
    counts = canon_counts(root)
    dstat = decision_statuses(root)
    tstat = task_statuses(root)
    findings = []
    findings.extend(check_numeric(lines, counts))
    findings.extend(check_decision_status(lines, dstat))
    findings.extend(check_focus_tasks(lines, tstat))
    return findings


def main(argv=None):
    help_guard(__doc__, argv)
    argv = sys.argv[1:] if argv is None else list(argv)
    as_json = "--json" in argv
    # единственная команда — check (дефолт); прочие позиционные слова игнорируем мягко
    findings = run(ROOT)
    if as_json:
        print(json.dumps({"schema": "status_drift.v1", "count": len(findings),
                          "findings": findings}, ensure_ascii=False, indent=2))
        return 1 if findings else 0
    if not findings:
        print("OK: рассинхрона STATUS.md с каноном не обнаружено")
        return 0
    print("ДРЕЙФ STATUS.md ↔ канон (%d):" % len(findings))
    for f in findings:
        print("  - " + f["msg"])
    print("\n(advisory, dry-run: STATUS.md не правится — это генерируемо-ручной гибрид; "
          "проза чинится человеком)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
