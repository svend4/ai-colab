#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_sandbox_schema_validator
# TYPE: active-script
# DOMAIN: core.sandbox
# DEPTH_LEVEL: 1
# SUMMARY: Tests for read-only sandbox JSON schema validator.
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

import sandbox_schema_validator as sv
from test_tmp import temp_dir


def valid_manifest():
    return {
        'id': 'demo-driver',
        'type': 'driver',
        'title': 'Demo driver',
        'status': 'ready',
        'level': 'L1',
        'mode': 'read-only',
        'owner': 'Codex',
        'risk': 'low',
        'activation': 'manual',
        'interfaces': ['inspect'],
        'inputs': ['path'],
        'outputs': ['summary'],
        'sandbox': 'required-before-run-or-test',
        'secrets': 'forbidden-in-repo',
        'source_last_verified': '2026-06-24',
        'timeout_seconds': 30,
        'max_output_bytes': 1048576,
        'audit': False,
        'related': ['drivers/SCHEMA.md'],
    }


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def issue_codes(report):
    return {issue['code'] for item in report['files'] for issue in item['issues']}


def test_valid_manifest_and_json():
    with temp_dir('schema_validator_') as tmp:
        root = Path(tmp)
        write_json(root / 'manifest.json', valid_manifest())
        write_json(root / 'config.json', {'ok': True})
        report = sv.scan(tmp)
        assert report['summary']['json_files'] == 2, report
        assert report['summary']['manifest_files'] == 1, report
        assert report['summary']['errors'] == 0, report
        print('PASS: valid manifest and json')


def test_invalid_manifest_rules():
    with temp_dir('schema_validator_') as tmp:
        root = Path(tmp)
        bad = valid_manifest()
        bad.pop('title')
        bad['risk'] = 'medium'
        bad['audit'] = False
        bad['interfaces'] = 'inspect'
        bad['source_last_verified'] = '24-06-2026'
        bad['timeout_seconds'] = 0
        bad['secrets'] = 'in-repo'
        write_json(root / 'manifest.json', bad)
        report = sv.scan(tmp)
        codes = issue_codes(report)
        assert 'missing-title' in codes, codes
        assert 'audit-required' in codes, codes
        assert 'invalid-interfaces' in codes, codes
        assert 'invalid-source-last-verified' in codes, codes
        assert 'invalid-timeout_seconds' in codes, codes
        assert 'secrets-in-repo' in codes, codes
        assert report['summary']['errors'] >= 6, report
        print('PASS: invalid manifest rules')


def test_invalid_json_parse():
    with temp_dir('schema_validator_') as tmp:
        root = Path(tmp)
        (root / 'broken.json').write_text('{bad json', encoding='utf-8')
        report = sv.scan(tmp)
        assert 'invalid-json' in issue_codes(report), report
        assert report['summary']['errors'] == 1, report
        print('PASS: invalid json parse')


def test_cli_json_exit_codes():
    with temp_dir('schema_validator_') as tmp:
        root = Path(tmp)
        write_json(root / 'manifest.json', valid_manifest())
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = sv.main([tmp, '--json'])
        assert code == 0
        payload = json.loads(buf.getvalue())
        assert payload['summary']['ok'] is True, payload

        (root / 'bad.json').write_text('{bad json', encoding='utf-8')
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = sv.main([tmp, '--json'])
        assert code == 1
        print('PASS: cli json exit codes')


def test_max_bytes_warning():
    with temp_dir('schema_validator_') as tmp:
        root = Path(tmp)
        (root / 'large.json').write_text('{"ok": true}', encoding='utf-8')
        report = sv.scan(tmp, max_bytes=2)
        assert report['summary']['errors'] == 0, report
        assert report['summary']['warnings'] == 1, report
        assert 'too-large' in issue_codes(report), report
        print('PASS: max bytes warning')


def run():
    test_valid_manifest_and_json()
    test_invalid_manifest_rules()
    test_invalid_json_parse()
    test_cli_json_exit_codes()
    test_max_bytes_warning()
    print('\nAll tests passed!')
    return 0


if __name__ == '__main__':
    sys.exit(run())