# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_reconcile
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Тест reconcile.py — детектор коллизий (B дубль / E переполнение / C дивергенция) + план исхода на fixture-репо.
# ==========================================
"""Тест reconcile.py — детектор КОЛЛИЗИЙ по принципу reconcile.

Гермётичен: строит ИЗОЛИРОВАННЫЙ temp-репозиторий (уникальный tempfile.mkdtemp — урок B-03:
без общих путей tmp-work/, чтобы не было флейка в батче параллельных агентов).

Тестирует функции IN-PROCESS (импорт модуля, перенаправление ROOT на temp-репо), а не через
subprocess по абсолютному пути — иначе мутация модуля не доходит до теста (co-defective, C-III).
Утверждения на ТОЧНЫЕ множества/значения, чтобы структурные мутации детектора краснели.

Обе ступени: standalone `__main__` (запуск напрямую) + pytest-collectable (функции test_*).
"""
# --- бутстрап путей (C14): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import os
import sys
import tempfile
import shutil

from _ioutil import configure_output  # UTF-8 stdout на Windows (F-006 mojibake)
configure_output()
import reconcile


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# --- Фикстуры содержимого -------------------------------------------------------------------

def _dup_body_a():
    # Осмысленный многострочный документ; строки достаточно длинные (>= MIN_MEANINGFUL_LEN).
    return (
        "# Открытые решения для человека\n\n"
        "Ниже перечислены гейты стратегии, которые ждут решения Stefan.\n"
        "Гейт первый: выбрать стратегию переполнения канона — снапшот или папочный режим.\n"
        "Гейт второй: подтвердить флип primary между конкурирующими документами.\n"
        "Гейт третий: ратифицировать принцип неразрушающей сверки коллизий.\n"
        "Каждый гейт требует явного подтверждения ответственного человека.\n"
    )


def _dup_body_b():
    # Почти то же самое (класс B): те же строки-гейты, отличается лишь заголовок/подводка.
    return (
        "# Стратегические гейты — материал котла\n\n"
        "Ниже перечислены гейты стратегии, которые ждут решения Stefan.\n"
        "Гейт первый: выбрать стратегию переполнения канона — снапшот или папочный режим.\n"
        "Гейт второй: подтвердить флип primary между конкурирующими документами.\n"
        "Гейт третий: ратифицировать принцип неразрушающей сверки коллизий.\n"
        "Каждый гейт требует явного подтверждения ответственного человека.\n"
    )


def _big_body():
    line = "Это содержательная строка канонического документа для проверки порога переполнения.\n"
    # гарантированно больше OVERFLOW_BYTES
    n = (reconcile.OVERFLOW_BYTES // len(line.encode("utf-8"))) + 200
    return "# Большой документ\n\n" + line * n


def _build(root):
    # B: два near-duplicate .md на РАЗНЫХ путях (docs vs kotel) — детектор должен спарить.
    _w(os.path.join(root, "docs", "human-decisions-open.md"), _dup_body_a())
    _w(os.path.join(root, "kotel", "human-strategy-gates.md"), _dup_body_b())

    # E: большой канон-файл (> порога) — переполнение.
    _w(os.path.join(root, "dialog.md"), _big_body())

    # E-исключение: большой, но ГЕНЕРИРУЕМЫЙ (имя в GENERATED_BASENAMES) — НЕ считаем переполнением.
    _w(os.path.join(root, "docs", "dcard_index.md"),
       "# D-Card Index\n\n> Автосгенерированный реестр.\n\n" + _big_body())
    # E-исключение по МАРКЕРУ в шапке (имя не из списка, но помечен как сгенерированный).
    _w(os.path.join(root, "docs", "auto-report.md"),
       "# Отчёт\n\nЭтот файл auto-generated — do not edit.\n\n" + _big_body())

    # C: кластер файлов вокруг темы 'orchestrat' (>=2) — кандидаты вариантов.
    _w(os.path.join(root, "docs", "orchestrator-cycle.md"), "# Оркестраторный цикл\nтело\n")
    _w(os.path.join(root, "docs", "orchestration-architecture.md"), "# Архитектура оркестрации\nтело\n")
    # одиночная тема 'cauldron' (ровно 1 файл) — кластером НЕ считается.
    _w(os.path.join(root, "docs", "cauldron-board.md"), "# Доска котла\nтело\n")

    # Уникальные, ни на что не похожие файлы — не должны попасть ни в один класс.
    _w(os.path.join(root, "docs", "unique-alpha.md"), "# Альфа\nсовершенно уникальное содержание один\n")
    _w(os.path.join(root, "reports", "unique-beta.md"), "# Бета\nсовершенно другое содержание два три\n")


def _redirect_root(root):
    """Перенаправить ROOT детектора на temp-репо и вернуть сохранённое значение."""
    saved = reconcile.ROOT
    reconcile.ROOT = root
    return saved


# --- Тело проверок (используется и pytest-функциями, и standalone run) -----------------------

def _check_fixture(root):
    _redirect_root(root)

    res = reconcile.detect()

    # B: РОВНО одна пара дублей — human-decisions-open ↔ human-strategy-gates.
    dups = res["B_duplicate"]
    assert len(dups) == 1, "ожидалась РОВНО 1 пара дублей: %s" % [
        (d["primary_candidate"], d["other"]) for d in dups]
    pair = {dups[0]["primary_candidate"], dups[0]["other"]}
    assert pair == {"docs/human-decisions-open.md", "kotel/human-strategy-gates.md"}, \
        "пара дублей не та: %s" % pair
    assert dups[0]["jaccard"] >= reconcile.DUP_JACCARD or dups[0]["containment"] >= reconcile.DUP_CONTAINMENT, \
        "метрика дубля ниже порога: %s" % dups[0]

    # E: РОВНО один переполненный (dialog.md); генерируемые большие — исключены.
    overflow = {d["path"] for d in res["E_overflow"]}
    assert overflow == {"dialog.md"}, \
        "переполнение должно быть РОВНО {dialog.md} (генерируемые исключены): %s" % overflow

    # C: РОВНО один кластер дивергенции — тема 'orchestrat' с 2 файлами; одиночный 'cauldron' не кластер.
    div = res["C_divergence"]
    assert len(div) == 1 and div[0]["theme"] == "orchestrat" and div[0]["count"] == 2, \
        "дивергенция должна быть РОВНО {orchestrat:2}: %s" % [(d["theme"], d["count"]) for d in div]

    # detect: суммарно 3 коллизии → exit 1.
    assert reconcile.main(["detect"]) == 1, "detect с находками должен дать exit 1"

    # plan: dry-run покрывает все три класса, помечает человека, ничего не пишет.
    items = reconcile.plan()
    classes = sorted({it["class"] for it in items})
    assert classes == ["B", "C", "E"], "plan должен покрыть классы B/C/E: %s" % classes
    assert all(it.get("needs_human") for it in items), "у каждого плана должна быть пометка ЧЕЛОВЕК"
    # снапшот переполнения — content-address имя `_full-<sha8>` (§6)
    e_item = [it for it in items if it["class"] == "E"][0]
    assert "_full-" in e_item["mechanism"], "план E должен предлагать снапшот _full-<sha8>: %s" % e_item
    assert reconcile.main(["plan"]) == 1, "plan с находками должен дать exit 1"

    # Инвариант «ничего не пишет»: список файлов до и после detect+plan идентичен (нет создания снапшотов).
    before = _snapshot_tree(root)
    reconcile.detect(); reconcile.plan()
    after = _snapshot_tree(root)
    assert before == after, "reconcile НЕ должен создавать/менять файлы (dry-run инвариант)"


def _check_clean(root):
    """Чистая папка (уникальные, небольшие, без тем-кластеров) → 0 коллизий, exit 0."""
    _redirect_root(root)
    _w(os.path.join(root, "docs", "one.md"), "# Один\nуникальное содержание номер один здесь\n")
    _w(os.path.join(root, "docs", "two.md"), "# Два\nсовсем иное содержание номер два тут\n")
    res = reconcile.detect()
    assert reconcile._detect_total(res) == 0, "на чистой папке коллизий быть не должно: %s" % {
        k: len(v) for k, v in res.items()}
    assert reconcile.main(["detect"]) == 0, "чистый detect → exit 0"
    assert reconcile.main(["plan"]) == 0, "чистый plan → exit 0"


def _snapshot_tree(root):
    out = set()
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            out.add(os.path.relpath(os.path.join(dp, f), root).replace("\\", "/"))
    return out


# --- pytest-collectable точки входа ---------------------------------------------------------

def test_fixture_collisions():
    saved = reconcile.ROOT
    root = tempfile.mkdtemp(prefix="reconcile_fix_")
    try:
        _build(root)
        _check_fixture(root)
    finally:
        reconcile.ROOT = saved
        shutil.rmtree(root, ignore_errors=True)


def test_clean_folder():
    saved = reconcile.ROOT
    root = tempfile.mkdtemp(prefix="reconcile_clean_")
    try:
        _check_clean(root)
    finally:
        reconcile.ROOT = saved
        shutil.rmtree(root, ignore_errors=True)


# --- standalone run -------------------------------------------------------------------------

def run():
    saved = reconcile.ROOT
    try:
        test_fixture_collisions()
        test_clean_folder()
        print("TESTS OK reconcile: B(near-dup пара) · E(переполнение, генерируемые исключены) · "
              "C(кластер темы, одиночка не кластер) · plan(B/C/E + пометка человек + снапшот _full) · "
              "clean→0 · dry-run не пишет · exit 1/0")
        return 0
    finally:
        reconcile.ROOT = saved


if __name__ == "__main__":
    try:
        sys.exit(run())
    except AssertionError as exc:
        print("TEST FAIL:", exc)
        sys.exit(1)
