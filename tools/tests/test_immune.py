"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_immune
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Скрипт test_immune.py. Описание сгенерировано автоматически.
# ==========================================
"""
"""Тест immune.py — иммунный детектор аномалий (median/MAD + порог + инцидент-сценарий)."""
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
import immune

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    fails = []

    # median
    if immune._median([1, 3, 2]) != 2 or immune._median([1, 2, 3, 4]) != 2.5:
        fails.append("_median неверна")
    # MAD робастна к выбросу: [1,2,3,4,100] median=3, |dev|=[2,1,0,1,97], median(dev)=1
    # (выброс 100 НЕ раздувает MAD — в этом робастность против std, который был бы огромен)
    m = immune._median([1, 2, 3, 4, 100])
    if immune._mad([1, 2, 3, 4, 100], m) != 1:
        fails.append("_mad не робастна к выбросу: %s" % immune._mad([1, 2, 3, 4, 100], m))

    # профиль из «нормальных» коммитов (~3 файла, ~2 удаления, добавление-доминантных)
    normal = [{"files": 3, "deletions": 2, "additions": 5}] * 30 + [{"files": 5, "deletions": 4, "additions": 8}] * 20
    prof = immune.profile(normal)
    if prof["n_commits"] != 50:
        fails.append("profile n_commits != 50")
    if not (2 <= prof["files_median"] <= 5):
        fails.append("files_median вне нормы: %s" % prof["files_median"])

    # ИНЦИДЕНТ: 147 файлов / 8643 удал / 269 добавл → many_files + net_deletion + large_deletion → АНОМАЛИЯ
    incident = immune.assess({"files": 147, "deletions": 8643, "additions": 269}, prof)
    if not incident["anomaly"] or len(incident["fired"]) < 2:
        fails.append("инцидент outbox-strip НЕ аномалия (провал иммунитета!): fired=%s" % incident["fired"])

    # нормальный коммит → 0 антител → НЕ аномалия
    if immune.assess({"files": 3, "deletions": 2, "additions": 5}, prof)["anomaly"]:
        fails.append("нормальный коммит ложно аномалия")

    # КВОРУМ: легитимная КРУПНАЯ ДОБАВКА (много файлов, мало удалений, addition-доминантна) →
    # только many_files (1 антитело) < кворум → НЕ аномалия (ключевое отличие стрипа от роста)
    big_add = immune.assess({"files": 100, "deletions": 3, "additions": 4000}, prof)
    fired_dims = {f["dim"] for f in big_add["fired"]}
    if big_add["anomaly"]:
        fails.append("легитимная крупная добавка ложно аномалия: %s" % big_add["fired"])
    if "many_files" not in fired_dims:
        fails.append("many_files-антитело должно сигналить на 100 файлов")

    # guard: <MIN_SAMPLE → воздержаться
    thin = immune.profile([{"files": 3, "deletions": 2, "additions": 5}] * 5)
    g = immune.assess({"files": 999, "deletions": 999, "additions": 0}, thin)
    if g["anomaly"] or not g.get("insufficient"):
        fails.append("малая выборка дала вердикт (должна воздержаться)")

    # === C0: fail-closed при сбое git (сбой НЕ маскируется под «короткую историю», exit 0) ===
    # 1) _git пробрасывает GitError при недоступном git (раньше глотал OSError в "")
    real_run = immune.subprocess.run
    def _boom(*a, **k):
        raise OSError("git недоступен (симуляция)")
    immune.subprocess.run = _boom
    try:
        try:
            immune._git(["log", "-1"])
            fails.append("_git проглотил OSError в пустую строку (fail-open)")
        except immune.GitError:
            pass
    finally:
        immune.subprocess.run = real_run

    # 2) git недоступен → main() возвращает ненулевой exit (fail-closed), а не 0
    import tempfile
    real_root = immune.ROOT
    immune.ROOT = tempfile.mkdtemp()  # не-git каталог: git выдаёт ненулевой код («not a git repository»)
    try:
        rc = immune.main(["--json"])
    finally:
        immune.ROOT = real_root
    if rc == 0:
        fails.append("git-сбой (не-git каталог) дал exit 0 — детектор молча самовыключился")

    # 3) страховочная сверка: git log молча пуст, а rev-list видит 407 коммитов → сбой, exit != 0
    #    (воспроизводит наблюдённый инцидент: «0 < 10 коммитов» при 407 реальных)
    real_git = immune._git
    def _fake_git(args):
        if args[0] == "log":
            return ""          # история «потерялась» при сборе
        if args[0] == "rev-list":
            return "407\n"     # а репозиторий её видит
        return ""
    immune._git = _fake_git
    try:
        rc = immune.main(["--json"])
    finally:
        immune._git = real_git
    if rc == 0:
        fails.append("пустой git log при 407 в rev-list дал exit 0 (сверка rev-list не сработала)")

    # 4) честно короткая история (5 коммитов и rev-list подтверждает 5) → по-прежнему exit 0
    def _short_git(args):
        if args[0] == "log":
            return "\n".join("C%s\n1\t1\tf.md" % ("a" * 40) for _ in range(5))
        if args[0] == "rev-list":
            return "5\n"
        return ""              # пустой diff рабочего дерева
    immune._git = _short_git
    try:
        rc = immune.main([])
    finally:
        immune._git = real_git
    if rc != 0:
        fails.append("честно короткая история (5 коммитов) должна давать exit 0, получено %s" % rc)

    if fails:
        print("FAIL test_immune:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_immune: median + MAD-робастность + профиль + инцидент=аномалия + норма=ок + guard-малой-выборки"
          " + fail-closed при сбое git (C0)")


if __name__ == "__main__":
    main()
