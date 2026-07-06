#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# [FILE ID CARD]
# ID: tools.l2_inventory
# TYPE: active-script
# DOMAIN: core.indexing
# DEPTH_LEVEL: 1
# SUMMARY: Read-only L2-inventory сиблинг-источника → SQLite/FTS5 (пилот T-273, замкнутый контур).
# ==========================================
"""l2_inventory.py — read-only инвентаризация внешнего источника в SQLite/FTS5 (пилот T-273).

Первый живой L2-груз замкнутого контура. Строит быстрый индекс сиблинг-каталога
(источник — C:/Users/stefan/Documents/ai-colab-backup-2026-06-24, СТРОГО read-only)
без выхода за пределы --source. os.walk строго на чтение: метаданные каждого файла
(относительный путь, размер, mtime, расширение) + для текстовых расширений (.md/.txt/.py
и т.п.) индексируется содержимое с лимитом на файл; бинарные файлы — только метаданные.

Переиспользует канонические паттерны репозитория (рекомендация билдеру W3):
  - configure_output из _ioutil (единый UTF-8-вывод);
  - redaction.redact на любом тексте, идущем в БД/отчёт (маскирование секретов/путей);
  - confinement по паттерну file-inventory (T-059): candidate.relative_to(base), никакого
    execute/network, только чтение;
  - FTS5 с деградацией к LIKE по паттерну canon_index.py (T-141).

Writes ТОЛЬКО в tmp-work/t273/ (или иной явно указанный --db), НИКОГДА в источник.

CLI:
    python tools/l2_inventory.py build --source <dir> [--db <path>] [--max-text-bytes N] [--max-files N] [--json]
    python tools/l2_inventory.py query --db <path> "<fts>" [--limit N] [--json]
    python tools/l2_inventory.py stats --db <path> [--json]

Exit-коды (стабильные):
    0 — успех
    2 — ошибка использования (нет аргумента, пустой запрос, неизвестная команда)
    3 — источник/БД не найдены или путь вне разрешённого корня
"""
import os
import sys
import json
import sqlite3
import argparse
import stat
import datetime
from pathlib import Path

from _ioutil import configure_output
from _cli import help_guard

# drivers/ в sys.path — канонический redaction живёт там (как в text_extract.py).
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_DRIVERS = os.path.join(_ROOT, "drivers")
if _DRIVERS not in sys.path:
    sys.path.insert(0, _DRIVERS)
from redaction import redact  # канонический redaction (маскирование секретов/путей)

configure_output()

# БД по умолчанию — только в tmp-work/t273/ (жёсткое правило пилота).
DEFAULT_DB = os.path.join(_ROOT, "tmp-work", "t273", "l2_inventory.db")

# Лимит содержимого на текстовый файл: 200 КБ (рекомендация W3). Бинарные — только метаданные.
DEFAULT_MAX_TEXT_BYTES = 200 * 1024
# 0 означает без лимита; для реального W_run пилота передавайте явный --max-files.
DEFAULT_MAX_FILES = 0
DEFAULT_QUERY_LIMIT = 10

# Каталоги, которые не спускаем (шум/служебное) — паттерн file-inventory (T-059).
SKIP_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "venv", ".venv", "target", "build", "dist", "tmp-work",
}

# Текстовые расширения — для них индексируем содержимое (с лимитом). Прочее — только метаданные.
TEXT_EXTS = {
    ".md", ".markdown", ".txt", ".text", ".py", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".html", ".htm", ".css", ".js", ".ts", ".sql",
    ".csv", ".rst", ".sh", ".xml",
}


class PathAccessError(ValueError):
    """Путь вне разрешённого корня (confinement нарушен)."""
    pass


def _is_relative_to(path, base):
    """py3.8-совместимая проверка path.relative_to(base) без исключения наружу."""
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def resolve_source(source):
    """Разрешить --source в абсолютный существующий каталог (сам себе allowed-root).

    Источник — СИБЛИНГ репозитория (не внутри него), поэтому корнем confinement для
    os.walk служит сам разрешённый source: ни один candidate не должен выходить за
    его пределы (candidate.relative_to(base)). Никаких записей сюда — только чтение.
    """
    root = Path(source).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(str(root))
    if not root.is_dir():
        raise NotADirectoryError(str(root))
    return root


def resolve_db_path(db_path, source_root):
    """Разрешить путь БД и запретить запись внутрь read-only source."""
    db = Path(db_path).expanduser()
    if not db.is_absolute():
        db = Path.cwd() / db
    db = db.resolve()
    if _is_relative_to(db, source_root):
        raise PathAccessError("--db inside --source запрещён: %s" % redact(str(db)))
    return db


def _is_reparse_or_symlink(path):
    """Не читать symlink/reparse-point как часть confinement-пилота."""
    try:
        if path.is_symlink():
            return True
        attrs = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _read_text(path, max_bytes):
    """Прочитать текст файла с лимитом байт. Возвращает (text, truncated, had_error)."""
    try:
        with open(path, "rb") as f:
            raw = f.read(max_bytes + 1)
    except OSError:
        return "", False, True
    truncated = len(raw) > max_bytes
    if truncated:
        raw = raw[:max_bytes]
    return raw.decode("utf-8", errors="replace"), truncated, False

def _has_fts5(conn):
    """Есть ли FTS5 в этой сборке sqlite3 (проба). Паттерн canon_index.py."""
    try:
        conn.execute("CREATE VIRTUAL TABLE _fts5probe USING fts5(x)")
        conn.execute("DROP TABLE _fts5probe")
        return True
    except sqlite3.OperationalError:
        return False


def _meta_is_fts(conn):
    """Хранит ли текущая БД files-таблицу как FTS5 (по флагу в meta)."""
    row = conn.execute("SELECT sql FROM sqlite_master WHERE name='files'").fetchone()
    return bool(row) and "fts5" in (row[0] or "").lower()


def build(source, db_path=DEFAULT_DB, max_text_bytes=DEFAULT_MAX_TEXT_BYTES, max_files=DEFAULT_MAX_FILES):
    """Просканировать источник (read-only) и (пере)собрать SQLite/FTS5-индекс.

    Возвращает dict-отчёт: путь источника, БД, режим (fts5/like), счётчики, разбивку
    по расширениям, суммарный размер. БД создаётся только в целевом --db (по умолчанию
    tmp-work/t273/); каталог создаётся при отсутствии. В источник ничего не пишется.
    """
    root = resolve_source(source)
    db_abs = resolve_db_path(db_path, root)
    max_files = int(max_files or 0)
    max_text_bytes = int(max_text_bytes or DEFAULT_MAX_TEXT_BYTES)

    files = []            # строки для БД: (rel, ext, size, mtime, is_text, body)
    by_ext = {}
    total_size = 0
    total_files = 0
    text_indexed = 0
    limit_hit = False
    skipped_dirs = 0
    skipped_symlink_or_reparse = 0
    skipped_outside_root = 0
    read_errors = 0
    built_at = datetime.datetime.now().isoformat(timespec="seconds")

    for dirpath, dirnames, filenames in os.walk(root):
        if max_files and total_files >= max_files:
            limit_hit = True
            dirnames[:] = []
            break

        kept_dirs = []
        for d in sorted(dirnames):
            candidate_dir = Path(dirpath) / d
            if d in SKIP_DIRS:
                skipped_dirs += 1
                continue
            if _is_reparse_or_symlink(candidate_dir):
                skipped_symlink_or_reparse += 1
                continue
            kept_dirs.append(d)
        dirnames[:] = kept_dirs

        for filename in sorted(filenames):
            if max_files and total_files >= max_files:
                limit_hit = True
                break

            path = Path(dirpath) / filename
            if _is_reparse_or_symlink(path):
                skipped_symlink_or_reparse += 1
                continue
            try:
                resolved_path = path.resolve()
            except OSError:
                read_errors += 1
                continue
            # confinement: candidate обязан лежать внутри source (иначе пропускаем)
            if not _is_relative_to(resolved_path, root):
                skipped_outside_root += 1
                continue
            rel = path.relative_to(root).as_posix()
            try:
                st = path.stat(follow_symlinks=False)
            except OSError:
                read_errors += 1
                continue
            ext = path.suffix.lower() or "(none)"
            is_text = ext in TEXT_EXTS
            body = ""
            if is_text and st.st_size > 0:
                text, _trunc, had_error = _read_text(path, max_text_bytes)
                if had_error:
                    read_errors += 1
                # ЛЮБОЙ текст в БД проходит канонический redaction (секреты/пути)
                body = redact(text)
                if body:
                    text_indexed += 1
            mtime = datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
            files.append((rel, ext, st.st_size, mtime, 1 if is_text else 0, body))
            total_files += 1
            total_size += st.st_size
            by_ext[ext] = by_ext.get(ext, 0) + 1

    os.makedirs(str(db_abs.parent), exist_ok=True)
    conn = sqlite3.connect(str(db_abs))
    try:
        fts = _has_fts5(conn)
        conn.execute("DROP TABLE IF EXISTS files")
        conn.execute("DROP TABLE IF EXISTS meta")
        if fts:
            # rel/ext/size/mtime — неиндексируемые (UNINDEXED), body — полнотекстовое
            conn.execute(
                "CREATE VIRTUAL TABLE files USING fts5("
                "rel UNINDEXED, ext UNINDEXED, size UNINDEXED, mtime UNINDEXED, is_text UNINDEXED, body)"
            )
        else:
            conn.execute(
                "CREATE TABLE files(rel TEXT, ext TEXT, size INTEGER, mtime TEXT, is_text INTEGER, body TEXT)"
            )
        conn.executemany(
            "INSERT INTO files(rel, ext, size, mtime, is_text, body) VALUES(?,?,?,?,?,?)", files
        )
        # meta: параметры сборки — источник маскируем redact'ом (личный путь → $HOME)
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
        conn.executemany(
            "INSERT INTO meta(key, value) VALUES(?,?)",
            [
                ("source", redact(str(root))),
                ("built_at", built_at),
                ("engine", "fts5" if fts else "like"),
                ("max_text_bytes", str(max_text_bytes)),
                ("max_files", str(max_files)),
                ("limit_hit", "true" if limit_hit else "false"),
                ("truncated_by_max_files", "true" if limit_hit else "false"),
                ("skipped_dirs", str(skipped_dirs)),
                ("skipped_symlink_or_reparse", str(skipped_symlink_or_reparse)),
                ("skipped_outside_root", str(skipped_outside_root)),
                ("read_errors", str(read_errors)),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "source": redact(str(root)),
        "db": redact(str(db_abs)),
        "engine": "fts5" if fts else "like",
        "built_at": built_at,
        "max_text_bytes": max_text_bytes,
        "max_files": max_files,
        "limit_hit": limit_hit,
        "truncated_by_max_files": limit_hit,
        "total_files": total_files,
        "total_size_bytes": total_size,
        "text_indexed": text_indexed,
        "by_extension": dict(sorted(by_ext.items(), key=lambda kv: (-kv[1], kv[0]))),
        "skipped_dirs": skipped_dirs,
        "skipped_symlink_or_reparse": skipped_symlink_or_reparse,
        "skipped_outside_root": skipped_outside_root,
        "read_errors": read_errors,
    }

def _fts_query(q):
    """Собрать безопасный FTS5 MATCH-запрос: термины ≥2 симв. через OR (паттерн canon_index)."""
    import re
    terms = re.findall(r"[0-9A-Za-zА-Яа-яёЁ_]{2,}", q)
    return " OR ".join('"%s"' % t for t in terms) if terms else '""'


def query(db_path, q, limit=DEFAULT_QUERY_LIMIT):
    """FTS-поиск по индексу → [{rel, ext, size, mtime, snippet}]. None, если БД нет.

    При FTS5 — bm25-ранжирование + snippet(); при деградации — LIKE по body. Сниппет и
    путь-источник (rel) возвращаются в каждом попадании. Пустой запрос обрабатывает main().
    """
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    try:
        fts = _meta_is_fts(conn)
        if fts:
            rows = conn.execute(
                "SELECT rel, ext, size, mtime, snippet(files, 5, '[', ']', '…', 10) "
                "FROM files WHERE files MATCH ? ORDER BY bm25(files) LIMIT ?",
                (_fts_query(q), limit),
            ).fetchall()
        else:
            like = "%" + q.replace("%", "").replace("_", "") + "%"
            rows = conn.execute(
                "SELECT rel, ext, size, mtime, substr(body,1,120) "
                "FROM files WHERE body LIKE ? OR rel LIKE ? LIMIT ?",
                (like, like, limit),
            ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        conn.close()
    return [
        {
            "rel": r[0],
            "ext": r[1],
            "size": r[2],
            "mtime": r[3],
            "snippet": (r[4] or "").replace("\n", " ").strip(),
        }
        for r in rows
    ]


def _meta_int(meta, key):
    try:
        return int(meta.get(key, "0") or 0)
    except ValueError:
        return 0


def stats(db_path):
    """Сводка по индексу: кол-во файлов, суммарный размер, разбивка по расширениям.

    None, если БД нет. Разбивка отсортирована по убыванию количества, затем по имени.
    """
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    try:
        total_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        total_size = conn.execute("SELECT COALESCE(SUM(size),0) FROM files").fetchone()[0]
        text_indexed = conn.execute("SELECT COUNT(*) FROM files WHERE is_text=1 AND body<>''").fetchone()[0]
        ext_rows = conn.execute(
            "SELECT ext, COUNT(*) c FROM files GROUP BY ext ORDER BY c DESC, ext ASC"
        ).fetchall()
        meta = {}
        try:
            meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        except sqlite3.OperationalError:
            meta = {}
    finally:
        conn.close()
    limit_hit = meta.get("limit_hit", meta.get("truncated_by_max_files", "false")) == "true"
    return {
        "db": redact(str(Path(db_path).resolve())),
        "source": meta.get("source", ""),
        "engine": meta.get("engine", ""),
        "built_at": meta.get("built_at", ""),
        "max_text_bytes": _meta_int(meta, "max_text_bytes"),
        "max_files": _meta_int(meta, "max_files"),
        "limit_hit": limit_hit,
        "truncated_by_max_files": limit_hit,
        "total_files": total_files,
        "total_size_bytes": int(total_size),
        "text_indexed": text_indexed,
        "by_extension": {ext: c for ext, c in ext_rows},
        "skipped_dirs": _meta_int(meta, "skipped_dirs"),
        "skipped_symlink_or_reparse": _meta_int(meta, "skipped_symlink_or_reparse"),
        "skipped_outside_root": _meta_int(meta, "skipped_outside_root"),
        "read_errors": _meta_int(meta, "read_errors"),
    }

def _print_build(report):
    print("=== L2-INVENTORY BUILD ===")
    print("  источник:   %s" % report["source"])
    print("  БД:         %s (%s)" % (report["db"], report["engine"]))
    print("  файлов:     %d" % report["total_files"])
    print("  размер:     %d байт" % report["total_size_bytes"])
    print("  текст в ФТС: %d" % report["text_indexed"])
    print("  расширения (топ):")
    for ext, c in list(report["by_extension"].items())[:15]:
        print("    %-12s %d" % (ext, c))


def _print_stats(report):
    print("=== L2-INVENTORY STATS ===")
    print("  БД:       %s (%s)" % (report["db"], report["engine"] or "—"))
    if report["source"]:
        print("  источник: %s" % report["source"])
    if report["built_at"]:
        print("  собрано:  %s" % report["built_at"])
    print("  файлов:   %d" % report["total_files"])
    print("  размер:   %d байт" % report["total_size_bytes"])
    print("  текст в ФТС: %d" % report["text_indexed"])
    print("  расширения:")
    for ext, c in report["by_extension"].items():
        print("    %-12s %d" % (ext, c))


def _print_query(q, res):
    print("=== L2-INVENTORY QUERY «%s» — %d попаданий ===" % (q, len(res)))
    for r in res:
        print("  %-50s [%s] %d Б  %s" % (r["rel"][:50], r["ext"], r["size"], r["mtime"]))
        if r["snippet"]:
            print("       %s" % r["snippet"][:110])


def _build_parser():
    p = argparse.ArgumentParser(prog="l2_inventory.py", add_help=False)
    sub = p.add_subparsers(dest="cmd")

    b = sub.add_parser("build", add_help=False)
    b.add_argument("--source", required=True)
    b.add_argument("--db", default=DEFAULT_DB)
    b.add_argument("--max-text-bytes", type=int, default=DEFAULT_MAX_TEXT_BYTES)
    b.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    b.add_argument("--json", action="store_true")

    q = sub.add_parser("query", add_help=False)
    q.add_argument("--db", default=DEFAULT_DB)
    q.add_argument("terms", nargs="*")
    q.add_argument("--limit", type=int, default=DEFAULT_QUERY_LIMIT)
    q.add_argument("--json", action="store_true")

    s = sub.add_parser("stats", add_help=False)
    s.add_argument("--db", default=DEFAULT_DB)
    s.add_argument("--json", action="store_true")
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    help_guard(__doc__, argv)
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        # argparse отдаёт 2 при ошибке разбора — сохраняем стабильный usage-код
        return 2

    if not args.cmd:
        print(__doc__)
        return 2

    if args.cmd == "build":
        try:
            report = build(args.source, db_path=args.db, max_text_bytes=args.max_text_bytes, max_files=args.max_files)
        except (FileNotFoundError, NotADirectoryError, PathAccessError) as exc:
            _emit_error(exc, as_json="--json" in argv)
            return 3
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            _print_build(report)
        return 0

    if args.cmd == "query":
        q = " ".join(args.terms).strip()
        if not q:
            print("l2_inventory: query требует непустой запрос")
            return 2
        res = query(args.db, q, limit=args.limit)
        if res is None:
            print("l2_inventory: индекс не построен — сначала `build --source <dir> --db %s`" % args.db)
            return 3
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            _print_query(q, res)
        return 0

    if args.cmd == "stats":
        report = stats(args.db)
        if report is None:
            print("l2_inventory: индекс не построен — сначала `build --source <dir> --db %s`" % args.db)
            return 3
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            _print_stats(report)
        return 0

    print(__doc__)
    return 2


def _emit_error(exc, as_json=False):
    if as_json:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False))
    else:
        print("l2_inventory: %s: %s" % (type(exc).__name__, exc))


if __name__ == "__main__":
    sys.exit(main())
