"""Тест immune.py — иммунный детектор аномалий (median/MAD + порог + инцидент-сценарий)."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
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

    if fails:
        print("FAIL test_immune:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_immune: median + MAD-робастность + профиль + инцидент=аномалия + норма=ок + guard-малой-выборки")


if __name__ == "__main__":
    main()
