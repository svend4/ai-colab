#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.test_sandbox
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: Tests for external-source read-only sandbox intake.
# ==========================================
'''Tests for tools/sandbox.py read-only external-source intake.'''
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'drivers'))
import sandbox as sb
from test_tmp import temp_dir


def cleanup(source_id):
    for p in (
        os.path.join(sb.INBOX, '%s.md' % source_id),
        os.path.join(sb.REPORTS, '%s-inventory.md' % source_id),
    ):
        try:
            os.remove(p)
        except OSError:
            pass


def test_fixture_intake():
    sid = '_sbtest'
    cleanup(sid)
    try:
        r = sb.intake(sid, os.path.join(ROOT, 'data', 'fixtures'), note='test intake')
        assert os.path.exists(r['manifest']) and os.path.exists(r['report']), r
        assert sid in sb.list_sources(), sb.list_sources()
        rep = open(r['report'], encoding='utf-8').read()
        assert 'Inventory:' in rep and 'read-only' in rep, rep[:200]
        man = open(r['manifest'], encoding='utf-8').read()
        assert 'type: external-source' in man and 'status: quarantine' in man, man[:200]
        print('PASS: fixture intake')
    finally:
        cleanup(sid)


def test_python_ast_intake_report():
    sid = '_sbtest_py'
    cleanup(sid)
    try:
        with temp_dir('sandbox_py_') as tmp:
            src = Path(tmp)
            (src / 'app.py').write_text(
                'import os\n\nclass App:\n    def run(self):\n        return os.system(\'echo x\')\n',
                encoding='utf-8',
            )
            r = sb.intake(sid, tmp, note='python ast intake')
            rep = open(r['report'], encoding='utf-8').read()
            assert 'Python semantic analysis (read-only AST)' in rep, rep
            assert '`app.py`' in rep, rep
            assert 'source=python_analyzer' in rep, rep
            print('PASS: python ast intake report')
    finally:
        cleanup(sid)


def run():
    ok = True
    try:
        test_fixture_intake()
        test_python_ast_intake_report()
        print('TESTS OK sandbox: read-only intake')
    except AssertionError as exc:
        ok = False
        print('TEST FAIL:', exc)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run())
