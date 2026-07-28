"""
# ==========================================
# [FILE ID CARD]
# ID: tools.test_bulk_guard_range
# TYPE: active-script
# DOMAIN: core.validation
# DEPTH_LEVEL: 1
# SUMMARY: Быстрые mock-тесты range-режима bulk_guard для merge-gate/CI.
# ==========================================
"""
import contextlib
import io
import os
import sys

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import bulk_guard as bg

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


B = "b" * 40
C1 = "1" * 40
C2 = "2" * 40
H = "h" * 40


class FakeGit:
    def __init__(self, refs, commits, parents, diffs, tags=None, summaries=None):
        self.refs = dict(refs)
        self.commits = list(commits)
        self.parents = dict(parents)
        self.diffs = dict(diffs)
        self.tags = dict(tags or {})
        self.summaries = dict(summaries or {})
        for value in list(self.refs.values()) + self.commits + list(self.parents.values()):
            self.refs.setdefault(value, value)

    def resolve(self, name):
        return self.refs.get(name, name if name in self.refs.values() else None)

    def __call__(self, args, timeout=30):
        if args[:2] == ["rev-parse", "--verify"]:
            ref = args[2]
            if ref.endswith("^{commit}"):
                resolved = self.resolve(ref[:-9])
                return (0, resolved + "\n", "") if resolved else (1, "", "unknown ref")
            if ref.endswith("^1"):
                commit = self.resolve(ref[:-2])
                parent = self.parents.get(commit)
                return (0, parent + "\n", "") if parent else (1, "", "unknown parent")
            resolved = self.resolve(ref)
            return (0, resolved + "\n", "") if resolved else (1, "", "unknown ref")

        if args[:2] == ["rev-list", "--reverse"]:
            spec = args[2]
            if ".." not in spec:
                return 1, "", "bad range"
            return 0, "\n".join(self.commits) + ("\n" if self.commits else ""), ""

        if args and args[0] == "diff":
            left, right = args[-3], args[-2]
            return 0, self.diffs.get((left, right), ""), ""

        if args[:3] == ["tag", "--list", "backup-*"]:
            return 0, "\n".join(sorted(self.tags)) + ("\n" if self.tags else ""), ""

        if args[:2] == ["tag", "--points-at"]:
            ref = self.resolve(args[2]) or args[2]
            names = [name for name, target in sorted(self.tags.items()) if target == ref and name.startswith("backup-")]
            return 0, "\n".join(names) + ("\n" if names else ""), ""

        if args[:3] == ["log", "-1", "--format=%s"]:
            commit = self.resolve(args[3]) or args[3]
            return 0, self.summaries.get(commit, "") + "\n", ""

        return 1, "", "unexpected git call: %r" % (args,)


@contextlib.contextmanager
def fake_git(fake):
    old_proc = bg._git_proc
    old_root = bg.ROOT
    bg._git_proc = fake
    bg.ROOT = "FAKE-ROOT"
    try:
        yield
    finally:
        bg._git_proc = old_proc
        bg.ROOT = old_root


def assert_true(fails, cond, message):
    if not cond:
        fails.append(message)


def check_with(fake, spec="BASE..HEAD"):
    with fake_git(fake):
        return bg.check_range(spec)


def test_delete_then_restore_hidden(fails):
    fake = FakeGit(
        refs={"BASE": B, "HEAD": C2},
        commits=[C1, C2],
        parents={C1: B, C2: C1},
        diffs={(B, C2): "", (B, C1): "0\t600\tlive.md\n", (C1, C2): "600\t0\tlive.md\n"},
        summaries={C1: "bulk delete", C2: "restore"},
    )
    r = check_with(fake)
    assert_true(fails, r["verdict"] == "STOP-uninsured", "delete+restore должен быть STOP")
    assert_true(fails, r["hidden_by_aggregate"], "delete+restore должен быть hidden_by_aggregate")
    assert_true(fails, r["aggregate"]["deletions"] == 0, "aggregate должен скрывать восстановленное удаление")
    assert_true(fails, any(c["stat"]["deletions"] >= 600 for c in r["commits"]), "per-commit deletion не найден")


def test_backup_on_parent_insures(fails):
    fake = FakeGit(
        refs={"BASE": B, "HEAD": C1},
        commits=[C1],
        parents={C1: B},
        diffs={(B, C1): "0\t600\tlive.md\n"},
        tags={"backup-range-parent": B},
    )
    r = check_with(fake)
    assert_true(fails, r["verdict"] == "ok-insured", "backup на parent/base должен страховать bulk range")
    assert_true(fails, r["commits"][0]["backup_on_parent"] == ["backup-range-parent"], "backup_on_parent не найден")


def test_backup_on_head_does_not_insure(fails):
    fake = FakeGit(
        refs={"BASE": B, "HEAD": C1},
        commits=[C1],
        parents={C1: B},
        diffs={(B, C1): "0\t600\tlive.md\n"},
        tags={"backup-range-head": C1},
    )
    r = check_with(fake)
    assert_true(fails, r["verdict"] == "STOP-uninsured", "backup на финальном HEAD не должен страховать уже сделанное удаление")
    assert_true(fails, r["insurance"]["backup_on_head"] == ["backup-range-head"], "backup_on_head должен быть виден в JSON")


def test_churn_split_bulk(fails):
    fake = FakeGit(
        refs={"BASE": B, "HEAD": C2},
        commits=[C1, C2],
        parents={C1: B, C2: C1},
        diffs={(B, C2): "0\t600\tall.md\n", (B, C1): "0\t300\ta.md\n", (C1, C2): "0\t300\tb.md\n"},
    )
    r = check_with(fake)
    assert_true(fails, r["verdict"] == "STOP-uninsured", "split churn 300+300 должен быть STOP")
    assert_true(fails, r["churn"]["deletions"] >= 600, "churn должен суммировать удаления по commits")
    assert_true(fails, any(b["type"] == "churn" for b in r["blocked_by"]), "blocked_by должен содержать churn")


def test_invalid_and_unknown_args(fails):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = bg.main(["--range", "HEAD...HEAD", "--json"])
    assert_true(fails, rc == 2, "invalid range syntax должен давать exit 2")
    assert_true(fails, "ERROR" in buf.getvalue(), "invalid range должен печатать ERROR JSON")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = bg.main(["--definitely-unknown"])
    assert_true(fails, rc == 2, "unknown arg должен давать exit 2")


def test_rename_not_bulk(fails):
    fake = FakeGit(
        refs={"BASE": B, "HEAD": C1},
        commits=[C1],
        parents={C1: B},
        diffs={(B, C1): "0\t0\told.md => new.md\n"},
    )
    r = check_with(fake)
    assert_true(fails, r["verdict"] == "ok-not-bulk", "pure rename не должен считаться bulk deletion")
    assert_true(fails, r["aggregate"]["deletions"] == 0, "rename aggregate deletions должен быть 0")


def test_json_shape(fails):
    fake = FakeGit(
        refs={"BASE": B, "HEAD": C1},
        commits=[C1],
        parents={C1: B},
        diffs={(B, C1): "1\t0\tx.md\n"},
    )
    with fake_git(fake):
        r = bg.check_range("BASE..HEAD", strict=True)
    for key in ("aggregate", "commits", "churn", "insurance", "verdict", "thresholds", "errors"):
        assert_true(fails, key in r, "range JSON без ключа %s" % key)


def main():
    fails = []
    for test in (
        test_delete_then_restore_hidden,
        test_backup_on_parent_insures,
        test_backup_on_head_does_not_insure,
        test_churn_split_bulk,
        test_invalid_and_unknown_args,
        test_rename_not_bulk,
        test_json_shape,
    ):
        test(fails)
    if fails:
        print("FAIL test_bulk_guard_range:")
        for item in fails:
            print("  -", item)
        sys.exit(1)
    print("OK test_bulk_guard_range: mocked range aggregate+per-commit+churn, parent insurance, head-not-insurance, hidden delete+restore, rename, invalid args")


if __name__ == "__main__":
    main()