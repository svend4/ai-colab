# ast: allow-eval
# ast: allow-subprocess
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.tests.test_python_analyzer
# TYPE: active-script
# DOMAIN: core.code-analysis
# DEPTH_LEVEL: 1
# SUMMARY: Tests for read-only Python AST analyzer.
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

import python_analyzer as pa
from test_tmp import temp_dir


SAMPLE = '''
import os
import subprocess as sp
from sys import argv

class Worker:
    def run(self):
        return os.system('echo x')

def main():
    return argv

async def fetch():
    return eval('1')
'''


def test_analyze_source():
    result = pa.analyze_source(SAMPLE, path='sample.py')
    assert result['syntax_ok'] is True
    modules = {item['module'].lstrip('.') for item in result['imports']}
    assert {'os', 'subprocess', 'sys'}.issubset(modules), modules
    classes = {item['name'] for item in result['classes']}
    functions = {item['qualname'] for item in result['functions']}
    risks = {item['name'] for item in result['risks']}
    assert 'Worker' in classes, classes
    assert {'Worker.run', 'main', 'fetch'}.issubset(functions), functions
    assert {'os', 'subprocess', 'sys', 'os.system', 'eval'}.issubset(risks), risks
    print('PASS: analyze source')


def test_analyze_file_and_cli_json():
    with temp_dir('py_analyzer_') as tmp:
        root = Path(tmp)
        sample = root / 'sample.py'
        sample.write_text(SAMPLE, encoding='utf-8')
        result = pa.analyze_file('sample.py', base_dir=tmp)
        assert result['path'] == 'sample.py', result
        assert result['summary']['classes'] == 1, result

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pa.main(['sample.py', '--base', tmp, '--json'])
        assert code == 0
        payload = json.loads(buf.getvalue())
        assert payload['path'] == 'sample.py', payload
        assert payload['summary']['functions'] == 3, payload
    print('PASS: file and cli json')


def test_syntax_error_is_data():
    result = pa.analyze_source('def broken(:\n', path='broken.py')
    assert result['syntax_ok'] is False
    assert result['risks'][0]['name'] == 'SyntaxError', result
    print('PASS: syntax error')


def test_base_dir_blocks_escape():
    with temp_dir('py_analyzer_') as tmp:
        try:
            pa.analyze_file(str(Path(tmp).parent / 'outside.py'), base_dir=tmp)
            assert False, 'base_dir did not block path escape'
        except ValueError:
            pass
    print('PASS: base dir blocks escape')


def run():
    test_analyze_source()
    test_analyze_file_and_cli_json()
    test_syntax_error_is_data()
    test_base_dir_blocks_escape()
    print('\nAll tests passed!')
    return 0


if __name__ == '__main__':
    sys.exit(run())
