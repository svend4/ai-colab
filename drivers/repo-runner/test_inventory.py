#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: drivers.repo_runner.test_inventory
# TYPE: active-script
# DOMAIN: drivers.repo-runner
# DEPTH_LEVEL: 1
# SUMMARY: Tests for read-only repo inventory and Python AST integration.
# ==========================================
'''Tests for repo-runner/inventory.py.'''

import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVERS_ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, DRIVERS_ROOT)
from inventory import DEFAULT_MAX_FILES, PathAccessError, clamp_max_files, limit_output, scan_repo
from test_tmp import temp_dir


def test_scan_empty_repo():
    with temp_dir('repo_runner_') as tmp:
        report = scan_repo(tmp)
        assert report['path'] == str(Path(tmp).resolve())
        assert report['summary']['total_files'] == 0
        assert report['summary']['total_size_mb'] == 0.0
        assert report['summary']['has_tests'] is False
        assert report['summary']['python_files_analyzed'] == 0
        print('PASS: empty repo')


def test_scan_python_repo():
    with temp_dir('repo_runner_') as tmp:
        root = Path(tmp)
        (root / 'setup.py').write_text('from setuptools import setup\nsetup(name=\'test\')\n', encoding='utf-8')
        (root / 'requirements.txt').write_text('requests\npytest\n', encoding='utf-8')
        (root / 'src').mkdir()
        (root / 'src' / 'main.py').write_text(
            'import os\nimport requests\n\nclass App:\n    def run(self):\n        return os.system(\'echo x\')\n',
            encoding='utf-8',
        )
        (root / 'tests').mkdir()
        (root / 'tests' / 'test_main.py').write_text('def test_main(): pass\n', encoding='utf-8')
        (root / 'README.md').write_text('# Test repo\n', encoding='utf-8')

        report = scan_repo(tmp)
        assert report['summary']['total_files'] == 5
        assert 'Python' in report['summary']['languages']
        assert report['summary']['has_tests'] is True
        assert report['summary']['has_package_files'] is True
        assert report['summary']['python_files_analyzed'] >= 3
        assert len(report['risks']) > 0

        main = next(item for item in report['python_analysis'] if item['path'] == 'src/main.py')
        modules = {item['module'].lstrip('.') for item in main['imports']}
        classes = {item['name'] for item in main['classes']}
        functions = {item['qualname'] for item in main['functions']}
        risk_names = {item['name'] for item in main['risks']}
        assert {'os', 'requests'}.issubset(modules), main
        assert 'App' in classes, main
        assert 'App.run' in functions, main
        assert {'os', 'requests', 'os.system'}.issubset(risk_names), main
        assert any(r.get('source') == 'python_analyzer' for r in report['risks']), report['risks']
        print('PASS: python repo')


def test_scan_risk_patterns():
    with temp_dir('repo_runner_') as tmp:
        (Path(tmp) / 'danger.py').write_text('eval(\'1+1\')\n', encoding='utf-8')
        report = scan_repo(tmp)
        assert any(r['risk'] == 'potentially dangerous eval' for r in report['risks'])
        assert any(r.get('source') == 'python_analyzer' and 'eval' in r['risk'] for r in report['risks'])
        print('PASS: risk patterns')


def test_nonexistent_path():
    report = scan_repo('/nonexistent/path/12345')
    assert 'error' in report
    print('PASS: nonexistent path')


def test_max_files_and_allowed_root():
    with temp_dir('repo_runner_') as tmp:
        root = Path(tmp)
        (root / 'a.py').write_text('print(\'a\')\n', encoding='utf-8')
        (root / 'b.py').write_text('print(\'b\')\n', encoding='utf-8')
        report = scan_repo('.', max_files=1, base_dir=tmp)
        assert report['summary']['total_files'] == 1
        assert report['summary']['truncated'] is True

        try:
            scan_repo(str(root.parent), base_dir=tmp)
            assert False, 'base_dir does not restrict exit from allowed root'
        except PathAccessError:
            pass
        print('PASS: max files and allowed root')


def test_limit_helpers():
    assert clamp_max_files(DEFAULT_MAX_FILES + 5000) == DEFAULT_MAX_FILES
    assert clamp_max_files(0) == 1
    assert clamp_max_files('not-int') == DEFAULT_MAX_FILES

    with temp_dir('repo_runner_') as tmp:
        root = Path(tmp)
        (root / 'a.py').write_text('print(1)\n', encoding='utf-8')
        report = scan_repo('.', max_files=DEFAULT_MAX_FILES + 5000, base_dir=tmp)
        assert report['max_files'] == DEFAULT_MAX_FILES
        assert report['summary']['max_files'] == DEFAULT_MAX_FILES

    payload = {
        'structure': ['x' * 200 for _ in range(100)],
        'python_analysis': [{'body': 'y' * 200} for _ in range(100)],
    }
    limited = limit_output(payload, max_output_bytes=512)
    assert limited['output_truncated'] is True
    assert 'output_truncated_fields' in limited
    assert len(str(limited)) < len(str(payload))
    print('PASS: limit helpers')

if __name__ == '__main__':
    test_scan_empty_repo()
    test_scan_python_repo()
    test_scan_risk_patterns()
    test_nonexistent_path()
    test_max_files_and_allowed_root()
    test_limit_helpers()
    print('\nAll tests passed!')
