#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.package_gate
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Гейт согласования пакетов kotel/packages/PKG-*.md по риску (proposed, не enforced).
# ==========================================
"""
"""
package_gate.py — гейт согласования пакетов котла (M1, Codex §4.2/§4.3; proposed-инструмент).

Пакет `kotel/packages/PKG-*.md` — операционная оболочка над каноническими T/Q/D:
несколько агентов договариваются о риске, зонах и задачах ДО реального запуска роя.
Этот гейт читает front-matter пакета и печатает вердикт согласования, переиспользуя
семантику риск-тиров из `risk_gate.py`:

    low    → AUTO   — можно без явного ok при зелёном каноне;
    medium → REVIEW — нужен ok (agreed_by) ИЛИ истёкшее окно ревью без veto;
    high   → HUMAN  — утверждает только человек (D-006).

Дополнительные проверки поверх тира:
  - medium/high пакет ОБЯЗАН ссылаться на канон (T-/Q-/D- в `tasks`/`related`),
    иначе WARN «нет канонической связи»;
  - medium без `agreed_by` и с `review_deadline` в прошлом → это СИГНАЛ, что
    `review_state` пора перевести в `expired` (окно ревью истекло без возражений).
    Файл НЕ меняется — печатается только сигнал `review_state: open→expired`;
  - `veto_by` непустой → BLOCKED (любой риск): пока вето стоит, пакет не идёт.

Это политика-советчик (proposed): нигде не enforced, pre-commit не трогает,
статусы канона не меняет, файлы пакетов не редактирует (только чтение).

CLI:
    python tools/package_gate.py check <PKG-file>        # один пакет
    python tools/package_gate.py check --all             # все kotel/packages/PKG-*.md
    python tools/package_gate.py check <...> --json       # машиночитаемый отчёт
    python tools/package_gate.py policy                   # показать политику тиров

Exit-коды (стабильные):
    0 — все проверенные пакеты «чистые» (нет BLOCKED и нет ожидающего HUMAN-gate);
    1 — хотя бы один пакет BLOCKED (veto) или ждёт HUMAN/REVIEW-решения;
    2 — ошибка вызова (нет команды/файла/каталога, мусорный аргумент).
"""
import glob
import json
import os
import sys

from _ioutil import configure_output
from _cli import help_guard
from _canon import parse_fm  # единый парсер front-matter (T-085)

configure_output()

ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SCHEMA = "package-gate.v1"

# Каталог пакетов котла (относительно ROOT).
PACKAGES_DIR = os.path.join("kotel", "packages")

# Тиры риска — та же семантика, что в risk_gate.py (переиспользование, не форк).
# Пустой risk трактуем как medium-подобный REVIEW по умолчанию (как risk_gate: пусто→REVIEW).
TIER = {
    "low": "AUTO",
    "medium": "REVIEW",
    "high": "HUMAN",
    "": "REVIEW",
}

TIER_TEXT = {
    "AUTO": "AUTO — низкий риск: можно без явного ok при зелёном каноне.",
    "REVIEW": "REVIEW — средний риск: нужен ok (agreed_by) или истёкшее окно ревью без veto.",
    "HUMAN": "HUMAN — высокий риск: утверждает только человек (D-006).",
}


def today():
    """Сегодняшняя дата ISO (YYYY-MM-DD). Вынесено функцией — тест инъектит `now`."""
    import datetime
    return datetime.date.today().isoformat()


def _split_list(raw):
    """Front-matter список в inline-форме `[a, b]` или `a, b` → список строк.

    parse_fm возвращает значения как строки; списки в пакетах пишутся inline
    (`tasks: [T-273]`, `agreed_by: []`) либо через запятую. YAML-блочные списки
    (перенос + `- item`) parse_fm не собирает — для гейта это не нужно: критичные
    поля (tasks/agreed_by/veto_by) в PKG хранятся inline. Пустой `[]`/'' → [].
    """
    if raw is None:
        return []
    s = str(raw).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    items = [x.strip().strip("'\"") for x in s.split(",")]
    return [x for x in items if x]


def _has_canon_link(fm):
    """Есть ли ссылка на канон (T-/Q-/D-) в `tasks` или `related`.

    Для medium/high это обязательное свойство: пакет-оболочка должен цепляться
    к канонической задаче/вопросу/решению, иначе теряется провенанс.
    """
    prefixes = ("T-", "Q-", "D-")
    for field in ("tasks", "related"):
        for item in _split_list(fm.get(field)):
            if item.upper().startswith(prefixes):
                return True
    return False


def _date_in_past(value, now):
    """`value` (YYYY-MM-DD) строго раньше `now`? Пустое/мусорное → False (не сигналим)."""
    v = (value or "").strip()
    if not v:
        return False
    # Лексикографическое сравнение ISO-дат корректно; но подстрахуемся форматом.
    return v < now


def evaluate(fm, now=None):
    """Вердикт согласования для одного пакета по его front-matter.

    Возвращает dict: id, risk, tier, verdict, review_state, review_state_signal,
    blocked, needs_human, needs_review, warnings[], reasons[].
    Файл не меняется — все переводы состояний только как СИГНАЛ.
    """
    now = now or today()
    pkg_id = (fm.get("id") or "").strip()
    risk = (fm.get("risk") or "").strip().lower()
    tier = TIER.get(risk, TIER[""])

    agreed_by = _split_list(fm.get("agreed_by"))
    veto_by = _split_list(fm.get("veto_by"))
    review_state = (fm.get("review_state") or "").strip()
    review_deadline = (fm.get("review_deadline") or "").strip()

    warnings = []
    reasons = []

    # 1) veto перекрывает всё: пока стоит вето — пакет BLOCKED (любой риск).
    blocked = bool(veto_by)
    if blocked:
        reasons.append("veto_by непустой: %s → BLOCKED" % ", ".join(veto_by))

    # 2) medium/high обязаны иметь каноническую связь (T/Q/D).
    if tier in ("REVIEW", "HUMAN") and not _has_canon_link(fm):
        warnings.append("нет канонической связи (T-/Q-/D-) в tasks/related при risk=%s" % (risk or "—"))

    # 3) medium без agreed_by и с истёкшим окном ревью → сигнал open→expired.
    #    Только СИГНАЛ: файл не трогаем, review_state в файле не меняем.
    review_state_signal = None
    window_expired = _date_in_past(review_deadline, now)
    if (
        tier == "REVIEW"
        and not agreed_by
        and window_expired
        and review_state == "open"
    ):
        review_state_signal = "open→expired"
        reasons.append(
            "review_deadline %s < %s и нет agreed_by → сигнал review_state: open→expired"
            % (review_deadline, now)
        )

    # 4) Итоговые флаги ожидания решения.
    #    HUMAN всегда ждёт человека (кроме случая, когда уже BLOCKED — тогда причина вето).
    needs_human = tier == "HUMAN"
    #    REVIEW ждёт решения, если нет agreed_by И окно ещё не истекло (иначе можно считать
    #    согласованным по правилу «ok или истёкшее окно без veto»).
    needs_review = False
    if tier == "REVIEW":
        if agreed_by:
            reasons.append("есть agreed_by: %s → согласовано" % ", ".join(agreed_by))
        elif window_expired:
            reasons.append("окно ревью истекло без veto → можно считать согласованным")
        else:
            needs_review = True
            reasons.append("нет agreed_by и окно ревью не истекло → ждёт REVIEW")
    if tier == "AUTO":
        reasons.append("низкий риск → AUTO без явного ok")

    return {
        "id": pkg_id,
        "risk": risk,
        "tier": tier,
        "verdict": _verdict_label(tier, blocked, needs_human, needs_review),
        "review_state": review_state,
        "review_state_signal": review_state_signal,
        "review_deadline": review_deadline,
        "agreed_by": agreed_by,
        "veto_by": veto_by,
        "blocked": blocked,
        "needs_human": needs_human and not blocked,
        "needs_review": needs_review,
        "window_expired": window_expired,
        "has_canon_link": _has_canon_link(fm),
        "warnings": warnings,
        "reasons": reasons,
    }


def _verdict_label(tier, blocked, needs_human, needs_review):
    """Короткий итоговый ярлык вердикта (для человека и для grep)."""
    if blocked:
        return "BLOCKED"
    if needs_human:
        return "HUMAN"
    if needs_review:
        return "REVIEW"
    return tier  # AUTO, либо REVIEW/HUMAN, уже разрешённый выше


def _pkg_exit_bad(result):
    """Пакет «нечистый» для exit-кода: BLOCKED или ждёт HUMAN/REVIEW-решения."""
    return result["blocked"] or result["needs_human"] or result["needs_review"]


def read_package(path):
    """Прочитать front-matter пакета (только чтение). Возвращает fm или None при ошибке."""
    try:
        with open(path, encoding="utf-8") as f:
            return parse_fm(f.read())
    except OSError:
        return None


def list_packages():
    """Все kotel/packages/PKG-*.md под ROOT (отсортировано). Пустой список, если каталога нет."""
    pdir = os.path.join(ROOT, PACKAGES_DIR)
    if not os.path.isdir(pdir):
        return []
    return sorted(glob.glob(os.path.join(pdir, "PKG-*.md")))


def check(paths, now=None, as_json=False):
    """Проверить список путей пакетов. Возвращает (rc, report_dict)."""
    now = now or today()
    items = []
    bad = 0
    for path in paths:
        fm = read_package(path)
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if fm is None:
            items.append({
                "file": rel,
                "error": "cannot-read",
                "verdict": "ERROR",
            })
            bad += 1
            continue
        res = evaluate(fm, now=now)
        res["file"] = rel
        items.append(res)
        if _pkg_exit_bad(res):
            bad += 1
    report = {
        "schema": SCHEMA,
        "now": now,
        "count": len(items),
        "bad": bad,
        "packages": items,
    }
    rc = 1 if bad else 0
    return rc, report


def _print_human(report):
    """Человекочитаемый вывод отчёта проверки."""
    for it in report["packages"]:
        if it.get("error"):
            print("[ERROR] %s — %s" % (it["file"], it["error"]))
            continue
        print("[%-7s] %s [risk=%s, tier=%s]" % (
            it["verdict"], it["id"] or it["file"], it["risk"] or "—", it["tier"]))
        if it.get("review_state_signal"):
            print("    сигнал review_state: %s" % it["review_state_signal"])
        for w in it["warnings"]:
            print("    WARN: %s" % w)
        for r in it["reasons"]:
            print("    - %s" % r)
    print("ИТОГ package_gate: пакетов=%d нечистых=%d (now=%s)" % (
        report["count"], report["bad"], report["now"]))


def _print_policy():
    for tier in ("AUTO", "REVIEW", "HUMAN"):
        print("  %-6s → %s" % (tier, TIER_TEXT[tier]))
    print("  veto_by непустой → BLOCKED (любой риск)")
    print("  medium/high без T-/Q-/D- в tasks/related → WARN «нет канонической связи»")


def main(argv=None):
    help_guard(__doc__)
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv:
        print("usage: package_gate.py check <PKG-file|--all> [--json] | policy")
        return 2

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "policy":
        _print_policy()
        return 0

    if cmd != "check":
        print("usage: package_gate.py check <PKG-file|--all> [--json] | policy")
        return 2

    as_json = "--json" in rest
    rest = [a for a in rest if a != "--json"]

    # Инъекция now для детерминизма/тестов (не документируется как публичный флаг).
    now = None
    filtered = []
    i = 0
    while i < len(rest):
        if rest[i] == "--now" and i + 1 < len(rest):
            now = rest[i + 1]
            i += 2
            continue
        filtered.append(rest[i])
        i += 1
    rest = filtered

    if "--all" in rest:
        paths = list_packages()
        if not paths:
            print(json.dumps({"schema": SCHEMA, "count": 0, "packages": []},
                             ensure_ascii=False, indent=2) if as_json
                  else "package_gate: нет kotel/packages/PKG-*.md")
            return 0
    else:
        targets = [a for a in rest if not a.startswith("-")]
        if not targets:
            print("usage: package_gate.py check <PKG-file|--all> [--json] | policy")
            return 2
        paths = []
        for t in targets:
            path = t if os.path.isabs(t) else os.path.join(ROOT, t)
            if not os.path.isfile(path):
                # Второй шанс: относительно каталога пакетов по имени.
                alt = os.path.join(ROOT, PACKAGES_DIR, os.path.basename(t))
                if os.path.isfile(alt):
                    path = alt
                else:
                    print(json.dumps({"error": "not-a-file", "path": t},
                                     ensure_ascii=False, indent=2) if as_json
                          else "ERROR: нет файла пакета: %s" % t)
                    return 2
            paths.append(path)

    rc, report = check(paths, now=now, as_json=as_json)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return rc


if __name__ == "__main__":
    sys.exit(main())
