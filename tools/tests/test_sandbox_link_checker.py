#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_sandbox_link_checker
# TYPE: active-script
# DOMAIN: core.sandbox
# DEPTH_LEVEL: 1
# SUMMARY: Tests for sandbox Markdown link checker.
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
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(_TOOLS_DIR)  # tools/ — тест перенесён в tools/tests/ (C14)
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'drivers'))

import sandbox_link_checker as lc
from test_tmp import temp_dir


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_clean_relative_and_root_links():
    with temp_dir('sandbox_links_') as tmp:
        root = Path(tmp)
        write(root / 'README.md', '[Sub](sub/page.md) [Root](/docs/ref.md)')
        write(root / 'sub' / 'page.md', '[Back](../README.md)')
        write(root / 'docs' / 'ref.md', '# Ref')
        report = lc.scan(tmp)
        assert report['ok'] is True, report
        assert report['files_scanned'] == 3, report
        print('PASS: clean relative and root links')


def test_broken_link_with_anchor_reports_line():
    with temp_dir('sandbox_links_') as tmp:
        root = Path(tmp)
        write(root / 'README.md', 'ok\n[Missing](missing.md#section)\n')
        report = lc.scan(tmp)
        assert report['ok'] is False, report
        assert report['issue_count'] == 1, report
        issue = report['issues'][0]['broken_links'][0]
        assert issue['kind'] == 'missing', issue
        assert issue['line'] == 2, issue
        assert issue['resolved'] == 'missing.md', issue
        print('PASS: broken link with anchor reports line')


def test_ignored_external_and_anchor_links():
    with temp_dir('sandbox_links_') as tmp:
        root = Path(tmp)
        write(root / 'README.md', '[Web](https://example.com) [Mail](mailto:a@example.com) [Anchor](#local)')
        report = lc.scan(tmp)
        assert report['ok'] is True, report
        assert report['issue_count'] == 0, report
        print('PASS: ignored external and anchor links')


def test_outside_root_traversal():
    with temp_dir('sandbox_links_') as tmp:
        root = Path(tmp)
        write(root / 'nested' / 'README.md', '[Escape](../../outside.md)')
        report = lc.scan(tmp)
        assert report['ok'] is False, report
        issue = report['issues'][0]['broken_links'][0]
        assert issue['kind'] == 'outside-root', issue
        assert issue['line'] == 1, issue
        print('PASS: outside-root traversal')


def test_cli_exit_codes_and_json():
    with temp_dir('sandbox_links_') as tmp:
        root = Path(tmp)
        write(root / 'README.md', '[Ok](ok.md)')
        write(root / 'ok.md', '# Ok')
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = lc.main([tmp])
        assert code == 0, code
        assert json.loads(buf.getvalue())['ok'] is True

        write(root / 'bad.md', '[Bad](missing.md)')
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = lc.main([tmp, '--json'])
        payload = json.loads(buf.getvalue())
        assert code == 1, (code, payload)
        assert payload['issue_count'] == 1, payload

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = lc.main([str(root / 'missing-dir')])
        assert code == 2, code
        print('PASS: cli exit codes and json')


def run():
    test_clean_relative_and_root_links()
    test_broken_link_with_anchor_reports_line()
    test_ignored_external_and_anchor_links()
    test_outside_root_traversal()
    test_cli_exit_codes_and_json()
    print('\nAll tests passed!')
    return 0


if __name__ == '__main__':
    sys.exit(run())