#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_package_gate
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Тест package_gate.py — вердикт согласования пакетов по риску (тиры/veto/canon/expired).
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

# Реальный пакет-пример (только чтение) — использовать как fixture нельзя менять.
REAL_PKG = os.path.join(ROOT, "kotel", "packages", "PKG-20260706-pilot-t273.md")

FIXED_NOW = "2026-07-06"  # детерминированное «сегодня» для сигналов окна ревью


def _write_pkg(root, name, **fields):
    """Записать фикстурный PKG-файл во временный kotel/packages/ с inline-front-matter."""
    pdir = os.path.join(root, "kotel", "packages")
    os.makedirs(pdir, exist_ok=True)
    lines = ["---", "id: %s" % name, "type: package"]
    for k, v in fields.items():
        lines.append("%s: %s" % (k, v))
    lines += ["---", "", "# %s" % name, "тело пакета", ""]
    path = os.path.join(pdir, name + ".md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return path


def _fresh_gate(root):
    """Импортировать package_gate с ROOT=<временный>, перечитав модуль (COLLAB_ROOT)."""
    os.environ["COLLAB_ROOT"] = root
    import package_gate as pg
    importlib.reload(pg)
    assert pg.ROOT == root, (pg.ROOT, root)
    return pg


def _call(pg, *argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = pg.main(list(argv))
    return rc, buf.getvalue()


def test_tiers_low_medium_high():
    """low→AUTO, medium→REVIEW, high→HUMAN (переиспользование семантики risk_gate)."""
    with temp_dir("package_gate_") as tmp:
        pg = _fresh_gate(tmp)
        # low: без agreed_by всё равно AUTO
        _write_pkg(tmp, "PKG-low", risk="low", tasks="[T-100]",
                   agreed_by="[]", veto_by="[]", review_state="open",
                   review_deadline="2026-07-09")
        # medium: без agreed_by, окно не истекло → REVIEW (ждёт)
        _write_pkg(tmp, "PKG-med", risk="medium", tasks="[T-101]",
                   agreed_by="[]", veto_by="[]", review_state="open",
                   review_deadline="2026-07-09")
        # high: → HUMAN всегда
        _write_pkg(tmp, "PKG-high", risk="high", tasks="[T-102]",
                   agreed_by="[stefan]", veto_by="[]", review_state="open",
                   review_deadline="2026-07-09")

        low = pg.evaluate(pg.read_package(os.path.join(tmp, "kotel", "packages", "PKG-low.md")), now=FIXED_NOW)
        med = pg.evaluate(pg.read_package(os.path.join(tmp, "kotel", "packages", "PKG-med.md")), now=FIXED_NOW)
        high = pg.evaluate(pg.read_package(os.path.join(tmp, "kotel", "packages", "PKG-high.md")), now=FIXED_NOW)

        assert low["tier"] == "AUTO" and low["verdict"] == "AUTO", low
        assert med["tier"] == "REVIEW" and med["verdict"] == "REVIEW" and med["needs_review"], med
        assert high["tier"] == "HUMAN" and high["verdict"] == "HUMAN" and high["needs_human"], high
        print("PASS: тиры low→AUTO / medium→REVIEW / high→HUMAN")


def test_medium_agreed_by_resolves():
    """medium С agreed_by → согласовано (не ждёт REVIEW)."""
    with temp_dir("package_gate_") as tmp:
        pg = _fresh_gate(tmp)
        p = _write_pkg(tmp, "PKG-agreed", risk="medium", tasks="[T-200]",
                       agreed_by="[codex]", veto_by="[]", review_state="open",
                       review_deadline="2026-07-09")
        res = pg.evaluate(pg.read_package(p), now=FIXED_NOW)
        assert not res["needs_review"], res
        assert res["verdict"] == "REVIEW", res  # тир остаётся REVIEW, но решение есть
        assert res["agreed_by"] == ["codex"], res
        print("PASS: medium + agreed_by → согласовано, не ждёт")


def test_veto_blocks_any_risk():
    """veto_by непустой → BLOCKED независимо от риска."""
    with temp_dir("package_gate_") as tmp:
        pg = _fresh_gate(tmp)
        p = _write_pkg(tmp, "PKG-veto", risk="low", tasks="[T-300]",
                       agreed_by="[]", veto_by="[novax]", review_state="open",
                       review_deadline="2026-07-09")
        res = pg.evaluate(pg.read_package(p), now=FIXED_NOW)
        assert res["blocked"] and res["verdict"] == "BLOCKED", res
        assert res["veto_by"] == ["novax"], res
        print("PASS: veto_by → BLOCKED (даже при low)")


def test_no_canon_link_warns_for_medium_high():
    """medium/high без T-/Q-/D- в tasks/related → WARN «нет канонической связи»."""
    with temp_dir("package_gate_") as tmp:
        pg = _fresh_gate(tmp)
        p = _write_pkg(tmp, "PKG-nolink", risk="high", tasks="[]",
                       related="[some-topic]", agreed_by="[stefan]", veto_by="[]",
                       review_state="open", review_deadline="2026-07-09")
        res = pg.evaluate(pg.read_package(p), now=FIXED_NOW)
        assert not res["has_canon_link"], res
        assert any("канонической связи" in w for w in res["warnings"]), res

        # А low без связи — WARN не даёт (обязательность только для medium/high).
        p2 = _write_pkg(tmp, "PKG-lownolink", risk="low", tasks="[]",
                        related="[some-topic]", agreed_by="[]", veto_by="[]",
                        review_state="open", review_deadline="2026-07-09")
        res2 = pg.evaluate(pg.read_package(p2), now=FIXED_NOW)
        assert not any("канонической связи" in w for w in res2["warnings"]), res2
        print("PASS: WARN нет канонической связи только для medium/high")


def test_expired_window_signal_open_to_expired():
    """medium без agreed_by + review_deadline в прошлом + review_state=open → сигнал open→expired.

    Файл при этом НЕ меняется (гейт — только чтение): проверяем, что на диске
    review_state остался 'open'.
    """
    with temp_dir("package_gate_") as tmp:
        pg = _fresh_gate(tmp)
        p = _write_pkg(tmp, "PKG-expired", risk="medium", tasks="[T-400]",
                       agreed_by="[]", veto_by="[]", review_state="open",
                       review_deadline="2026-07-01")  # < FIXED_NOW
        res = pg.evaluate(pg.read_package(p), now=FIXED_NOW)
        assert res["window_expired"], res
        assert res["review_state_signal"] == "open→expired", res
        # окно истекло без veto → REVIEW больше не «ждёт» (правило ok/истёкшее окно)
        assert not res["needs_review"], res
        # файл не тронут: review_state на диске всё ещё open
        with open(p, encoding="utf-8") as f:
            assert "review_state: open" in f.read(), "файл не должен меняться"
        print("PASS: сигнал open→expired, файл не изменён")


def test_cli_check_and_json_exit_codes():
    """CLI: check одного файла, --json, --all, стабильные exit-коды."""
    with temp_dir("package_gate_") as tmp:
        pg = _fresh_gate(tmp)
        low = _write_pkg(tmp, "PKG-cli-low", risk="low", tasks="[T-500]",
                         agreed_by="[]", veto_by="[]", review_state="open",
                         review_deadline="2026-07-09")
        _write_pkg(tmp, "PKG-cli-veto", risk="medium", tasks="[T-501]",
                   agreed_by="[]", veto_by="[mavis]", review_state="open",
                   review_deadline="2026-07-09")

        # чистый low → rc 0
        rc, out = _call(pg, "check", low, "--now", FIXED_NOW)
        assert rc == 0 and "AUTO" in out, (rc, out)

        # --json одного файла — валидный JSON со схемой
        rc, out = _call(pg, "check", low, "--now", FIXED_NOW, "--json")
        assert rc == 0, (rc, out)
        payload = json.loads(out)
        assert payload["schema"] == "package-gate.v1", payload
        assert payload["count"] == 1 and payload["bad"] == 0, payload

        # --all: среди пакетов есть BLOCKED (veto) → rc 1
        rc, out = _call(pg, "check", "--all", "--now", FIXED_NOW, "--json")
        assert rc == 1, (rc, out)
        rep = json.loads(out)
        verdicts = {p["id"]: p["verdict"] for p in rep["packages"]}
        assert verdicts.get("PKG-cli-veto") == "BLOCKED", verdicts
        assert verdicts.get("PKG-cli-low") == "AUTO", verdicts

        # policy → rc 0, печатает тиры
        rc, out = _call(pg, "policy")
        assert rc == 0 and "AUTO" in out and "REVIEW" in out and "HUMAN" in out, out

        # нет команды → usage rc 2
        rc, out = _call(pg)
        assert rc == 2, (rc, out)

        # несуществующий файл → rc 2
        rc, out = _call(pg, "check", os.path.join(tmp, "kotel", "packages", "PKG-нет.md"))
        assert rc == 2, (rc, out)
        print("PASS: CLI check/--json/--all + exit-коды 0/1/2")


def test_real_pkg_readonly_example():
    """Реальный PKG-20260706-pilot-t273.md (только чтение) как пример: medium с agreed_by=[].

    На дату файла (posted_at 2026-07-06, review_deadline 2026-07-07) окно ещё
    открыто → medium без agreed_by ждёт REVIEW. Никаких правок реального файла.
    """
    if not os.path.isfile(REAL_PKG):
        print("SKIP: реального PKG нет — пропуск примера")
        return
    # Работаем с реальным ROOT (не подменяем COLLAB_ROOT), только чтение.
    os.environ.pop("COLLAB_ROOT", None)
    import package_gate as pg
    importlib.reload(pg)
    fm = pg.read_package(REAL_PKG)
    assert fm is not None, "не прочитался реальный PKG"
    assert fm.get("risk") == "medium", fm.get("risk")
    res = pg.evaluate(fm, now="2026-07-06")
    assert res["tier"] == "REVIEW", res
    assert res["has_canon_link"], res  # tasks: [T-273] + related T-/D-
    # agreed_by пустой, окно (deadline 2026-07-07) ещё открыто на 2026-07-06 → ждёт
    assert res["needs_review"], res
    print("PASS: реальный PKG-20260706-pilot-t273 читается, medium/REVIEW, ждёт согласования")


def run():
    ok = True
    try:
        test_tiers_low_medium_high()
        test_medium_agreed_by_resolves()
        test_veto_blocks_any_risk()
        test_no_canon_link_warns_for_medium_high()
        test_expired_window_signal_open_to_expired()
        test_cli_check_and_json_exit_codes()
        test_real_pkg_readonly_example()
        print("\nTESTS OK package_gate: тиры + veto→BLOCKED + canon-WARN + open→expired сигнал + CLI rc(0/1/2)")
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
