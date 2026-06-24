#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.sandbox
# TYPE: active-script
# DOMAIN: core
# DEPTH_LEVEL: 1
# SUMMARY: External-source read-only intake and inventory reporting.
# ==========================================
'''External-source intake for generic sandbox sources.

Automates S1 intake, S3 read-only inventory, and S7 report stages from
`docs/external-code-sandbox.md`. It registers an external source folder,
scans it with repo-runner inventory, and writes a committable report.
Target code is never executed. Execute remains gated by
`docs/execute-sandbox-preflight.md`.

CLI:
    python tools/sandbox.py intake <source-id> --from <path> [--note ...]
    python tools/sandbox.py list
'''
import importlib.util
import os
import sys
from _ioutil import configure_output

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVERS = os.path.join(ROOT, 'drivers')
SANDBOX = os.path.join(ROOT, 'sandbox')
INBOX = os.path.join(SANDBOX, 'inbox')
REPORTS = os.path.join(SANDBOX, 'reports')

configure_output()


def _load(name, *parts):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DRIVERS, *parts))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inv = _load('sb_inventory', 'repo-runner', 'inventory.py')


def _risk_label(risk):
    if isinstance(risk, str):
        return risk
    loc = risk.get('file') or risk.get('path') or '?'
    line = risk.get('line')
    suffix = ':%s' % line if line else ''
    text = risk.get('risk') or risk.get('name') or risk
    severity = risk.get('severity', 'unknown')
    source = risk.get('source')
    source_suffix = ' source=%s' % source if source else ''
    return '%s%s: %s [%s]%s' % (loc, suffix, text, severity, source_suffix)


def _summary_files(summary):
    return summary.get('total_files', summary.get('files', summary.get('file_count', '?')))


def intake(source_id, from_path, note='', max_files=2000):
    src = os.path.abspath(os.path.expanduser(from_path))
    if not os.path.isdir(src):
        raise NotADirectoryError('источник не найден: %s' % src)
    os.makedirs(INBOX, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)

    # S3 read-only inventory: target code is not executed; allowed-root is the source itself.
    report = inv.scan_repo(src, max_files=max_files, base_dir=src)
    summary = report.get('summary', {}) if isinstance(report, dict) else {}
    risks = report.get('risks', []) if isinstance(report, dict) else []
    py_analysis = report.get('python_analysis', []) if isinstance(report, dict) else []

    manifest = os.path.join(INBOX, '%s.md' % source_id)
    with open(manifest, 'w', encoding='utf-8', newline='\n') as f:
        f.write(
            '---\nid: %s\ntype: external-source\nfrom: %s\nstatus: quarantine\nmode: read-only\n'
            'secrets: unknown-until-reviewed\nnote: %s\n---\n\n# Внешний источник: %s\n\n'
            'Зарегистрирован для read-only intake (D-016/D-017, контракт `docs/external-code-sandbox.md`).\n'
            'Код НЕ запускается до закрытия gate `docs/execute-sandbox-preflight.md`.\n'
            % (source_id, src, note, source_id)
        )

    rep = os.path.join(REPORTS, '%s-inventory.md' % source_id)
    langs = summary.get('languages', summary.get('by_lang', {}))
    with open(rep, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Inventory: %s (read-only)\n\n' % source_id)
        f.write(
            '- Источник: `%s`\n- Файлов: %s\n- Языки: %s\n- Есть тесты: %s\n'
            '- Помечено рисков: %d\n- Python AST: %s файлов\n\n'
            % (src, _summary_files(summary), langs, summary.get('has_tests'), len(risks), len(py_analysis))
        )
        if py_analysis:
            f.write('## Python semantic analysis (read-only AST)\n')
            for item in py_analysis[:50]:
                s = item.get('summary', {})
                f.write(
                    '- `%s`: syntax_ok=%s imports=%s classes=%s functions=%s risks=%s\n'
                    % (
                        item.get('path'),
                        item.get('syntax_ok'),
                        s.get('imports', 0),
                        s.get('classes', 0),
                        s.get('functions', 0),
                        s.get('risks', 0),
                    )
                )
            if len(py_analysis) > 50:
                f.write('- ... truncated in report, see inventory JSON producer for full data\n')
            f.write('\n')
        if risks:
            f.write('## Риск-файлы (только пометка, НЕ запуск)\n')
            for risk in risks[:50]:
                f.write('- %s\n' % _risk_label(risk))
            if len(risks) > 50:
                f.write('- ... truncated in report\n')
        f.write(
            '\nКод НЕ запускался (read-only). Следующее — обсуждение и решение по '
            '`docs/execute-sandbox-preflight.md`.\n'
        )
    return {'manifest': manifest, 'report': rep, 'files': _summary_files(summary), 'risks': len(risks)}


def list_sources():
    out = []
    if os.path.isdir(INBOX):
        for fn in sorted(os.listdir(INBOX)):
            if fn.endswith('.md') and fn != 'README.md':
                out.append(fn[:-3])
    return out


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    cmd = a[0]
    try:
        if cmd == 'list':
            for s in list_sources():
                print(s)
            return 0
        if cmd == 'intake' and len(a) > 1 and '--from' in a:
            frm = a[a.index('--from') + 1]
            note = a[a.index('--note') + 1] if '--note' in a else ''
            r = intake(a[1], frm, note=note)
            print('intake %s: файлов=%s рисков=%d -> %s ; %s' % (a[1], r['files'], r['risks'], r['manifest'], r['report']))
            return 0
    except Exception as exc:
        print('ОШИБКА: %s: %s' % (type(exc).__name__, exc))
        return 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
