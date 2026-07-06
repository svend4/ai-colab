#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_zone_overlap
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Тест zone_overlap.py — advisory-детектор пересечения зон активных пакетов (WARN/FAIL/ADVICE).
# ==========================================
# --- бутстрап путей (C14, аудит 2026-07-02): тест живёт в tools/tests/, инструменты — в tools/.
# Вставка ДО локальных импортов, чтобы standalone-запуск работал из нового места.
import os as _os
import sys as _sys
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)
# --- конец бутстрапа ---

import io
import json
import os
import sys
import importlib
from contextlib import redirect_stdout

HERE = _TOOLS_DIR  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "drivers"))

from test_tmp import temp_dir  # noqa: E402

# Реальный пакет-пример (только чтение) — как fixture его менять нельзя.
REAL_PKG = os.path.join(ROOT, "kotel", "packages", "PKG-20260706-pilot-t273.md")


def _write_pkg(root, name, status="in-swarm", input_zones=None, output_zones=None):
    """Записать фикстурный PKG во временный kotel/packages/ с БЛОЧНЫМИ списками зон.

    Пишем именно блочный YAML (перенос + `  - item`), как в реальных пакетах —
    так проверяем, что построчный парсер zone_overlap собирает эти списки
    (parse_fm их не собирает; ради этого и свой парсер).
    """
    pdir = os.path.join(root, "kotel", "packages")
    os.makedirs(pdir, exist_ok=True)
    lines = ["---", "id: %s" % name, "type: package", "status: %s" % status]
    if input_zones:
        lines.append("input_zones:")
        lines += ["  - %s" % z for z in input_zones]
    if output_zones:
        lines.append("output_zones:")
        lines += ["  - %s" % z for z in output_zones]
    lines += ["---", "", "# %s" % name, "тело пакета", ""]
    path = os.path.join(pdir, name + ".md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return path


def _fresh_zo(root):
    """Импортировать zone_overlap с ROOT=<временный>, перечитав модуль (COLLAB_ROOT).

    permissions читается по РЕАЛЬНОМУ tools/permissions.json (deny-пути), а пакеты —
    из временного каталога: так тест не зависит от временной копии permissions.json.
    """
    os.environ["COLLAB_ROOT"] = root
    import zone_overlap as zo
    importlib.reload(zo)
    assert zo.ROOT == root, (zo.ROOT, root)
    return zo


def _call(zo, *argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = zo.main(list(argv))
    return rc, buf.getvalue()


def test_zone_language_overlap():
    """Язык зон permissions.match: glob покрывает путь, dir-префикс ~ dir/**, разные пути не пересекаются."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        assert zo.zones_overlap("docs/**", "docs/a.md"), "glob должен покрывать путь"
        assert zo.zones_overlap("docs/", "docs/a.md"), "dir-префикс ~ dir/**"
        assert zo.zones_overlap("**", "tools/x.py"), "** покрывает всё"
        assert zo.zones_overlap("*.md", "docs/a.md"), "*.md покрывает любой .md"
        assert not zo.zones_overlap("docs/a.md", "docs/b.md"), "разные файлы не пересекаются"
        assert not zo.zones_overlap("tools/", "docs/"), "разные каталоги не пересекаются"
        print("PASS: язык зон (glob/dir/точный путь)")


def test_two_pkg_overlap_warn():
    """Два активных пакета с ПЕРЕСЕКАЮЩИМИСЯ output-зонами → WARN; непересекающиеся → чисто."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        # A и B оба пишут в reports/ → пересечение (WARN)
        _write_pkg(tmp, "PKG-A", status="in-swarm", output_zones=["reports/", "tmp-a/"])
        _write_pkg(tmp, "PKG-B", status="agreed", output_zones=["reports/x.md", "tmp-b/"])
        # C пишет в изолированную зону → с A/B не пересекается
        _write_pkg(tmp, "PKG-C", status="in-swarm", output_zones=["isolated-c/"])

        rc, report = zo.check(as_json=True)
        assert report["active_count"] == 3, report
        # ровно одна пара пересеклась: A↔B по reports/
        ab = [o for o in report["overlaps"] if {o["a"], o["b"]} == {"PKG-A", "PKG-B"}]
        assert ab, "A↔B должны пересечься по reports/: %r" % report["overlaps"]
        # C ни с кем не пересекается
        assert not any("PKG-C" in (o["a"], o["b"]) for o in report["overlaps"]), report["overlaps"]
        assert report["warn"] == 1, report
        assert rc == 1, "WARN должен дать advisory rc=1"
        print("PASS: пересечение output-зон → WARN, изолированная зона чиста")


def test_no_overlap_clean():
    """Активные пакеты с непересекающимися зонами → чисто (rc 0, warn 0)."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        _write_pkg(tmp, "PKG-X", status="in-swarm", output_zones=["zone-x/"])
        _write_pkg(tmp, "PKG-Y", status="agreed", output_zones=["zone-y/"])
        rc, report = zo.check(as_json=True)
        assert report["warn"] == 0 and report["fail"] == 0, report
        assert not report["overlaps"], report
        assert rc == 0, "непересекающиеся зоны → rc 0"
        print("PASS: непересекающиеся зоны — чисто")


def test_status_filter_only_active():
    """Фильтр статуса: только in-swarm/agreed активны; draft игнорируется (нет ложного WARN)."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        # оба пишут в reports/, но один draft → активен только один → пересечения нет
        _write_pkg(tmp, "PKG-active", status="in-swarm", output_zones=["reports/"])
        _write_pkg(tmp, "PKG-draft", status="draft", output_zones=["reports/"])
        rc, report = zo.check(as_json=True)
        assert report["active_count"] == 1, "draft не активен: %r" % report["active"]
        assert report["warn"] == 0 and rc == 0, report
        # --all снимает фильтр: оба видны и теперь пересекаются
        rc2, report2 = zo.check(all_statuses=True, as_json=True)
        assert report2["active_count"] == 2, report2
        assert report2["warn"] == 1 and rc2 == 1, report2
        print("PASS: статус-фильтр (draft вне активных; --all снимает фильтр)")


def test_deny_path_fail():
    """Зона, задевающая deny-путь (_deny_agents из РЕАЛЬНОГО permissions.json) → FAIL/HUMAN."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        # tools/** задевает и tools/permissions.json, и tools/githooks/** (deny)
        _write_pkg(tmp, "PKG-deny", status="in-swarm", output_zones=["tools/**"])
        rc, report = zo.check(as_json=True)
        assert report["fail"] >= 1, "tools/** должен задеть deny-пути: %r" % report["deny"]
        denied = report["deny"][0]
        assert denied["pkg"] == "PKG-deny", denied
        assert any(d.startswith("tools/") for d in denied["deny"]), denied
        assert rc == 1, "FAIL → advisory rc=1"
        print("PASS: зона в deny-путях → FAIL/HUMAN")


def test_generated_index_advice():
    """Зона, задевающая генерируемый индекс (ownership.GENERATED) → ADVICE «через worktree» (не блок)."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        # output-зона прямо на TASKS.md — генерат → совет worktree, но НЕ поднимает rc
        _write_pkg(tmp, "PKG-gen", status="in-swarm", output_zones=["TASKS.md", "safe-zone/"])
        rc, report = zo.check(as_json=True)
        assert report["advice"] >= 1, "TASKS.md должен дать advice: %r" % report["generated"]
        g = report["generated"][0]
        assert g["pkg"] == "PKG-gen" and g["zone"] == "TASKS.md", g
        # ADVICE в одиночку rc НЕ поднимает (нет WARN/FAIL)
        assert report["warn"] == 0 and report["fail"] == 0, report
        assert rc == 0, "advice сам по себе не блок — rc 0"
        print("PASS: генерируемый индекс → ADVICE (rc не поднят)")


def test_block_yaml_parsing():
    """Парсер собирает БЛОЧНЫЕ YAML-списки зон (то, что parse_fm не умеет)."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        p = _write_pkg(tmp, "PKG-parse", status="in-swarm",
                       input_zones=["docs/", "tasks/T-1.md"],
                       output_zones=["reports/", "tmp/"])
        data = zo.read_package_zones(p)
        assert data["status"] == "in-swarm", data
        assert data["input"] == ["docs/", "tasks/T-1.md"], data["input"]
        assert data["output"] == ["reports/", "tmp/"], data["output"]
        print("PASS: блочные YAML-списки зон разобраны")


def test_cli_and_exit_codes():
    """CLI: check/--json/--all, policy, usage; стабильные exit-коды 0/1/2."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        _write_pkg(tmp, "PKG-1", status="in-swarm", output_zones=["reports/"])
        _write_pkg(tmp, "PKG-2", status="agreed", output_zones=["reports/y.md"])

        # check --json: валидный JSON со схемой; пересечение → rc 1
        rc, out = _call(zo, "check", "--json")
        assert rc == 1, (rc, out)
        payload = json.loads(out)
        assert payload["schema"] == "zone-overlap.v1", payload
        assert payload["active_count"] == 2 and payload["warn"] == 1, payload

        # человекочитаемый check без флагов — печатает разделы
        rc, out = _call(zo, "check")
        assert rc == 1 and "ZONE-OVERLAP" in out and "WARN" in out, out

        # policy → rc 0, печатает классы находок и язык зон
        rc, out = _call(zo, "policy")
        assert rc == 0 and "FAIL" in out and "WARN" in out and "ADVICE" in out, out

        # нет команды → usage rc 2
        rc, out = _call(zo)
        assert rc == 2 and "usage" in out, (rc, out)

        # мусорная команда → usage rc 2
        rc, out = _call(zo, "wat")
        assert rc == 2, (rc, out)
        print("PASS: CLI check/--json/policy/usage + rc 0/1/2")


def test_advisory_not_enforced_readonly():
    """Advisory-инвариант: детектор только читает пакеты, файлы не меняет."""
    with temp_dir("zone_overlap_") as tmp:
        zo = _fresh_zo(tmp)
        p = _write_pkg(tmp, "PKG-ro", status="in-swarm", output_zones=["tools/**", "TASKS.md"])
        with open(p, encoding="utf-8") as f:
            before = f.read()
        # находки есть (deny + generated), но файл не тронут
        zo.check(as_json=True)
        with open(p, encoding="utf-8") as f:
            after = f.read()
        assert before == after, "zone_overlap не должен менять файлы пакетов"
        print("PASS: advisory read-only — файлы пакетов не изменены")


def test_real_pkg_readonly_example():
    """Реальный PKG-20260706-pilot-t273.md (только чтение): draft → вне активных (не WARN)."""
    if not os.path.isfile(REAL_PKG):
        print("SKIP: реального PKG нет — пропуск примера")
        return
    os.environ.pop("COLLAB_ROOT", None)
    import zone_overlap as zo
    importlib.reload(zo)
    data = zo.read_package_zones(REAL_PKG)
    assert data is not None, "не прочитался реальный PKG"
    # реальный статус draft → в check() он отфильтруется (не активен)
    assert data["status"] == "draft", data["status"]
    # но блочные зоны реального файла разобраны (парсер работает на настоящем формате)
    assert "reports/" in data["output"], data["output"]
    assert "docs/" in data["input"], data["input"]
    rc, report = zo.check(as_json=True)
    assert not any(p["id"] == "PKG-20260706-pilot-t273" for p in report["active"]), \
        "draft-пакет не должен попасть в активные"
    print("PASS: реальный PKG читается (draft → вне активных, блочные зоны разобраны)")


def run():
    ok = True
    try:
        test_zone_language_overlap()
        test_two_pkg_overlap_warn()
        test_no_overlap_clean()
        test_status_filter_only_active()
        test_deny_path_fail()
        test_generated_index_advice()
        test_block_yaml_parsing()
        test_cli_and_exit_codes()
        test_advisory_not_enforced_readonly()
        test_real_pkg_readonly_example()
        print("\nTESTS OK zone_overlap: overlap→WARN + deny→FAIL + generated→ADVICE + "
              "статус-фильтр + блочный YAML + CLI rc(0/1/2) + read-only")
    except AssertionError as e:
        ok = False
        print("TEST FAIL:", e)
    except Exception as e:  # noqa: BLE001
        ok = False
        print("TEST ERROR:", repr(e))
    finally:
        os.environ.pop("COLLAB_ROOT", None)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
