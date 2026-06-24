#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# ==========================================
# [FILE ID CARD]
# ID: tools.sandbox_intake_chain
# TYPE: active-script
# DOMAIN: core.sandbox
# DEPTH_LEVEL: 1
# SUMMARY: Unified read-only sandbox intake chain result for external sources and agent drafts.
# ==========================================
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import python_analyzer
import sandbox_link_checker
import sandbox_schema_validator

SKIP_DIRS = {'.git', '__pycache__', '.mypy_cache', '.pytest_cache', 'node_modules', '.venv', 'venv'}


def _rel(path, base):
    return os.path.relpath(os.path.abspath(path), os.path.abspath(base)).replace(os.sep, '/')


def _inside(path, base):
    try:
        return os.path.commonpath([os.path.abspath(path), os.path.abspath(base)]) == os.path.abspath(base)
    except ValueError:
        return False


def _display_path(path):
    return _rel(path, ROOT) if _inside(path, ROOT) else os.path.abspath(path)


def _walk_files(base):
    base = os.path.abspath(base)
    for root, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            yield os.path.join(root, name)


def _status(ok=True, warn=False, error=False):
    if error:
        return 'error'
    if warn:
        return 'warn'
    return 'ok' if ok else 'skipped'


def file_inventory(base):
    files = list(_walk_files(base))
    by_ext = {}
    total_bytes = 0
    markdown = []
    python = []
    manifests = []
    for path in files:
        try:
            total_bytes += os.path.getsize(path)
        except OSError:
            pass
        ext = os.path.splitext(path)[1].lower() or '<none>'
        by_ext[ext] = by_ext.get(ext, 0) + 1
        rel = _rel(path, base)
        if ext == '.md':
            markdown.append(rel)
        if ext == '.py':
            python.append(rel)
        if os.path.basename(path) == 'manifest.json':
            manifests.append(rel)
    return {
        'status': 'ok',
        'files': len(files),
        'total_bytes': total_bytes,
        'by_extension': dict(sorted(by_ext.items())),
        'markdown_files': markdown,
        'python_files': python,
        'manifest_files': manifests,
    }


def python_ast_check(base, max_files=200):
    py_files = [p for p in _walk_files(base) if p.lower().endswith('.py')]
    results = []
    risks = []
    errors = []
    for path in py_files[:max_files]:
        try:
            item = python_analyzer.analyze_file(path, base_dir=base)
        except Exception as exc:
            item = {
                'path': _rel(path, base),
                'syntax_ok': None,
                'imports': [],
                'classes': [],
                'functions': [],
                'risks': [],
                'summary': {'imports': 0, 'classes': 0, 'functions': 0, 'risks': 0},
                'error': {'type': type(exc).__name__, 'message': str(exc)},
            }
        item['file'] = item.get('path', _rel(path, base))
        if item.get('risks'):
            for risk in item['risks']:
                risks.append({'file': item['file'], 'risk': risk})
        if item.get('syntax_ok') is False or item.get('error'):
            errors.append({'file': item['file'], 'error': item.get('error') or 'syntax-error'})
        results.append(item)
    truncated = len(py_files) > max_files
    return {
        'status': _status(ok=True, warn=bool(risks) or truncated, error=bool(errors)),
        'tool': 'tools/python_analyzer.py',
        'files_found': len(py_files),
        'files_checked': len(results),
        'truncated': truncated,
        'risks': risks,
        'errors': errors,
        'results': results,
    }


def schema_check(base):
    report = sandbox_schema_validator.scan(base)
    results = []
    errors = []
    warnings = []
    for item in report.get('files', []):
        copied = {
            'file': item.get('path'),
            'kind': item.get('kind'),
            'issues': item.get('issues', []),
        }
        item_errors = [i for i in copied['issues'] if i.get('severity') != 'warning']
        item_warnings = [i for i in copied['issues'] if i.get('severity') == 'warning']
        copied['status'] = _status(ok=True, warn=bool(item_warnings), error=bool(item_errors))
        for issue in item_errors:
            errors.append({'file': copied['file'], 'issue': issue})
        for issue in item_warnings:
            warnings.append({'file': copied['file'], 'issue': issue})
        results.append(copied)
    summary = report.get('summary', {})
    return {
        'status': _status(ok=True, warn=bool(warnings), error=bool(errors)),
        'tool': 'tools/sandbox_schema_validator.py',
        'json_files_checked': summary.get('json_files', 0),
        'manifests_checked': summary.get('manifest_files', 0),
        'errors': errors,
        'warnings': warnings,
        'results': results,
    }


def markdown_link_check(base):
    report = sandbox_link_checker.scan(base)
    issues = report.get('issues') or []
    return {
        'status': _status(ok=report.get('ok', False), error=bool(issues)),
        'tool': 'tools/sandbox_link_checker.py',
        'files_checked': report.get('files_scanned', 0),
        'issue_count': report.get('issue_count', 0),
        'issues': issues,
    }


def risk_summary(checks):
    blocking = []
    warnings = []
    if checks['schema']['status'] == 'error':
        blocking.append('schema-errors')
    if checks['markdown_links']['status'] == 'error':
        blocking.append('markdown-link-errors')
    if checks['python_ast']['status'] == 'error':
        blocking.append('python-parse-errors')
    if checks['python_ast'].get('risks'):
        warnings.append('python-risk-signals')
    if checks['schema'].get('warnings'):
        warnings.append('schema-warnings')

    if blocking:
        level = 'high'
        route = 'ask-agent-revision'
    elif warnings:
        level = 'medium'
        route = 'keep-quarantine'
    else:
        level = 'low'
        route = 'keep-quarantine'

    return {
        'level': level,
        'execute_blocked': True,
        'blocking_reasons': blocking,
        'warnings': warnings,
        'route': route,
    }


def scan(base, source_id=None, kind=None, max_python_files=200):
    base = os.path.abspath(base)
    if kind is None:
        norm = base.replace('\\', '/').lower()
        kind = 'agent-draft' if '/sandbox/drafts/' in norm or norm.endswith('/sandbox/drafts') else 'external-source'
    source_id = source_id or os.path.basename(base.rstrip(os.sep)) or 'sandbox-source'

    checks = {
        'inventory': file_inventory(base),
        'python_ast': python_ast_check(base, max_files=max_python_files),
        'schema': schema_check(base),
        'markdown_links': markdown_link_check(base),
    }
    risk = risk_summary(checks)
    recommendation = {
        'route': risk['route'],
        'human_gate_required': risk['level'] == 'high',
        'next_task_proposal': 'create a separate promotion or revision task; execute remains blocked',
    }
    if kind == 'agent-draft' and risk['level'] == 'low':
        recommendation['route'] = 'create-promotion-task'
        recommendation['human_gate_required'] = False
        recommendation['next_task_proposal'] = 'review draft and create a normal claimed promotion task if useful'

    return {
        'schema': 'sandbox-intake-result.v1',
        'source': {
            'id': source_id,
            'kind': kind,
            'path': _display_path(base),
            'mode': 'read-only',
            'execute_allowed': False,
        },
        'checks': checks,
        'risk_summary': {
            'level': risk['level'],
            'execute_blocked': True,
            'blocking_reasons': risk['blocking_reasons'],
            'warnings': risk['warnings'],
        },
        'recommendation': recommendation,
        'evidence': {
            'commands': [
                'python tools/sandbox_intake_chain.py %s --json' % _display_path(base),
            ],
            'tools': [
                'tools/python_analyzer.py',
                'tools/sandbox_schema_validator.py',
                'tools/sandbox_link_checker.py',
            ],
        },
    }


def render_text(result):
    lines = [
        'SANDBOX INTAKE RESULT',
        'source: %s (%s)' % (result['source']['id'], result['source']['kind']),
        'execute_allowed: %s' % result['source']['execute_allowed'],
        'risk: %s' % result['risk_summary']['level'],
        'route: %s' % result['recommendation']['route'],
        'checks:',
    ]
    for name, payload in result['checks'].items():
        lines.append('- %s: %s' % (name, payload.get('status')))
    if result['risk_summary']['blocking_reasons']:
        lines.append('blocking: ' + ', '.join(result['risk_summary']['blocking_reasons']))
    if result['risk_summary']['warnings']:
        lines.append('warnings: ' + ', '.join(result['risk_summary']['warnings']))
    return '\n'.join(lines)


def build_parser():
    p = argparse.ArgumentParser(description='Build one read-only sandbox intake result from current static tools.')
    p.add_argument('target', help='Sandbox source or draft directory to inspect')
    p.add_argument('--kind', choices=['external-source', 'agent-draft'], default=None)
    p.add_argument('--source-id', default=None)
    p.add_argument('--max-python-files', type=int, default=200)
    p.add_argument('--json', action='store_true', help='Print JSON output')
    p.add_argument('--text', action='store_true', help='Print compact text output')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print(json.dumps({'error': 'not-a-directory', 'path': args.target}, ensure_ascii=False, indent=2))
        return 2
    result = scan(target, source_id=args.source_id, kind=args.kind, max_python_files=args.max_python_files)
    if args.text:
        print(render_text(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['risk_summary']['level'] == 'high' else 0


if __name__ == '__main__':
    sys.exit(main())