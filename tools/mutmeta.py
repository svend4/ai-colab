"""mutmeta.py — мета-тест ДЕТЕКТОРА: ловит со-дефектные тесты мутацией (контр-инвариант C-III формулы).

topics/defect-class-formula-2026-06-26 §C-III: «флаг/тест без проверки самого детектора — это ВЕРА, а не
видимость». Зелёный тест поверх сломанного кода (как `test_metrics.py` поверх `metrics.py:77 load("темы")`)
даёт ложную гарантию. mutmeta это ловит: вносит в КОПИЮ модуля по одной мутации (==↔!=, True↔False,
return X→None, литерал→0) и прогоняет тест против мутанта. Тест ОБЯЗАН покраснеть хотя бы на одной мутации;
если переживает ВСЕ — он `!co-defective` (ловит не то, что должен), и его зелёный цвет — иллюзия.

Безопасно: настоящие файлы не трогаются — мутируется копия в temp-каталоге, тест бежит оттуда.

CLI:
  python tools/mutmeta.py <module> [<test>]     # напр.: mutmeta.py metrics  (test по умолч. test_<module>)
  python tools/mutmeta.py <module> --json
  python tools/mutmeta.py <module> --cap 8       # ограничить число мутантов
"""
import os
from _ioutil import configure_output
from _cli import help_guard
import sys
import re
import json
import glob
import shutil
import subprocess

configure_output()
TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("COLLAB_ROOT") or os.path.dirname(TOOLS)


def _compiles(src):
    try:
        compile(src, "<mut>", "exec")
        return True
    except SyntaxError:
        return False


def gen_mutants(src, cap=12):
    """По ОДНОЙ мутации на сайт → список (label, mutant_src). Только компилирующиеся, без дублей, до cap."""
    rules = [
        (re.compile(r"=="), "!="),
        (re.compile(r"!="), "=="),
        (re.compile(r"\bTrue\b"), "False"),
        (re.compile(r"\bFalse\b"), "True"),
        (re.compile(r"\breturn (?!None\b)[^\n#]+"), "return None"),
        (re.compile(r"(?<![\w.])[1-9][0-9]*\b"), "0"),
    ]
    out, seen = [], set()
    for rx, repl in rules:
        for m in rx.finditer(src):
            s, e = m.span()
            mutant = src[:s] + repl + src[e:]
            if mutant == src or mutant in seen or not _compiles(mutant):
                continue
            seen.add(mutant)
            out.append(("%r→%r@%d" % (m.group(0)[:12], repl, s), mutant))
            if len(out) >= cap:
                return out
    return out


def verdict(results):
    """results=[(label, caught_bool)] → сводка. co_defective = валидные мутанты есть, но НИ ОДИН не пойман."""
    valid = len(results)
    caught = sum(1 for _l, c in results if c)
    return {"valid_mutants": valid, "caught": caught,
            "mutation_score": round(caught / valid, 2) if valid else None,
            "co_defective": valid > 0 and caught == 0,
            "missed": [l for l, c in results if not c]}


def run_meta(module, test, tools_dir=None, cap=12, timeout=60):
    """Прогнать мета-тест: мутировать копию <module>, бежать <test> против каждого мутанта.

    Возвращает (verdict, results). Настоящие файлы не трогаются."""
    tools_dir = tools_dir or TOOLS
    src_path = os.path.join(tools_dir, module + ".py")
    test_path = os.path.join(tools_dir, test + ".py")
    if not (os.path.exists(src_path) and os.path.exists(test_path)):
        return {"error": "нет модуля или теста: %s / %s" % (module, test)}, []
    src = open(src_path, encoding="utf-8", errors="replace").read()
    mutants = gen_mutants(src, cap)
    if not mutants:
        return {"error": "не удалось сгенерировать мутантов (нечего ломать)"}, []
    tmp_root = os.path.join(ROOT, "tmp-work", "mutmeta")
    os.makedirs(tmp_root, exist_ok=True)
    tmp = os.path.join(tmp_root, "%s_%d" % (module, os.getpid()))
    n = 0
    while os.path.exists(tmp):
        n += 1
        tmp = os.path.join(tmp_root, "%s_%d_%d" % (module, os.getpid(), n))
    os.makedirs(tmp, exist_ok=True)
    try:
        dst = os.path.join(tmp, "tools")
        shutil.copytree(tools_dir, dst)
        dst_mod, dst_test = os.path.join(dst, module + ".py"), os.path.join(dst, test + ".py")
        results = []
        env = dict(os.environ); env["PYTHONUTF8"] = "1"
        for label, mut in mutants:
            with open(dst_mod, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(mut)
            try:
                p = subprocess.run([sys.executable, dst_test], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                                   timeout=timeout, env=env, cwd=dst)
                caught = (p.returncode != 0)
            except subprocess.TimeoutExpired:
                caught = True  # завис на мутанте — считаем пойманным (тест среагировал)
            results.append((label, caught))
            with open(dst_mod, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(src)  # восстановить для следующего
        return verdict(results), results
    finally:
        pass


DEFAULT_SWEEP = ["metrics", "assurance", "doc_consensus", "drift_check",
                 "crdt_merge", "view", "text_mux", "commit_queue"]


def discover_pairs(tools_dir=None, only=None):
    """[(module, test)] для test_X.py, у которых есть X.py. only — множество имён модулей-фильтр."""
    tools_dir = tools_dir or TOOLS
    pairs = []
    for tp in sorted(glob.glob(os.path.join(tools_dir, "test_*.py"))):
        name = os.path.basename(tp)[5:-3]
        if only and name not in only:
            continue
        if os.path.exists(os.path.join(tools_dir, name + ".py")):
            pairs.append((name, "test_" + name))
    return pairs


def _run_one_in(dst, module, test, cap, timeout, env):
    """Мета-тест ОДНОГО модуля в УЖЕ скопированном dst (sweep копирует tools/ один раз) → verdict."""
    dst_mod, dst_test = os.path.join(dst, module + ".py"), os.path.join(dst, test + ".py")
    if not (os.path.exists(dst_mod) and os.path.exists(dst_test)):
        return {"error": "нет модуля/теста"}
    src = open(dst_mod, encoding="utf-8", errors="replace").read()
    mutants = gen_mutants(src, cap)
    if not mutants:
        return {"error": "нет мутантов"}
    results = []
    for label, mut in mutants:
        with open(dst_mod, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(mut)
        try:
            p = subprocess.run([sys.executable, dst_test], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                               timeout=timeout, env=env, cwd=dst)
            caught = (p.returncode != 0)
        except subprocess.TimeoutExpired:
            caught = True
        results.append((label, caught))
    with open(dst_mod, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    return verdict(results)


def sweep(pairs, tools_dir=None, cap=8, timeout=60):
    """Прогон по многим (module,test). Копирует tools/ ОДИН раз (эффективно). → [{module,test,**verdict}]."""
    tools_dir = tools_dir or TOOLS
    tmp_root = os.path.join(ROOT, "tmp-work", "mutmeta_sweep")
    os.makedirs(tmp_root, exist_ok=True)
    tmp, n = os.path.join(tmp_root, "run_%d" % os.getpid()), 0
    while os.path.exists(tmp):
        n += 1; tmp = os.path.join(tmp_root, "run_%d_%d" % (os.getpid(), n))
    dst = os.path.join(tmp, "tools")
    shutil.copytree(tools_dir, dst)
    env = dict(os.environ); env["PYTHONUTF8"] = "1"
    return [{"module": m, "test": t, **_run_one_in(dst, m, t, cap, timeout, env)} for m, t in pairs]


def _opt(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


VALUE_FLAGS = ("--cap",)


def main(argv):
    help_guard(__doc__, argv)
    args, skip = [], False
    for a in argv:                      # позиционные = не флаги И не значения value-флагов (--cap 8)
        if skip:
            skip = False; continue
        if a in VALUE_FLAGS:
            skip = True; continue
        if a.startswith("--"):
            continue
        args.append(a)
    cap = int(_opt(argv, "--cap", "12"))
    if "--sweep" in argv:
        only = set(args) if args else set(DEFAULT_SWEEP)
        res = sweep(discover_pairs(only=only), cap=cap)
        if "--json" in argv:
            print(json.dumps(res, ensure_ascii=False, indent=2)); return 0
        rank = sorted(res, key=lambda r: (not r.get("co_defective"),
                      r.get("mutation_score") if r.get("mutation_score") is not None else 1.0))
        print("=== MUTMETA SWEEP · здоровье детекторов (%d) ===" % len(res))
        for r in rank:
            if "error" in r:
                print("  —  %-15s %s" % (r["module"], r["error"]))
            elif r.get("co_defective"):
                print("  ✗ CO-DEFECTIVE %-15s 0/%d — тест НЕ ловит мутации источника" % (r["module"], r["valid_mutants"]))
            elif (r.get("mutation_score") or 0) < 0.5:
                print("  ⚠ слабый       %-15s score %.2f (%d/%d)" % (r["module"], r["mutation_score"], r["caught"], r["valid_mutants"]))
            else:
                print("  ✓ ок           %-15s score %.2f" % (r["module"], r["mutation_score"]))
        co = [r["module"] for r in res if r.get("co_defective")]
        print("\n  co-defective: %s" % (", ".join(co) or "нет"))
        return 1 if co else 0
    if not args:
        print("mutmeta: нужен <module> или --sweep. Пример: mutmeta.py metrics"); return 2
    module = args[0]
    test = args[1] if len(args) > 1 else "test_" + module
    v, results = run_meta(module, test, cap=cap)
    if "error" in v:
        print("mutmeta: %s" % v["error"]); return 2
    if "--json" in argv:
        print(json.dumps({"module": module, "test": test, **v}, ensure_ascii=False, indent=2)); return 0
    print("=== МЕТА-ТЕСТ ДЕТЕКТОРА · %s ← %s ===" % (module, test))
    print("  мутантов: %d · поймано: %d · mutation-score: %s" % (
        v["valid_mutants"], v["caught"], v["mutation_score"]))
    if v["co_defective"]:
        print("  ✗ CO-DEFECTIVE: тест НЕ ловит НИ ОДНУ мутацию источника — зелёный цвет иллюзорен.")
        print("    (флаг без проверки детектора = вера, не видимость — C-III)")
    elif v["mutation_score"] is not None and v["mutation_score"] < 0.5:
        print("  ⚠ слабый детектор: пропущено %d мутаций: %s" % (len(v["missed"]), v["missed"][:5]))
    else:
        print("  ✓ детектор реагирует на дефекты источника (не со-дефектен)")
    return 1 if v["co_defective"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
