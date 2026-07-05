#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_sandbox_intake_chain
# TYPE: active-script
# DOMAIN: core.sandbox
# DEPTH_LEVEL: 1
# SUMMARY: Tests for read-only sandbox intake chain orchestrator.
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

import sandbox_intake_chain as sic
from test_tmp import temp_dir


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def write_manifest(root):
    write(root / 'manifest.json', json.dumps({
        'name': 'demo',
        'version': '0.1.0',
        'entrypoint': 'src/main.py',
        'schema_version': 'draft-1',
    }, ensure_ascii=False, indent=2))


def test_clean_agent_draft_promotes_to_task_candidate():
    with temp_dir('intake_chain_') as tmp:
        root = Path(tmp)
        write_manifest(root)
        write(root / 'README.md', '[Src](src/main.py)')
        write(root / 'src' / 'main.py', 'def hello():\n    return "ok"\n')
        result = sic.scan(tmp, kind='agent-draft', source_id='clean-draft')
        assert result['schema'] == 'sandbox-intake-result.v1', result
        assert result['source']['execute_allowed'] is False, result
        assert result['risk_summary']['level'] == 'low', result
        assert result['recommendation']['route'] == 'create-promotion-task', result
        assert result['checks']['inventory']['files'] == 3, result
        print('PASS: clean agent draft promotes to task candidate')


def test_python_risk_is_medium_not_execute_permission():
    with temp_dir('intake_chain_') as tmp:
        root = Path(tmp)
        write_manifest(root)
        write(root / 'risk.py', 'import subprocess\ndef run():\n    return open("x")\n')
        result = sic.scan(tmp, kind='external-source')
        assert result['risk_summary']['level'] == 'medium', result
        assert 'python-risk-signals' in result['risk_summary']['warnings'], result
        assert result['source']['execute_allowed'] is False, result
        print('PASS: python risk is medium and execute stays blocked')


def test_broken_link_is_high_and_cli_exit_1():
    with temp_dir('intake_chain_') as tmp:
        root = Path(tmp)
        write_manifest(root)
        write(root / 'README.md', '[Missing](missing.md)')
        result = sic.scan(tmp)
        assert result['risk_summary']['level'] == 'high', result
        assert 'markdown-link-errors' in result['risk_summary']['blocking_reasons'], result
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = sic.main([tmp, '--json'])
        payload = json.loads(buf.getvalue())
        assert code == 1, (code, payload)
        assert payload['risk_summary']['level'] == 'high', payload
        print('PASS: broken link is high and cli exits 1')


def test_schema_error_is_high():
    with temp_dir('intake_chain_') as tmp:
        root = Path(tmp)
        write(root / 'manifest.json', '{"name":"demo"}')
        result = sic.scan(tmp)
        assert result['risk_summary']['level'] == 'high', result
        assert 'schema-errors' in result['risk_summary']['blocking_reasons'], result
        print('PASS: schema error is high')


def test_cli_bad_dir_exit_2_and_text_output():
    with temp_dir('intake_chain_') as tmp:
        root = Path(tmp)
        write_manifest(root)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = sic.main([tmp, '--text'])
        assert code == 0, code
        assert 'SANDBOX INTAKE RESULT' in buf.getvalue(), buf.getvalue()
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = sic.main([str(root / 'missing')])
        assert code == 2, code
        print('PASS: cli bad dir and text output')


def run():
    test_clean_agent_draft_promotes_to_task_candidate()
    test_python_risk_is_medium_not_execute_permission()
    test_broken_link_is_high_and_cli_exit_1()
    test_schema_error_is_high()
    test_cli_bad_dir_exit_2_and_text_output()
    print('\nAll tests passed!')
    return 0


if __name__ == '__main__':
    sys.exit(run())